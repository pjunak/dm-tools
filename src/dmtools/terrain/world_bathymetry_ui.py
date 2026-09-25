# pyright: reportUnknownMemberType=false
"""Ocean-floor scenarios over immutable geography; all edits require generation."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Literal, cast

import numpy as np
from PIL import ImageTk

from dmtools.terrain.adapters.world_bathymetry_inputs import (
    BATHYMETRY_EXTENSION,
    bathymetry_file_hash,
)
from dmtools.terrain.adapters.world_bathymetry_render import (
    BATHYMETRY_LAYERS,
    BathymetryLayer,
    render_bathymetry,
)
from dmtools.terrain.adapters.world_context_render import render_world_context
from dmtools.terrain.adapters.world_render import OCEAN
from dmtools.terrain.application.world_bathymetry import (
    BathymetryFile,
    BathymetryRun,
    export_bathymetry,
    generate_bathymetry,
    match_context,
    open_bathymetry,
    open_bathymetry_inputs,
    save_bathymetry_inputs,
)
from dmtools.terrain.application.world_context import WorldContextRun
from dmtools.terrain.domain.world_bathymetry import BathymetryInputs, BathymetrySettings
from dmtools.terrain.pipeline.control import CancellationToken, GenerationCancelled
from dmtools.terrain.viewport import MapViewport

type _Mode = Literal["generate", "open-result", "open-input", "save-input", "export"]
type _Event = BathymetryRun | BathymetryFile | Path | str | Exception


class BathymetryEditor(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        context: WorldContextRun,
        *,
        on_close: Callable[[BathymetryFile | None], None] | None = None,
        saved: BathymetryFile | None = None,
    ) -> None:
        super().__init__(parent)
        self.context = context
        self.run: BathymetryRun | None = None
        self.file: BathymetryFile | None = None
        self.on_close = on_close
        self.busy = False
        self._closed = False
        self._loading = True
        self._controls: list[tuple[ttk.Widget, str]] = []
        self._events: queue.Queue[_Event] = queue.Queue()
        self._mode: _Mode = "generate"
        self._after_job: Callable[[], None] | None = None
        self._cancellation: CancellationToken | None = None
        self._draw_id: str | None = None
        self._poll_id: str | None = None
        self._photo: ImageTk.PhotoImage | None = None
        self._built_signature: object = None
        self._saved_signature: object = None
        self._frozen_selection: tuple[str, ...] = ()
        self.viewport = MapViewport()
        self._pan: tuple[int, int] | None = None
        settings = BathymetrySettings(latitude_cells=context.context.grid.shape[0])
        self.values = {
            key: tk.StringVar(self, value=str(getattr(settings, key)))
            for key in (
                "latitude_cells",
                "shelf_width_km",
                "shelf_depth_m",
                "slope_width_km",
                "basin_depth_m",
            )
        }
        self.layer = tk.StringVar(self, value="Connected water")
        self.status = tk.StringVar(
            self,
            value="Largest water region is suggested. "
            "Review ocean membership and the illustrative parameters before generating.",
        )
        self.summary = tk.StringVar(
            self, value="No bathymetry generated. Unselected water has no depth."
        )
        self.inspection = tk.StringVar(self, value="Wheel: zoom · Middle/right drag: pan · F: fit")
        self.legend = tk.StringVar(self)
        self.title("Bathymetry inputs — " + context.context.world.project.name)
        self.geometry("1320x850")
        self.minsize(1050, 760)
        self.transient(parent.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", lambda: self.guard(self.close))
        self._build()
        for body in context.context.water_bodies:
            self.tree.insert(
                "",
                "end",
                iid=str(body.id),
                text=f"Water {body.id}",
                values=(f"{body.area_km2:,.0f}" if body.area_km2 >= 1 else "<1",),
            )
        if context.context.water_bodies:
            self.tree.selection_set(str(context.context.water_bodies[0].id))
        for value in self.values.values():
            value.trace_add("write", self._changed)
        self._saved_signature = self._signature()
        self._loading = False
        self.bind("<Control-s>", lambda _e: self._key(self.save))
        self.bind("<Control-Shift-S>", lambda _e: self._key(lambda: self.save(save_as=True)))
        self.canvas.bind("f", lambda _e: self._key(self.fit))
        self._poll_id = self.after(80, self._poll)
        self.grab_set()
        if saved is not None:
            self.load_inputs(saved.path)
        self._schedule_draw()

    @staticmethod
    def _key(action: Callable[[], None]) -> str:
        action()
        return "break"

    @property
    def dirty(self) -> bool:
        return self._signature() != self._saved_signature

    @property
    def current(self) -> bool:
        return self.run is not None and self._signature() == self._built_signature

    def _signature(self) -> object:
        return tuple(v.get() for v in self.values.values()), tuple(sorted(self.tree.selection()))

    def _button(self, parent: tk.Misc, text: str, action: Callable[[], None]) -> ttk.Button:
        button = ttk.Button(parent, text=text, command=action)
        self._controls.append((button, "normal"))
        return button

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        head = ttk.Frame(self, padding=(14, 10))
        head.grid(row=0, column=0, sticky="ew")
        ttk.Label(head, text="Ocean-floor hypotheses", style="Header.TLabel").pack(side="left")
        for text, action in (
            ("Open inputs…", self.choose_inputs),
            ("Save inputs", self.save),
            ("Save As…", lambda: self.save(save_as=True)),
            ("Open result…", self.choose_result),
        ):
            self._button(head, text, action).pack(side="left", padx=6)
        main = ttk.Frame(self, padding=(14, 0))
        main.grid(row=1, column=0, sticky="nsew")
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)
        side = ttk.Frame(main, padding=(0, 0, 12, 0))
        side.grid(row=0, column=0, sticky="nsew")
        side.columnconfigure(0, weight=1)
        side.rowconfigure(1, weight=1)
        ttk.Label(
            side, text="SELECT OCEANS · CTRL/SHIFT FOR MULTIPLE", style="Eyebrow.TLabel"
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))
        tree_frame = ttk.Frame(side)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(tree_frame, columns=("area",), selectmode="extended", height=8)
        self.tree.heading("#0", text="Connected water")
        self.tree.heading("area", text="Area (km²)")
        self.tree.column("#0", width=135)
        self.tree.column("area", width=160, anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew")

        def scroll_tree(*args: str) -> None:
            self.tree.yview(*args)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=scroll_tree)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self._selected)
        form = ttk.Frame(side)
        form.grid(row=2, column=0, sticky="ew", pady=10)
        form.columnconfigure(1, weight=1)
        for row, (key, label) in enumerate(
            (
                ("latitude_cells", "Latitude rows (4-360)"),
                ("shelf_width_km", "Shelf width (km)"),
                ("shelf_depth_m", "Shelf-break depth (m)"),
                ("slope_width_km", "Slope width (km)"),
                ("basin_depth_m", "Basin depth (m)"),
            )
        ):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
            entry = ttk.Entry(form, textvariable=self.values[key], width=15)
            entry.grid(row=row, column=1, sticky="ew", pady=3)
            self._controls.append((entry, "normal"))
        self._button(side, "Generate ocean floor", self.generate).grid(row=3, column=0, sticky="ew")
        self._button(side, "Export result…", self.export).grid(row=4, column=0, sticky="ew", pady=6)
        ttk.Label(
            side,
            text="One editable margin profile for the selected waters. "
            "These values are hypotheses, not inferred age or measured depth. "
            "Mixed-layer depth and water transport are separate future models.",
            wraplength=330,
        ).grid(row=5, column=0, sticky="ew", pady=8)
        ttk.Label(side, textvariable=self.summary, wraplength=330).grid(
            row=6, column=0, sticky="ew", pady=8
        )
        ttk.Label(side, textvariable=self.legend, wraplength=330).grid(row=7, column=0, sticky="ew")
        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        toolbar = ttk.Frame(right)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._button(toolbar, "Fit world", self.fit).pack(side="left")
        choice = ttk.Combobox(
            toolbar,
            textvariable=self.layer,
            values=("Connected water", *BATHYMETRY_LAYERS),
            state="readonly",
            width=23,
        )
        choice.pack(side="left", padx=8)
        choice.bind("<<ComboboxSelected>>", lambda _e: self._schedule_draw())
        self.canvas = tk.Canvas(right, background=OCEAN, highlightthickness=0, takefocus=True)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda _e: self._schedule_draw())
        self.canvas.bind("<Motion>", self._motion)
        self.canvas.bind("<MouseWheel>", self._wheel)
        for button in (2, 3):
            self.canvas.bind(f"<ButtonPress-{button}>", self._pan_start)
            self.canvas.bind(f"<B{button}-Motion>", self._pan_move)
        self.canvas.bind("<Button-1>", lambda _e: self.canvas.focus_set())
        ttk.Label(right, textvariable=self.inspection, wraplength=680).grid(
            row=2, column=0, sticky="ew", pady=6
        )
        footer = ttk.Frame(self, padding=(14, 8))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        self.status_label = ttk.Label(footer, textvariable=self.status, wraplength=1000)
        self.status_label.grid(row=0, column=0, sticky="ew")
        footer.bind(
            "<Configure>", lambda e: self.status_label.configure(wraplength=max(300, e.width - 120))
        )
        self.cancel_button = ttk.Button(
            footer, text="Cancel job", command=self.cancel, state="disabled"
        )
        self.cancel_button.grid(row=0, column=1, padx=8)

    def _selected(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        if self.busy:
            if self.tree.selection() != self._frozen_selection:
                self.tree.selection_set(self._frozen_selection)
            return
        self._changed()

    def _changed(self, *_args: str) -> None:
        if self._loading:
            return
        self.title(
            ("* " if self.dirty else "")
            + "Bathymetry inputs — "
            + self.context.context.world.project.name
        )
        if self.run and not self.current:
            self.status.set(
                "Inputs changed. The previous result is stale; generate to apply changes."
            )
        self._schedule_draw()

    def inputs(self) -> BathymetryInputs:
        return BathymetryInputs(
            self.context.context.world.project,
            tuple(sorted(int(i) for i in self.tree.selection())),
            BathymetrySettings(
                int(self.values["latitude_cells"].get()),
                *(
                    float(self.values[key].get())
                    for key in (
                        "shelf_width_km",
                        "shelf_depth_m",
                        "slope_width_km",
                        "basin_depth_m",
                    )
                ),
            ),
        )

    def _apply_inputs(self, inputs: BathymetryInputs) -> None:
        inputs = match_context(inputs, self.context)
        self._loading = True
        for key, value in self.values.items():
            value.set(str(getattr(inputs.settings, key)))
        self.tree.selection_set(tuple(map(str, inputs.ocean_ids)))
        self._loading = False
        self._changed()

    def _work(
        self,
        mode: _Mode,
        label: str,
        action: Callable[[], _Event],
        after: Callable[[], None] | None = None,
    ) -> None:
        if self.busy:
            return
        self._mode, self._after_job = mode, after
        self._cancellation = None if mode == "save-input" else CancellationToken()
        self.busy = True
        self._frozen_selection = self.tree.selection()
        for control, _ in self._controls:
            control["state"] = "disabled"
        self.cancel_button.configure(state="normal" if self._cancellation else "disabled")
        self.status.set(label)

        def worker() -> None:
            try:
                self._events.put(action())
            except Exception as error:
                self._events.put(error)

        threading.Thread(target=worker, name="world-bathymetry-worker", daemon=True).start()

    def _progress(self, fraction: float, label: str) -> None:
        self._events.put(f"{fraction:.0%} · {label}")

    def _poll(self) -> None:
        self._poll_id = None
        if self._closed:
            return
        while not self._events.empty():
            event = self._events.get_nowait()
            if isinstance(event, str):
                self.status.set(event)
                continue
            self.busy = False
            self._cancellation = None
            for control, state in self._controls:
                control["state"] = state
            self.cancel_button.configure(state="disabled")
            after, self._after_job = self._after_job, None
            if isinstance(event, Exception):
                self.status.set(
                    "Cancelled; previous result and inputs retained."
                    if isinstance(event, GenerationCancelled)
                    else str(event)
                )
                continue
            if isinstance(event, BathymetryFile):
                if self._mode == "open-input":
                    self._apply_inputs(event.inputs)
                self.file = event
                self._saved_signature = self._signature()
                self.status.set(
                    f"Inputs {'opened' if self._mode == 'open-input' else 'saved'}: "
                    f"{event.path.name}. Generate to apply them."
                )
            elif isinstance(event, BathymetryRun):
                self.context = WorldContextRun(event.result.context, event.runtime)
                if self._mode == "open-result":
                    self._apply_inputs(event.result.inputs)
                    self.file = None
                    self._saved_signature = self._signature()
                self.run = event
                self._built_signature = self._signature()
                self.layer.set("Ocean floor")
                missing = event.result.unsampled_ocean_ids
                self.summary.set(
                    f"{event.result.sampled_cells:,} ocean samples · "
                    f"{event.result.context.grid.shape[1]} x "
                    f"{event.result.context.grid.shape[0]} cells. "
                    f"{event.result.context.mixed_cells:,} mixed coast cells remain approximate. "
                    + (
                        "No centre samples in selected waters: "
                        + ", ".join(map(str, missing))
                        + ". "
                        if missing
                        else ""
                    )
                    + "Cell-centre elevations are not cell-average depth or transport capacity."
                )
                self.status.set(
                    "Ocean-floor hypothesis ready. Coastline unchanged; "
                    "numerical error does not measure geological uncertainty."
                )
            else:
                self.status.set(f"Exported completed bathymetry: {event}")
            self._changed()
            self._schedule_draw()
            if after:
                after()
                if self._closed:
                    return
        self._poll_id = self.after(80, self._poll)

    def generate(self) -> None:
        if self.busy:
            return
        try:
            inputs = self.inputs()
        except ValueError as error:
            self.status.set(str(error))
            return
        context = self.context
        self._work(
            "generate",
            "Preparing the ocean-depth scenario…",
            lambda: generate_bathymetry(
                inputs, context, self._progress, cancellation=self._cancellation
            ),
        )

    def save(self, *, save_as: bool = False, after: Callable[[], None] | None = None) -> None:
        if self.busy:
            return
        try:
            inputs = self.inputs()
            path, digest = (self.file.path, self.file.sha256) if self.file else (None, None)
            if path is None or save_as:
                selected = filedialog.asksaveasfilename(
                    parent=self,
                    title="Save bathymetry inputs",
                    defaultextension=BATHYMETRY_EXTENSION,
                    initialfile=path.name if path else "world.dmbathy.json",
                    filetypes=[("Bathymetry inputs", "*.dmbathy.json")],
                )
                if not selected:
                    return
                path = Path(selected)
                if self.file is None or path.resolve() != self.file.path.resolve():
                    digest = bathymetry_file_hash(path)
        except (ValueError, OSError) as error:
            self.status.set(str(error))
            return
        target = path
        self._work(
            "save-input",
            "Saving portable inputs…",
            lambda: save_bathymetry_inputs(inputs, self.context, target, digest),
            after,
        )

    def load_inputs(self, path: Path) -> None:
        self._work(
            "open-input",
            "Opening bathymetry inputs…",
            lambda: open_bathymetry_inputs(path, self.context, cancellation=self._cancellation),
        )

    def choose_inputs(self) -> None:
        def choose() -> None:
            selected = filedialog.askopenfilename(
                parent=self,
                title="Open bathymetry inputs",
                filetypes=[("Bathymetry inputs", "*.dmbathy.json")],
            )
            if selected:
                self.load_inputs(Path(selected))

        self.guard(choose)

    def load_result(self, path: Path) -> None:
        context = self.context

        def operation() -> BathymetryRun:
            result = open_bathymetry(path, cancellation=self._cancellation)
            match_context(result.result.inputs, context)
            return result

        self._work("open-result", "Verifying bathymetry and its geographic dependency…", operation)

    def choose_result(self) -> None:
        def choose() -> None:
            selected = filedialog.askopenfilename(
                parent=self,
                title="Open completed bathymetry",
                filetypes=[("Bathymetry result", "bathymetry.json")],
            )
            if selected:
                self.load_result(Path(selected))

        self.guard(choose)

    def export(self) -> None:
        if self.busy:
            return
        if self.run is None or not self.current:
            self.status.set("Generate from the current inputs before exporting.")
            return
        selected = filedialog.asksaveasfilename(
            parent=self,
            title="New bathymetry output folder",
            initialfile="world-bathymetry",
            confirmoverwrite=False,
        )
        if not selected:
            return
        run, target = self.run, Path(selected)
        self._work(
            "export",
            "Exporting a new result with its geographic source…",
            lambda: export_bathymetry(run, target, cancellation=self._cancellation),
        )

    def cancel(self) -> None:
        if self._cancellation:
            self._cancellation.cancel()

    def guard(self, action: Callable[[], None]) -> None:
        if self.busy:
            self.status.set("Finish or cancel the current job before continuing.")
            self.lift()
            return
        if not self.dirty:
            action()
            return
        answer = messagebox.askyesnocancel(
            "Save bathymetry inputs?", "Save these inputs before continuing?", parent=self
        )
        if answer is True:
            self.save(after=action)
        elif answer is False:
            action()

    def _size(self) -> tuple[int, int]:
        return max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())

    def fit(self) -> None:
        self.viewport.fit()
        self._schedule_draw()

    def _schedule_draw(self) -> None:
        if not self._closed and self._draw_id is None:
            self._draw_id = self.after(30, self._draw)

    def _draw(self) -> None:
        self._draw_id = None
        self.canvas.delete("all")
        if self.run is not None and self.layer.get() in BATHYMETRY_LAYERS:
            preview = render_bathymetry(
                self.run.result,
                self.viewport,
                self._size(),
                cast(BathymetryLayer, self.layer.get()),
            )
            depth = self.run.result.inputs.settings.basin_depth_m
            if self.layer.get() == "Ocean floor":
                legend = f"Light: 0 m · dark blue: -{depth:g} m. Green: land. "
            elif self.layer.get() == "Distance error":
                legend = f"Dark: 0 m · orange: {depth:g} m numerical bound. "
            else:
                legend = "Orange: mixed/split or subcell geography. "
            self.legend.set(legend + "Grey: unselected water. Zoom does not add samples.")
        else:
            preview = render_world_context(
                self.context.context, self.viewport, self._size(), "Connected water"
            )
            self.legend.set(
                "Colours distinguish connected water regions. Hover shows the "
                "dominant cell ID; mixed cells may contain other waters."
            )
        with preview:
            self._photo = ImageTk.PhotoImage(preview, master=self)
        self.canvas.create_image(0, 0, image=self._photo, anchor="nw")
        if self.run is not None and not self.current:
            self.canvas.create_rectangle(10, 10, 440, 39, fill="#684629", outline="")
            self.canvas.create_text(
                20,
                24,
                text="PREVIOUS RESULT · Generate to apply the edited inputs",
                fill="#fff2cb",
                anchor="w",
            )

    def _motion(self, event: tk.Event[tk.Misc]) -> None:
        grid = self.context.context.grid
        left, top, right, bottom = self.viewport.rect(
            self._size(), (grid.frame.width, grid.frame.height)
        )
        if not left <= event.x <= right or not top <= event.y <= bottom:
            return
        rows, columns = grid.shape
        row = min(rows - 1, int((event.y - top) / (bottom - top) * rows))
        column = min(columns - 1, int((event.x - left) / (right - left) * columns))
        if self.run and self.layer.get() != "Connected water":
            result = self.run.result
            body = int(result.centre_water_body[row, column])
            bed = float(result.bed_elevation_m[row, column])
            text = (
                f"Water {body} · bed {bed:,.2f} m · numerical bound "
                f"{result.distance_depth_error_m[row, column]:.2f} m"
                if np.isfinite(bed)
                else f"{'Land' if body == 0 else f'Water {body}'} · no depth"
            )
        else:
            text = f"Dominant water ID: {self.context.context.water_body[row, column]}"
        flags = int(self.context.context.support_flags[row, column])
        self.inspection.set(
            f"{grid.latitude_deg(row):.2f}°, {grid.longitude_deg(column):.2f}° · "
            f"{text} · geographic support flags {flags}"
        )

    def _wheel(self, event: tk.Event[tk.Misc]) -> None:
        frame = self.context.context.grid.frame
        self.viewport.zoom_at(
            1.2 if event.delta > 0 else 1 / 1.2,
            (event.x, event.y),
            self._size(),
            (frame.width, frame.height),
        )
        self._schedule_draw()

    def _pan_start(self, event: tk.Event[tk.Misc]) -> None:
        self._pan = (event.x, event.y)

    def _pan_move(self, event: tk.Event[tk.Misc]) -> None:
        if self._pan:
            frame = self.context.context.grid.frame
            self.viewport.pan(
                (event.x - self._pan[0], event.y - self._pan[1]),
                self._size(),
                (frame.width, frame.height),
            )
            self._pan = (event.x, event.y)
            self._schedule_draw()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.cancel()
        for identifier in (self._poll_id, self._draw_id):
            if identifier:
                self.after_cancel(identifier)
        self._photo = None
        self.grab_release()
        if self.on_close:
            self.on_close(self.file)
        self.destroy()
