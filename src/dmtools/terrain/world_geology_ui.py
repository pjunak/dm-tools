# pyright: reportUnknownMemberType=false
"""Pre-generation geology authoring over a retained world and read-only context."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Literal, cast
from uuid import uuid4

from PIL import ImageTk

from dmtools.terrain.adapters.world_context_render import (
    CONTEXT_LAYERS,
    ContextLayer,
    render_world_context,
)
from dmtools.terrain.adapters.world_geology import GEOLOGY_EXTENSION, geology_file_hash
from dmtools.terrain.adapters.world_geology_render import SETTING_COLOURS, render_geology
from dmtools.terrain.adapters.world_render import OCEAN, render_world_source
from dmtools.terrain.application.world_context import WorldContextRun
from dmtools.terrain.application.world_geology import GeologyFile, open_geology, save_geology
from dmtools.terrain.domain.models import Point2D
from dmtools.terrain.domain.world_context import EXPOSURE_BEARINGS
from dmtools.terrain.domain.world_geology import (
    GEOLOGICAL_SETTINGS,
    MAX_PROVINCE_VERTICES,
    ContinentGeology,
    GeologicalSetting,
    GeologyProfile,
    GeologyProvince,
    WorldGeologyRecipe,
    blank_geology,
)
from dmtools.terrain.pipeline.control import CancellationToken, GenerationCancelled
from dmtools.terrain.pipeline.world import WorldMap
from dmtools.terrain.pipeline.world_geology import GeologyCoverage, resolve_geology
from dmtools.terrain.viewport import MapViewport
from dmtools.terrain.world_landform_ui import WorldLandformForm


@dataclass(frozen=True)
class _Result:
    coverage: GeologyCoverage
    mode: Literal["initial", "edit", "open", "save"]
    file: GeologyFile | None = None


class GeologyEditor(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        world: WorldMap,
        context: WorldContextRun | None = None,
        *,
        on_close: Callable[[GeologyFile | None], None] | None = None,
        saved: GeologyFile | None = None,
    ) -> None:
        super().__init__(parent)
        self.world = world
        self.context = context
        self.on_close = on_close
        self.file = saved
        self.recipe = saved.coverage.recipe if saved else blank_geology(world.project)
        self.coverage: GeologyCoverage | None = saved.coverage if saved else None
        self._saved_recipe = self.recipe
        self._undo: list[GeologyCoverage] = []
        self._redo: list[GeologyCoverage] = []
        self._events: queue.Queue[_Result | Exception] = queue.Queue()
        self._controls: list[tuple[ttk.Widget, str]] = []
        self._field_widgets: dict[str, ttk.Widget] = {}
        self._callback: Callable[[], None] | None = None
        self._cancellation: CancellationToken | None = None
        self._selected = "continent:" + world.continents[0].id
        self._next_selected = self._selected
        self._draft: list[Point2D] | None = None
        self._draft_id: str | None = None
        self._loaded_form: tuple[str, ...] = ()
        self._closed = False
        self.busy = False
        self._poll_id: str | None = None
        self._draw_id: str | None = None
        self._photo: ImageTk.PhotoImage | None = None
        self._pan: Point2D | None = None
        self.viewport = MapViewport()
        self.values = {
            key: tk.StringVar(self)
            for key in ("name", "priority", "setting", "crust", "rejuvenation", "duration")
        }
        self.layer = tk.StringVar(self, value="Geology coverage")
        self.bearing = tk.StringVar(self, value="N")
        self.status = tk.StringVar(self, value="Select a continent default or draw a province.")
        self.detail = tk.StringVar(self)
        self.inspection = tk.StringVar(self, value="Wheel: zoom · Middle/right drag: pan · F: fit")
        self.title("Geology inputs — " + world.project.name)
        self.geometry("1320x850")
        self.minsize(1050, 740)
        self.transient(parent.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", lambda: self.guard(self.close))
        self._build()
        self._populate()
        self._load_form()
        self.bind("<Control-s>", lambda _e: self._key(self.save))
        self.bind("<Control-Shift-S>", lambda _e: self._key(lambda: self.save(save_as=True)))
        self.bind("<Control-o>", lambda _e: self._key(self.choose_open))
        self.canvas.bind("<Return>", lambda _e: self._key(self.apply))
        self.canvas.bind("<Escape>", lambda _e: self._key(self.revert))
        self.canvas.bind("<BackSpace>", lambda _e: self._key(self.remove_vertex))
        self.canvas.bind("f", lambda _e: self._key(self.fit))
        self._poll_id = self.after(60, self._poll)
        self.grab_set()
        if saved is not None:
            self.load(saved.path)
        else:
            self._work(
                "Resolving continent defaults…",
                lambda: _Result(resolve_geology(world, self.recipe, self._cancellation), "initial"),
            )
        self._schedule_draw()

    @staticmethod
    def _key(action: Callable[[], None]) -> str:
        action()
        return "break"

    @property
    def form_dirty(self) -> bool:
        return self._form() != self._loaded_form

    @property
    def dirty(self) -> bool:
        return self.recipe != self._saved_recipe or self.form_dirty or self._draft is not None

    def _button(self, parent: tk.Misc, text: str, command: Callable[[], None]) -> ttk.Button:
        button = ttk.Button(parent, text=text, command=command)
        self._controls.append((button, "normal"))
        return button

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        head = ttk.Frame(self, padding=(14, 10))
        head.grid(row=0, column=0, sticky="ew")
        ttk.Label(head, text="Geology inputs", style="Header.TLabel").pack(side="left")
        for text, command in (
            ("Open recipe…", self.choose_open),
            ("Save", self.save),
            ("Save As…", lambda: self.save(save_as=True)),
            ("Undo", self.undo),
            ("Redo", self.redo),
        ):
            self._button(head, text, command).pack(side="left", padx=(8, 0))
        main = ttk.Frame(self, padding=(14, 0))
        main.grid(row=1, column=0, sticky="nsew")
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)
        side = ttk.Frame(main, padding=(0, 0, 12, 0), width=340)
        side.grid(row=0, column=0, sticky="nsew")
        side.columnconfigure(0, weight=1)
        side.rowconfigure(1, weight=1)
        ttk.Label(side, text="CONTINENT DEFAULTS & PROVINCES", style="Eyebrow.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        tree_frame = ttk.Frame(side)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse", height=7)
        self.tree.column("#0", width=310)
        self.tree.grid(row=0, column=0, sticky="nsew")

        def scroll_tree(*args: str) -> None:
            self.tree.yview(*args)

        bar = ttk.Scrollbar(tree_frame, orient="vertical", command=scroll_tree)
        bar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=bar.set)
        self.tree.bind("<<TreeviewSelect>>", self._selection)
        tools = ttk.Frame(side)
        tools.grid(row=2, column=0, sticky="ew", pady=8)
        for text, action in (
            ("Draw province", self.start_drawing),
            ("Redraw", lambda: self.start_drawing(redraw=True)),
            ("Delete", self.delete),
        ):
            self._button(tools, text, action).pack(side="left", padx=(0, 4))
        self.form_tabs = ttk.Notebook(side)
        self.form_tabs.grid(row=3, column=0, sticky="ew")
        form = ttk.Frame(self.form_tabs, padding=6)
        self.form_tabs.add(form, text="Geological history")
        self.landform_form = WorldLandformForm(self.form_tabs)
        self.form_tabs.add(self.landform_form, text="Landform guidance")
        form.columnconfigure(1, weight=1)
        for row, (key, label) in enumerate(
            (
                ("name", "Name"),
                ("priority", "Priority (0-100)"),
                ("setting", "Setting"),
                ("crust", "Crust age (Ma)"),
                ("rejuvenation", "Rejuvenation (Ma)"),
                ("duration", "Simulation span (Ma)"),
            )
        ):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
            widget = (
                ttk.Combobox(
                    form,
                    textvariable=self.values[key],
                    values=GEOLOGICAL_SETTINGS,
                    width=19,
                    state="readonly",
                )
                if key == "setting"
                else ttk.Entry(form, textvariable=self.values[key], width=21)
            )
            widget.grid(row=row, column=1, sticky="ew", pady=3)
            self._field_widgets[key] = widget
            self._controls.append((widget, "readonly" if key == "setting" else "normal"))
        actions = ttk.Frame(side)
        actions.grid(row=4, column=0, sticky="ew", pady=8)
        self._button(actions, "Apply / finish polygon", self.apply).pack(side="left")
        self._button(actions, "Revert / cancel", self.revert).pack(side="left", padx=4)
        ttk.Label(
            side,
            text="Ma = million years. Ages are before one common present. "
            "Simulation span is a duration. Blank = unknown.\n"
            "A province replaces the entire default, including blanks.",
            wraplength=330,
        ).grid(row=5, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(side, textvariable=self.detail, wraplength=330).grid(
            row=6, column=0, sticky="ew", pady=(0, 8)
        )
        legend = ttk.Frame(side)
        legend.grid(row=7, column=0, sticky="ew")
        for row, (setting, colour) in enumerate(SETTING_COLOURS.items()):
            tk.Label(legend, background=colour, width=2).grid(
                row=row // 2, column=row % 2 * 2, padx=(0, 5), pady=1
            )
            ttk.Label(legend, text=setting).grid(
                row=row // 2, column=row % 2 * 2 + 1, sticky="w", padx=(0, 7)
            )
        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        view_tools = ttk.Frame(right)
        view_tools.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._button(view_tools, "Fit world", self.fit).pack(side="left")
        layers = ("Geology coverage", "Source", *(CONTEXT_LAYERS if self.context else ()))
        selector = ttk.Combobox(
            view_tools, textvariable=self.layer, values=layers, state="readonly", width=24
        )
        selector.pack(side="left", padx=8)
        selector.bind("<<ComboboxSelected>>", lambda _e: self._schedule_draw())
        if self.context:
            ttk.Label(view_tools, text="Look").pack(side="left")
            bearing = ttk.Combobox(
                view_tools,
                textvariable=self.bearing,
                values=EXPOSURE_BEARINGS,
                state="readonly",
                width=4,
            )
            bearing.pack(side="left", padx=4)
            bearing.bind("<<ComboboxSelected>>", lambda _e: self._schedule_draw())
        self.canvas = tk.Canvas(right, background=OCEAN, highlightthickness=0, takefocus=True)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda _e: self._schedule_draw())
        self.canvas.bind("<Button-1>", self._pick)
        self.canvas.bind("<Motion>", self._motion)
        self.canvas.bind("<MouseWheel>", self._wheel)
        for button in (2, 3):
            self.canvas.bind(f"<ButtonPress-{button}>", self._pan_start)
            self.canvas.bind(f"<B{button}-Motion>", self._pan_move)
        ttk.Label(right, textvariable=self.inspection, wraplength=720).grid(
            row=2, column=0, sticky="ew", pady=6
        )
        foot = ttk.Frame(self, padding=(14, 8))
        foot.grid(row=2, column=0, sticky="ew")
        foot.columnconfigure(0, weight=1)
        ttk.Label(
            foot,
            text="Save this recipe, then choose it in World → Terrain to apply landform guidance. "
            "Geological ages remain hypotheses; climate and aging are not applied.",
            wraplength=930,
        ).grid(row=0, column=0, sticky="w")
        self.status_label = ttk.Label(foot, textvariable=self.status, wraplength=1080)
        self.status_label.grid(row=1, column=0, sticky="ew", pady=4)
        foot.bind(
            "<Configure>", lambda e: self.status_label.configure(wraplength=max(300, e.width - 120))
        )
        self.cancel_button = ttk.Button(
            foot, text="Cancel job", command=self.cancel, state="disabled"
        )
        self.cancel_button.grid(row=1, column=1, padx=6)

    def _form(self) -> tuple[str, ...]:
        return (*tuple(v.get() for v in self.values.values()), *self.landform_form.snapshot())

    def _populate(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.tree.insert("", "end", iid="defaults", text="Continent defaults", open=True)
        self.tree.insert(
            "", "end", iid="provinces", text="Provinces · higher priority wins", open=True
        )
        for c in self.world.continents:
            self.tree.insert("defaults", "end", iid="continent:" + c.id, text=c.name)
        for p in sorted(self.recipe.provinces, key=lambda p: (-p.priority, p.name)):
            self.tree.insert("provinces", "end", iid=p.id, text=f"{p.name} · priority {p.priority}")
        if self.tree.exists(self._selected):
            self.tree.selection_set(self._selected)
            self.tree.see(self._selected)

    def _load_form(self) -> None:
        province = next((p for p in self.recipe.provinces if p.id == self._selected), None)
        if province:
            name, priority, profile = province.name, str(province.priority), province.profile
        else:
            owner = self._selected.removeprefix("continent:")
            default = next((d for d in self.recipe.defaults if d.continent_id == owner), None)
            name = next((c.name for c in self.world.continents if c.id == owner), "New province")
            priority, profile = "0", default.profile if default else GeologyProfile()
        for key, value in zip(
            self.values,
            (
                name,
                priority,
                profile.setting,
                "" if profile.crust_age_ma is None else str(profile.crust_age_ma),
                "" if profile.rejuvenation_age_ma is None else str(profile.rejuvenation_age_ma),
                "" if profile.evolution_duration_ma is None else str(profile.evolution_duration_ma),
            ),
            strict=True,
        ):
            self.values[key].set(value)
        self.landform_form.load(profile.landform)
        self._loaded_form = self._form()
        self._lock_identity_fields()
        region = (
            next((r for r in self.coverage.regions if r.id == self._selected), None)
            if self.coverage
            else None
        )
        self.detail.set(
            f"Effective land: {region.area_km2:,.0f} km². "
            + ("Province override." if region.province else "Remaining default coverage.")
            if region
            else "Draw a polygon with at least three vertices."
        )

    def _lock_identity_fields(self) -> None:
        state = (
            "disabled"
            if self.busy
            else ("readonly" if self._selected.startswith("continent:") else "normal")
        )
        for key in ("name", "priority"):
            self._field_widgets[key]["state"] = state

    def _selection(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        selection = self.tree.selection()
        if not selection or selection[0] == self._selected:
            return
        if self.busy or self.form_dirty or self._draft is not None:
            self.status.set("Apply or revert the current edit before selecting another region.")
            if self.tree.exists(self._selected):
                self.tree.selection_set(self._selected)
            return
        if selection[0] in ("defaults", "provinces"):
            return
        self._selected = selection[0]
        self._load_form()
        self._schedule_draw()

    def _profile(self) -> GeologyProfile:
        values = [self.values[key].get().strip() for key in ("crust", "rejuvenation", "duration")]
        return GeologyProfile(
            cast(GeologicalSetting, self.values["setting"].get()),
            *(float(value) if value else None for value in values),
            landform=self.landform_form.read(),
        )

    def _candidate(self) -> WorldGeologyRecipe:
        profile = self._profile()
        if self._draft is not None or not self._selected.startswith("continent:"):
            current = next((p for p in self.recipe.provinces if p.id == self._selected), None)
            province = GeologyProvince(
                self._draft_id or self._selected,
                self.values["name"].get().strip(),
                tuple(self._draft)
                if self._draft is not None
                else current.vertices
                if current
                else (),
                int(self.values["priority"].get()),
                profile,
            )
            self._next_selected = province.id
            return replace(
                self.recipe,
                provinces=(*(p for p in self.recipe.provinces if p.id != province.id), province),
            )
        if (
            self.values["name"].get() != self._loaded_form[0]
            or self.values["priority"].get() != "0"
        ):
            raise ValueError(
                "Rename continents in the World workspace; priorities apply to provinces."
            )
        owner = self._selected.removeprefix("continent:")
        self._next_selected = self._selected
        return replace(
            self.recipe,
            defaults=tuple(
                ContinentGeology(owner, profile) if d.continent_id == owner else d
                for d in self.recipe.defaults
            ),
        )

    def apply(self, after: Callable[[], None] | None = None) -> None:
        if self.busy:
            return
        try:
            candidate = self._candidate()
        except ValueError as error:
            self.status.set(str(error))
            return
        self._work(
            "Resolving province priorities and land coverage…",
            lambda: _Result(resolve_geology(self.world, candidate, self._cancellation), "edit"),
            after,
        )

    def start_drawing(self, *, redraw: bool = False) -> None:
        if self.busy or self.form_dirty or self._draft is not None:
            self.status.set("Apply or revert the current edit before drawing.")
            return
        if redraw and self._selected.startswith("continent:"):
            self.status.set("Select a province to redraw its boundary.")
            return
        self._draft = []
        self._draft_id = self._selected if redraw else "province-" + uuid4().hex
        if not redraw:
            self._selected = self._draft_id
            self.tree.selection_remove(*self.tree.selection())
            self._load_form()
            names = {p.name for p in self.recipe.provinces}
            number = 1
            while f"Province {number}" in names:
                number += 1
            self.values["name"].set(f"Province {number}")
        self.status.set(
            "Click polygon vertices. Enter: finish · Backspace: remove vertex · "
            "Escape: cancel. Seam crossings follow the shorter longitude interval."
        )
        self.canvas.focus_set()
        self._schedule_draw()

    def remove_vertex(self) -> None:
        if not self.busy and self._draft:
            self._draft.pop()
            self._schedule_draw()

    def revert(self) -> None:
        if self.busy:
            return
        self._draft = None
        self._draft_id = None
        if not self.tree.exists(self._selected):
            self._selected = "continent:" + self.world.continents[0].id
        self._load_form()
        self._populate()
        self.status.set("Unapplied edit discarded.")
        self._schedule_draw()

    def delete(self) -> None:
        if self.busy or self.form_dirty or self._draft is not None:
            self.status.set("Apply or revert the current edit before deleting.")
            return
        if self._selected.startswith("continent:"):
            self.status.set("Continent defaults cannot be deleted; use unspecified / blank values.")
            return
        candidate = replace(
            self.recipe, provinces=tuple(p for p in self.recipe.provinces if p.id != self._selected)
        )
        self._next_selected = "continent:" + self.world.continents[0].id
        self._work(
            "Checking coverage after deletion…",
            lambda: _Result(resolve_geology(self.world, candidate, self._cancellation), "edit"),
        )

    def _history(self, undo: bool) -> None:
        source, target = (self._undo, self._redo) if undo else (self._redo, self._undo)
        if self.busy or self.form_dirty or self._draft is not None:
            self.status.set("Apply or revert the current edit before using history.")
            return
        if source and self.coverage:
            target.append(self.coverage)
            self.coverage = source.pop()
            self.recipe = self.coverage.recipe
            if not self._selected.startswith("continent:") and not any(
                p.id == self._selected for p in self.recipe.provinces
            ):
                self._selected = "continent:" + self.world.continents[0].id
            self._populate()
            self._load_form()
            self.status.set("Edit undone." if undo else "Edit restored.")
            self._schedule_draw()

    def undo(self) -> None:
        self._history(True)

    def redo(self) -> None:
        self._history(False)

    def _work(
        self,
        label: str,
        action: Callable[[], _Result],
        after: Callable[[], None] | None = None,
        *,
        cancellable: bool = True,
    ) -> None:
        if self.busy:
            return
        self.busy = True
        self.landform_form.set_busy(True)
        self._callback = after
        self._cancellation = CancellationToken() if cancellable else None
        for widget, _ in self._controls:
            widget["state"] = "disabled"
        self.cancel_button.configure(state="normal" if cancellable else "disabled")
        self.status.set(label)

        def worker() -> None:
            try:
                self._events.put(action())
            except Exception as error:
                self._events.put(error)

        threading.Thread(target=worker, name="world-geology-worker", daemon=True).start()

    def _poll(self) -> None:
        self._poll_id = None
        if self._closed:
            return
        if not self._events.empty():
            event = self._events.get_nowait()
            self.busy = False
            self.landform_form.set_busy(False)
            self._cancellation = None
            for widget, state in self._controls:
                widget["state"] = state
            self.cancel_button.configure(state="disabled")
            self._lock_identity_fields()
            callback, self._callback = self._callback, None
            if isinstance(event, Exception):
                self.status.set(
                    "Cancelled; previous recipe retained."
                    if isinstance(event, GenerationCancelled)
                    else str(event)
                )
            else:
                if event.mode == "edit" and self.coverage and event.coverage.recipe != self.recipe:
                    self._undo.append(self.coverage)
                    self._undo = self._undo[-20:]
                    self._redo.clear()
                self.coverage, self.recipe = event.coverage, event.coverage.recipe
                if event.mode in ("open", "save"):
                    self.file = event.file
                    self._saved_recipe = self.recipe
                if event.mode == "open":
                    self._undo.clear()
                    self._redo.clear()
                    self._next_selected = "continent:" + self.world.continents[0].id
                if event.mode in ("edit", "open"):
                    self._selected = self._next_selected
                self._draft = None
                self._draft_id = None
                self._populate()
                self._load_form()
                self.status.set(
                    f"{len(self.recipe.provinces)} provinces · "
                    f"{sum(r.area_km2 for r in self.coverage.regions):,.0f} km² land covered. "
                    + (
                        f"Saved {self.file.path.name}."
                        if event.mode == "save" and self.file
                        else "Coverage verified. Inputs remain geological hypotheses."
                    )
                )
                self._schedule_draw()
                if callback:
                    callback()
                    if self._closed:
                        return
        self._poll_id = self.after(60, self._poll)

    def cancel(self) -> None:
        if self._cancellation:
            self._cancellation.cancel()

    def choose_open(self) -> None:
        def choose() -> None:
            path = filedialog.askopenfilename(
                parent=self,
                title="Open geology inputs",
                filetypes=[("Geology recipe", "*.dmgeology.json")],
            )
            if path:
                self.load(Path(path))

        self.guard(choose)

    def load(self, path: Path) -> None:
        def operation() -> _Result:
            result = open_geology(path, self.world, self._cancellation)
            return _Result(result.coverage, "open", result)

        self._work("Opening and checking retained geology inputs…", operation)

    def save(self, *, save_as: bool = False, after: Callable[[], None] | None = None) -> None:
        if self.busy:
            return
        if self.form_dirty or self._draft is not None:
            self.apply(lambda: self.save(save_as=save_as, after=after))
            return
        if self.coverage is None:
            return
        path = self.file.path if self.file else None
        expected = self.file.sha256 if self.file else None
        if path is None or save_as:
            name = filedialog.asksaveasfilename(
                parent=self,
                title="Save geology inputs",
                defaultextension=GEOLOGY_EXTENSION,
                initialfile=path.name if path else "world.dmgeology.json",
                filetypes=[("Geology recipe", "*.dmgeology.json")],
            )
            if not name:
                return
            path = Path(name)
            try:
                # Same path must keep the loaded fingerprint, even through Save As.
                if self.file is None or path.resolve() != self.file.path.resolve():
                    expected = geology_file_hash(path)
            except (OSError, ValueError) as error:
                self.status.set(str(error))
                return
        coverage, target = self.coverage, path

        def operation() -> _Result:
            result = save_geology(coverage, target, expected)
            return _Result(result.coverage, "save", result)

        self._work(
            "Validating and saving portable geology recipe…", operation, after, cancellable=False
        )

    def guard(self, action: Callable[[], None]) -> None:
        if self.busy:
            self.status.set("Finish or cancel the current job before continuing.")
            self.lift()
            return
        if not self.dirty:
            action()
            return
        answer = messagebox.askyesnocancel(
            "Save geology inputs?",
            "Save the recipe before continuing? Unfinished or invalid polygons must be fixed "
            "or cancelled before saving.",
            parent=self,
        )
        if answer is True:
            self.save(after=action)
        elif answer is False:
            action()

    def fit(self) -> None:
        self.viewport.fit()
        self._schedule_draw()

    def _size(self) -> tuple[int, int]:
        return max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())

    def _position(self, event: tk.Event[tk.Misc]) -> Point2D | None:
        frame = self.world.project.frame
        left, top, right, bottom = self.viewport.rect(self._size(), (frame.width, frame.height))
        if not left <= event.x <= right or not top <= event.y <= bottom:
            return None
        return (
            frame.bounds[0] + (event.x - left) / (right - left) * frame.width,
            frame.bounds[1] + (event.y - top) / (bottom - top) * frame.height,
        )

    def _pick(self, event: tk.Event[tk.Misc]) -> None:
        self.canvas.focus_set()
        point = self._position(event)
        if self.busy or point is None:
            return
        if self._draft is not None:
            if len(self._draft) >= MAX_PROVINCE_VERTICES:
                self.status.set(f"Province vertex limit: {MAX_PROVINCE_VERTICES}.")
                return
            if self._draft:
                width = self.world.project.frame.width
                point = (
                    point[0] + round((self._draft[-1][0] - point[0]) / width) * width,
                    point[1],
                )
            self._draft.append(point)
            self.status.set(
                f"{len(self._draft)} vertices · Enter or Apply to finish. "
                "Backspace removes the last vertex; Escape cancels."
            )
            self._schedule_draw()
        elif self.coverage and not self.form_dirty:
            region = self.coverage.at(point)
            if region:
                self.tree.selection_set(region.id)

    def _motion(self, event: tk.Event[tk.Misc]) -> None:
        point = self._position(event)
        if point is None or self.coverage is None:
            return
        region = self.coverage.at(point)
        longitude, latitude = self.world.project.frame.source_to_lonlat(point)
        if region is None:
            text = "Water · land geology does not apply"
        else:
            p = region.profile
            ages = " · ".join(
                f"{label}: {value:g} Ma" if value is not None else f"{label}: unknown"
                for label, value in (
                    ("crust", p.crust_age_ma),
                    ("rejuvenation", p.rejuvenation_age_ma),
                    ("simulation", p.evolution_duration_ma),
                )
            )
            text = f"{region.name} · {p.setting} · {ages}"
        self.inspection.set(f"{latitude:.2f}°, {longitude:.2f}° · {text}")

    def _wheel(self, event: tk.Event[tk.Misc]) -> None:
        frame = self.world.project.frame
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
            frame = self.world.project.frame
            self.viewport.pan(
                (event.x - self._pan[0], event.y - self._pan[1]),
                self._size(),
                (frame.width, frame.height),
            )
            self._pan = (event.x, event.y)
            self._schedule_draw()

    def _schedule_draw(self) -> None:
        if not self._closed and self._draw_id is None:
            self._draw_id = self.after(30, self._draw)

    def _draw(self) -> None:
        self._draw_id = None
        self.canvas.delete("all")
        frame, project = self.world.project.frame, self.world.project
        if self.layer.get() == "Geology coverage" and self.coverage:
            preview = render_geology(self.coverage, self.viewport, self._size())
        elif self.context and self.layer.get() in CONTEXT_LAYERS:
            preview = render_world_context(
                self.context.context,
                self.viewport,
                self._size(),
                cast(ContextLayer, self.layer.get()),
                EXPOSURE_BEARINGS.index(self.bearing.get()),
            )
        else:
            preview = render_world_source(
                project.source,
                frame.bounds,
                project.assignments,
                self.viewport,
                self._size(),
                show_excluded=False,
            )
        with preview:
            self._photo = ImageTk.PhotoImage(preview, master=self)
        self.canvas.create_image(0, 0, image=self._photo, anchor="nw")
        left, top, right, bottom = self.viewport.rect(self._size(), (frame.width, frame.height))
        sx, sy = (right - left) / frame.width, (bottom - top) / frame.height
        self.canvas.create_rectangle(left, top, right, bottom, outline="#9bb4b3")
        outlines = [(p.vertices, p.name, p.id == self._selected) for p in self.recipe.provinces]
        if self._draft:
            outlines.append((tuple(self._draft), "Draft", True))
        for vertices, name, selected in outlines:
            if len(vertices) == 1:
                x = left + (vertices[0][0] - frame.bounds[0]) * sx
                y = top + (vertices[0][1] - frame.bounds[1]) * sy
                self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#fff2b6", outline=OCEAN)
                continue
            for offset in (-frame.width, 0.0, frame.width):
                points = [
                    (left + (x + offset - frame.bounds[0]) * sx, top + (y - frame.bounds[1]) * sy)
                    for x, y in vertices
                ]
                self.canvas.create_line(
                    *(v for point in (*points, points[0]) for v in point),
                    fill="#fff2b6" if selected else "#d8e2dc",
                    width=3 if selected else 1,
                    dash=(5, 3),
                )
                x, y = points[0]
                if left <= x <= right and top <= y <= bottom:
                    self.canvas.create_text(x + 5, y - 9, text=name, fill="#fff2b6", anchor="sw")
        if self.coverage and self._selected.startswith("continent:"):
            selected_region = next(
                (r for r in self.coverage.regions if r.id == self._selected), None
            )
            if selected_region:
                for component in selected_region.components:
                    for ring in (component.exterior, *component.holes):
                        self.canvas.create_line(
                            *(
                                v
                                for x, y in ring
                                for v in (
                                    left + (x - frame.bounds[0]) * sx,
                                    top + (y - frame.bounds[1]) * sy,
                                )
                            ),
                            fill="#fff2b6",
                            width=2,
                        )
        # Cover off-frame copies without touching the source image.
        width, height = self._size()
        for bounds in (
            (0, 0, max(0, left), height),
            (min(width, right), 0, width, height),
            (0, 0, width, max(0, top)),
            (0, min(height, bottom), width, height),
        ):
            self.canvas.create_rectangle(*bounds, fill=OCEAN, outline="")
        self.canvas.create_rectangle(left, top, right, bottom, outline="#9bb4b3")

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
