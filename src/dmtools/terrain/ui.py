# pyright: reportUnknownMemberType=false
"""Tk desktop interface for the first terrain-generator vertical slice."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from dmtools.terrain.adapters import (
    CoastlineInputError,
    load_svg_coastline,
    render_height_map,
    save_height_map,
)
from dmtools.terrain.domain import Coastline, TerrainSettings
from dmtools.terrain.pipeline import GeneratedTerrain, generate_terrain

_INK = "#172225"
_MUTED = "#65716f"
_PAPER = "#f1ede3"
_PANEL = "#fbf8ef"
_BORDER = "#d2ccbd"
_ACCENT = "#1d7772"
_ACCENT_ACTIVE = "#155e5a"
_PREVIEW = "#172225"


@dataclass(frozen=True, slots=True)
class _ControlSpec:
    key: str
    label: str
    minimum: float
    maximum: float
    default: float
    increment: float
    unit: str = ""
    integer: bool = False


@dataclass(frozen=True, slots=True)
class _ProgressEvent:
    fraction: float
    message: str


@dataclass(frozen=True, slots=True)
class _ResultEvent:
    terrain: GeneratedTerrain
    image: Image.Image


@dataclass(frozen=True, slots=True)
class _CoastlineEvent:
    coastline: Coastline


@dataclass(frozen=True, slots=True)
class _ErrorEvent:
    title: str
    status: str
    error: Exception


type _UiEvent = _ProgressEvent | _ResultEvent | _CoastlineEvent | _ErrorEvent


_CONTROLS = (
    _ControlSpec("seed", "Seed", 0, 4_294_967_295, 20_260_902, 1, integer=True),
    _ControlSpec("object_scale_km", "Object scale", 100, 12_000, 4_000, 100, "km"),
    _ControlSpec("resolution_px", "Output resolution", 256, 2_048, 768, 128, "px", True),
    _ControlSpec("maximum_elevation_m", "Elevation ceiling", 250, 10_000, 4_500, 100, "m"),
    _ControlSpec("largest_feature_km", "Largest feature", 25, 2_000, 450, 25, "km"),
    _ControlSpec("detail_levels", "Detail levels", 1, 10, 6, 1, integer=True),
    _ControlSpec("roughness", "Fine-detail strength", 0.25, 0.85, 0.55, 0.01),
    _ControlSpec("coastal_rise_km", "Coastal rise distance", 5, 1_000, 180, 5, "km"),
    _ControlSpec("variability", "Elevation variability", 0, 1, 0.75, 0.01),
)


class TerrainApp:
    """Small local workbench for importing, generating, previewing, and exporting."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("DM Tools — Terrain Lab")
        self.root.geometry("1280x840")
        self.root.minsize(1040, 700)
        self.root.configure(background=_PAPER)

        self._coastline: Coastline | None = None
        self._terrain: GeneratedTerrain | None = None
        self._image: Image.Image | None = None
        self._preview_photo: ImageTk.PhotoImage | None = None
        self._events: queue.Queue[_UiEvent] = queue.Queue()
        self._variables: dict[str, tk.DoubleVar] = {}
        self._value_labels: dict[str, ttk.Label] = {}
        self._specs = {spec.key: spec for spec in _CONTROLS}

        self._configure_styles()
        self._build_layout()
        self.root.after(80, self._poll_events)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Paper.TFrame", background=_PAPER)
        style.configure("Panel.TFrame", background=_PANEL)
        style.configure(
            "Header.TLabel", background=_PAPER, foreground=_INK, font=("Segoe UI", 22, "bold")
        )
        style.configure(
            "Eyebrow.TLabel", background=_PAPER, foreground=_ACCENT, font=("Segoe UI", 9, "bold")
        )
        style.configure("Body.TLabel", background=_PANEL, foreground=_INK, font=("Segoe UI", 9))
        style.configure("Muted.TLabel", background=_PANEL, foreground=_MUTED, font=("Segoe UI", 9))
        style.configure(
            "Value.TLabel", background=_PANEL, foreground=_ACCENT, font=("Consolas", 9, "bold")
        )
        style.configure(
            "Accent.TButton",
            background=_ACCENT,
            foreground="#ffffff",
            padding=(18, 11),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Accent.TButton", background=[("active", _ACCENT_ACTIVE), ("disabled", "#9ba9a6")]
        )
        style.configure("Quiet.TButton", background=_PANEL, foreground=_INK, padding=(12, 8))
        style.configure(
            "Terrain.Horizontal.TProgressbar",
            troughcolor="#d9d4c7",
            background=_ACCENT,
            bordercolor="#d9d4c7",
            lightcolor=_ACCENT,
            darkcolor=_ACCENT,
        )

    def _build_layout(self) -> None:
        page = ttk.Frame(self.root, style="Paper.TFrame", padding=(24, 20, 24, 22))
        page.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        page.columnconfigure(1, weight=1)
        page.rowconfigure(1, weight=1)

        header = ttk.Frame(page, style="Paper.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        ttk.Label(header, text="DM TOOLS  /  TERRAIN", style="Eyebrow.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(header, text="Coastline Terrain Lab", style="Header.TLabel").grid(
            row=1, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="A deterministic first relief pass from one closed SVG coastline.",
            style="Eyebrow.TLabel",
        ).grid(row=2, column=0, sticky="w", pady=(3, 0))

        controls = ttk.Frame(page, style="Panel.TFrame", padding=(18, 18))
        controls.grid(row=1, column=0, sticky="nsw", padx=(0, 16))
        controls.columnconfigure(0, weight=1)
        self._build_import_panel(controls)
        for row, spec in enumerate(_CONTROLS, start=2):
            self._build_numeric_control(controls, row, spec)
        self._build_actions(controls, len(_CONTROLS) + 2)

        preview_shell = tk.Frame(
            page, background=_PREVIEW, highlightthickness=1, highlightbackground="#28383a"
        )
        preview_shell.grid(row=1, column=1, sticky="nsew")
        preview_shell.rowconfigure(1, weight=1)
        preview_shell.columnconfigure(0, weight=1)
        self._build_preview(preview_shell)

    def _build_import_panel(self, parent: ttk.Frame) -> None:
        top = ttk.Frame(parent, style="Panel.TFrame")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text="COASTLINE SOURCE", style="Value.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.import_button = ttk.Button(
            top, text="Import SVG…", style="Quiet.TButton", command=self._choose_svg
        )
        self.import_button.grid(row=0, column=1, rowspan=2, padx=(12, 0))
        self.source_label = ttk.Label(
            top, text="No coastline loaded", style="Muted.TLabel", width=34
        )
        self.source_label.grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Separator(parent).grid(row=1, column=0, sticky="ew", pady=(0, 9))

    def _build_numeric_control(self, parent: ttk.Frame, row: int, spec: _ControlSpec) -> None:
        container = ttk.Frame(parent, style="Panel.TFrame")
        container.grid(row=row, column=0, sticky="ew", pady=3)
        container.columnconfigure(0, weight=1)
        variable = tk.DoubleVar(value=spec.default)
        self._variables[spec.key] = variable

        ttk.Label(container, text=spec.label, style="Body.TLabel").grid(row=0, column=0, sticky="w")
        value_label = ttk.Label(container, style="Value.TLabel", width=14, anchor="e")
        value_label.grid(row=0, column=1, sticky="e")
        self._value_labels[spec.key] = value_label

        scale = ttk.Scale(
            container,
            from_=spec.minimum,
            to=spec.maximum,
            variable=variable,
            command=lambda _value, key=spec.key: self._refresh_value(key),
        )
        scale.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        spinbox = ttk.Spinbox(
            container,
            from_=spec.minimum,
            to=spec.maximum,
            increment=spec.increment,
            textvariable=variable,
            width=10,
            command=lambda key=spec.key: self._refresh_value(key),
        )
        spinbox.grid(row=1, column=1, sticky="e")
        spinbox.bind("<FocusOut>", lambda _event, key=spec.key: self._refresh_value(key))
        spinbox.bind("<Return>", lambda _event, key=spec.key: self._refresh_value(key))
        self._refresh_value(spec.key)

    def _build_actions(self, parent: ttk.Frame, row: int) -> None:
        ttk.Separator(parent).grid(row=row, column=0, sticky="ew", pady=(12, 12))
        buttons = ttk.Frame(parent, style="Panel.TFrame")
        buttons.grid(row=row + 1, column=0, sticky="ew")
        buttons.columnconfigure(0, weight=1)
        self.generate_button = ttk.Button(
            buttons, text="Generate terrain", style="Accent.TButton", command=self._generate
        )
        self.generate_button.grid(row=0, column=0, sticky="ew")
        self.export_button = ttk.Button(
            buttons,
            text="Export PNG…",
            style="Quiet.TButton",
            state="disabled",
            command=self._export,
        )
        self.export_button.grid(row=0, column=1, padx=(8, 0))

        self.progress = ttk.Progressbar(
            parent, style="Terrain.Horizontal.TProgressbar", mode="determinate", maximum=100
        )
        self.progress.grid(row=row + 2, column=0, sticky="ew", pady=(12, 0))
        self.status_label = ttk.Label(
            parent, text="Import one closed SVG loop to begin.", style="Muted.TLabel"
        )
        self.status_label.grid(row=row + 3, column=0, sticky="w", pady=(6, 0))

    def _build_preview(self, parent: tk.Frame) -> None:
        toolbar = tk.Frame(parent, background=_PREVIEW)
        toolbar.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 8))
        tk.Label(
            toolbar,
            text="ELEVATION PREVIEW",
            background=_PREVIEW,
            foreground="#dce8e3",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")
        self.preview_meta = tk.Label(
            toolbar,
            text="Awaiting coastline",
            background=_PREVIEW,
            foreground="#80918e",
            font=("Consolas", 9),
        )
        self.preview_meta.pack(side="right")

        content = tk.Frame(parent, background=_PREVIEW)
        content.grid(row=1, column=0, sticky="nsew", padx=(16, 12), pady=(0, 14))
        content.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=1)
        self.preview = tk.Canvas(content, background="#10191b", highlightthickness=0)
        self.preview.grid(row=0, column=0, sticky="nsew")
        self.preview.create_text(
            20,
            20,
            text="Import a coastline\nto establish the land mask.",
            anchor="nw",
            fill="#71817e",
            font=("Segoe UI", 14),
        )
        self.preview.bind("<Configure>", lambda _event: self._draw_preview())

        legend = tk.Frame(content, background=_PREVIEW, width=64)
        legend.grid(row=0, column=1, sticky="ns", padx=(12, 0))
        tk.Label(
            legend,
            text="HIGH",
            background=_PREVIEW,
            foreground="#9eaaa8",
            font=("Segoe UI", 7, "bold"),
        ).pack()
        for colour in ("#f4f2eb", "#aaa497", "#6f5b45", "#a68752", "#50744e", "#7e9b65", "#d6c491"):
            tk.Frame(legend, background=colour, width=22, height=34).pack()
        tk.Label(
            legend,
            text="0 m",
            background=_PREVIEW,
            foreground="#9eaaa8",
            font=("Segoe UI", 7, "bold"),
        ).pack(pady=(3, 0))

    def _refresh_value(self, key: str) -> None:
        spec = self._specs[key]
        try:
            raw = float(self._variables[key].get())
        except tk.TclError, ValueError:
            return
        value = round(raw) if spec.integer else raw
        rendered = (
            f"{value:,.0f}" if spec.integer or spec.increment >= 1 else f"{value:.2f}"
        )
        if spec.unit:
            rendered = f"{rendered} {spec.unit}"
        self._value_labels[key].configure(text=rendered)

    def _choose_svg(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self.root,
            title="Import one closed coastline",
            filetypes=(("SVG vector", "*.svg"), ("All files", "*.*")),
        )
        if not selected:
            return
        source = Path(selected)
        self.import_button.configure(state="disabled")
        self.generate_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        self.source_label.configure(text=f"Reading {source.name}…")
        self.status_label.configure(text="Validating coastline in the background…")
        self.progress.configure(mode="indeterminate", value=0)
        self.progress.start(12)

        def worker() -> None:
            try:
                self._events.put(_CoastlineEvent(load_svg_coastline(source)))
            except CoastlineInputError as error:
                self._events.put(
                    _ErrorEvent(
                        title="Coastline could not be imported",
                        status="Coastline import failed.",
                        error=error,
                    )
                )
            except Exception as error:
                self._events.put(
                    _ErrorEvent(
                        title="Unexpected import failure",
                        status="Coastline import failed.",
                        error=error,
                    )
                )

        threading.Thread(target=worker, name="coastline-importer", daemon=True).start()

    def _accept_coastline(self, coastline: Coastline) -> None:
        self._coastline = coastline
        self._terrain = None
        self._image = None
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)
        self.import_button.configure(state="normal")
        self.generate_button.configure(state="normal")
        self.export_button.configure(state="disabled")
        self.source_label.configure(text=coastline.source_name)
        self.status_label.configure(text="Coastline valid. Adjust settings or generate.")
        self.preview_meta.configure(text=f"{len(coastline.points) - 1:,} sampled boundary points")
        self.preview.delete("all")
        self.preview.create_text(
            20,
            20,
            text="Coastline accepted.\nReady to generate.",
            anchor="nw",
            fill="#87a09b",
            font=("Segoe UI", 14),
        )

    def _read_settings(self) -> TerrainSettings:
        values = {key: variable.get() for key, variable in self._variables.items()}
        return TerrainSettings(
            seed=round(values["seed"]),
            object_scale_km=values["object_scale_km"],
            resolution_px=round(values["resolution_px"]),
            maximum_elevation_m=values["maximum_elevation_m"],
            largest_feature_km=values["largest_feature_km"],
            detail_levels=round(values["detail_levels"]),
            roughness=values["roughness"],
            coastal_rise_km=values["coastal_rise_km"],
            variability=values["variability"],
        )

    def _generate(self) -> None:
        if self._coastline is None:
            messagebox.showinfo(
                "Import a coastline", "Choose one closed SVG vector object first.", parent=self.root
            )
            return
        try:
            settings = self._read_settings()
        except (ValueError, tk.TclError) as error:
            messagebox.showerror("Invalid settings", str(error), parent=self.root)
            return

        self.generate_button.configure(state="disabled")
        self.import_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)
        self.status_label.configure(text="Starting deterministic generation…")
        coastline = self._coastline

        def worker() -> None:
            try:
                terrain = generate_terrain(
                    coastline,
                    settings,
                    lambda fraction, message: self._events.put(_ProgressEvent(fraction, message)),
                )
                self._events.put(_ProgressEvent(0.97, "Rendering colour relief"))
                image = render_height_map(terrain)
                self._events.put(_ResultEvent(terrain, image))
            except Exception as error:
                self._events.put(
                    _ErrorEvent(
                        title="Terrain generation failed",
                        status="Generation failed.",
                        error=error,
                    )
                )

        threading.Thread(target=worker, name="terrain-generator", daemon=True).start()

    def _poll_events(self) -> None:
        try:
            while True:
                event = self._events.get_nowait()
                if isinstance(event, _ProgressEvent):
                    self.progress.configure(value=event.fraction * 100.0)
                    self.status_label.configure(text=event.message)
                elif isinstance(event, _CoastlineEvent):
                    self._accept_coastline(event.coastline)
                elif isinstance(event, _ResultEvent):
                    self._terrain = event.terrain
                    self._image = event.image
                    self.progress.stop()
                    self.progress.configure(mode="determinate")
                    self.progress.configure(value=100)
                    self.status_label.configure(
                        text="Terrain ready. Preview or export the colour height map."
                    )
                    peak = float(event.terrain.elevation_m[event.terrain.land_mask].max())
                    self.preview_meta.configure(
                        text=(
                            f"{event.terrain.width} x {event.terrain.height} px"
                            f"  ·  peak {peak:,.0f} m"
                        )
                    )
                    self.import_button.configure(state="normal")
                    self.generate_button.configure(state="normal")
                    self.export_button.configure(state="normal")
                    self._draw_preview()
                else:
                    self.progress.stop()
                    self.progress.configure(mode="determinate", value=0)
                    self.import_button.configure(state="normal")
                    self.generate_button.configure(
                        state="normal" if self._coastline is not None else "disabled"
                    )
                    self.export_button.configure(
                        state="normal" if self._terrain is not None else "disabled"
                    )
                    source_name = (
                        self._coastline.source_name
                        if self._coastline is not None
                        else "No coastline loaded"
                    )
                    self.source_label.configure(text=source_name)
                    self.status_label.configure(text=event.status)
                    messagebox.showerror(event.title, str(event.error), parent=self.root)
        except queue.Empty:
            pass
        self.root.after(80, self._poll_events)

    def _draw_preview(self) -> None:
        if self._image is None:
            return
        width = max(1, self.preview.winfo_width() - 32)
        height = max(1, self.preview.winfo_height() - 32)
        display = self._image.copy()
        display.thumbnail((width, height), Image.Resampling.LANCZOS)
        self._preview_photo = ImageTk.PhotoImage(display)
        self.preview.delete("all")
        self.preview.create_image(
            self.preview.winfo_width() // 2,
            self.preview.winfo_height() // 2,
            image=self._preview_photo,
            anchor="center",
        )

    def _export(self) -> None:
        if self._terrain is None or self._image is None:
            return
        stem = Path(self._terrain.source_name).stem
        selected = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export colour height map",
            initialfile=f"{stem}-height-map.png",
            defaultextension=".png",
            filetypes=(("PNG image", "*.png"),),
        )
        if not selected:
            return
        try:
            save_height_map(self._image, self._terrain, Path(selected))
        except OSError as error:
            messagebox.showerror("Export failed", str(error), parent=self.root)
            return
        self.status_label.configure(text=f"Exported {Path(selected).name}")


def run() -> None:
    """Launch the local terrain workbench."""

    root = tk.Tk()
    TerrainApp(root)
    root.mainloop()
