# pyright: reportUnknownMemberType=false
"""Tk desktop interface for the first terrain-generator vertical slice."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from dataclasses import dataclass
from math import hypot
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import unary_union

from dmtools.terrain.adapters import (
    PROJECT_EXTENSION,
    CoastlineInputError,
    CoastlineSource,
    LoadedTerrainProject,
    RenderStyle,
    TerrainProjectInputError,
    elevation_legend_colours,
    load_svg_coastline_source,
    load_terrain_project,
    render_height_map,
    save_height_map,
    save_terrain_project,
)
from dmtools.terrain.adapters.render import render_drainage_overlay
from dmtools.terrain.domain import (
    BrushToolSettings,
    Coastline,
    ElevationMode,
    ElevationPoint,
    FeatureToolSettings,
    LandformSettings,
    TerrainAuthoringState,
    TerrainBrushStroke,
    TerrainConstraint,
    TerrainProject,
    TerrainRegion,
    TerrainSettings,
    TerrainStructure,
    landform_preset,
)
from dmtools.terrain.pipeline import GeneratedTerrain, generate_terrain

_INK = "#172225"
_MUTED = "#65716f"
_PAPER = "#f1ede3"
_PANEL = "#fbf8ef"
_BORDER = "#d2ccbd"
_ACCENT = "#1d7772"
_ACCENT_ACTIVE = "#155e5a"
_PREVIEW = "#172225"
_MAP_BACKGROUND = "#10191b"
_HEIGHT_COLOUR = "#f2c14e"
_RIDGE_COLOUR = "#e47b58"
_VALLEY_COLOUR = "#54a6c2"
_BRUSH_COLOUR = "#9fbe72"
_REGION_COLOUR = "#c5b6f5"

_RENDER_STYLE_LABELS: dict[str, RenderStyle] = {
    "Cartographic relief": "cartographic",
    "Scientific elevation": "scientific",
}


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
    source: CoastlineSource


@dataclass(frozen=True, slots=True)
class _ProjectEvent:
    loaded: LoadedTerrainProject


@dataclass(frozen=True, slots=True)
class _ProjectSavedEvent:
    path: Path


@dataclass(frozen=True, slots=True)
class _ErrorEvent:
    title: str
    status: str
    error: Exception


type _UiEvent = (
    _ProgressEvent
    | _ResultEvent
    | _CoastlineEvent
    | _ProjectEvent
    | _ProjectSavedEvent
    | _ErrorEvent
)


_CONTROLS = (
    _ControlSpec("seed", "Seed", 0, 4_294_967_295, 20_260_902, 1, integer=True),
    _ControlSpec("object_scale_km", "Object scale", 100, 12_000, 4_000, 100, "km"),
    _ControlSpec("resolution_px", "Output resolution", 256, 2_048, 768, 128, "px", True),
    _ControlSpec("maximum_elevation_m", "Elevation ceiling", 250, 12_000, 4_500, 100, "m"),
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
        self._coastline_source: CoastlineSource | None = None
        self._project_path: Path | None = None
        self._terrain: GeneratedTerrain | None = None
        self._image: Image.Image | None = None
        self._preview_photo: ImageTk.PhotoImage | None = None
        self._coast_polygon: Polygon | MultiPolygon | None = None
        self._constraints: list[TerrainConstraint] = []
        self._draft_points: list[tuple[float, float]] = []
        self._events: queue.Queue[_UiEvent] = queue.Queue()
        self._variables: dict[str, tk.DoubleVar] = {}
        self._value_labels: dict[str, ttk.Label] = {}
        self._specs = {spec.key: spec for spec in _CONTROLS}
        authoring_defaults = TerrainAuthoringState()
        self._authoring_tool = tk.StringVar(value=authoring_defaults.active_tool)
        self._tool_modes = {
            "brush": tk.StringVar(value=authoring_defaults.brush.elevation_mode.title()),
            "height": tk.StringVar(value=authoring_defaults.height.elevation_mode.title()),
            "ridge": tk.StringVar(value=authoring_defaults.ridge.elevation_mode.title()),
            "valley": tk.StringVar(value=authoring_defaults.valley.elevation_mode.title()),
        }
        self._tool_elevations = {
            "brush": tk.DoubleVar(value=authoring_defaults.brush.elevation_m),
            "height": tk.DoubleVar(value=authoring_defaults.height.elevation_m),
            "ridge": tk.DoubleVar(value=authoring_defaults.ridge.elevation_m),
            "valley": tk.DoubleVar(value=authoring_defaults.valley.elevation_m),
        }
        self._tool_sizes = {
            "brush": tk.DoubleVar(value=authoring_defaults.brush.width_km),
            "height": tk.DoubleVar(value=authoring_defaults.height.radius_km),
            "ridge": tk.DoubleVar(value=authoring_defaults.ridge.radius_km),
            "valley": tk.DoubleVar(value=authoring_defaults.valley.radius_km),
        }
        self._brush_intensity_percent = tk.DoubleVar(
            value=authoring_defaults.brush.intensity * 100.0
        )
        self._region_character = tk.StringVar(value="plain")
        self._region_values = {
            name: tk.DoubleVar(value=float(getattr(authoring_defaults.region, name)))
            for name in ("elevation_m", "relief_m", "feature_size_km", "transition_km",
                         "orientation_deg")
        }
        self._render_style_label = tk.StringVar(value="Cartographic relief")
        self._show_drainage = tk.BooleanVar(value=False)
        self._drainage_photo: ImageTk.PhotoImage | None = None
        self._legend_swatches: list[tk.Frame] = []
        self._brush_cursor: tuple[float, float] | None = None
        self._active_brush_values: tuple[float, float, float, ElevationMode] | None = None
        self._tool_buttons: dict[str, tk.Button] = {}
        self._authoring_widgets: list[tk.Widget] = []
        self._authoring_enabled = False

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
            text="Sketch elevation controls, ridges, and valleys before deterministic generation.",
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
        preview_shell.rowconfigure(2, weight=1)
        preview_shell.columnconfigure(0, weight=1)
        self._build_preview(preview_shell)

    def _build_import_panel(self, parent: ttk.Frame) -> None:
        top = ttk.Frame(parent, style="Panel.TFrame")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text="COASTLINE SOURCE", style="Value.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.source_label = ttk.Label(
            top, text="No land geometry loaded", style="Muted.TLabel", width=34
        )
        self.source_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(3, 7))
        self.import_button = ttk.Button(
            top, text="Import SVG…", style="Quiet.TButton", command=self._choose_svg
        )
        self.import_button.grid(row=2, column=0, sticky="ew")
        self.open_project_button = ttk.Button(
            top, text="Open project…", style="Quiet.TButton", command=self._choose_project
        )
        self.open_project_button.grid(row=2, column=1, sticky="ew", padx=(6, 0))
        self.save_project_button = ttk.Button(
            top,
            text="Save project…",
            style="Quiet.TButton",
            state="disabled",
            command=self._save_project,
        )
        self.save_project_button.grid(row=2, column=2, sticky="ew", padx=(6, 0))
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
            parent, text="Import closed SVG land shapes to begin.", style="Muted.TLabel",
            wraplength=300, justify="left",
        )
        self.status_label.grid(row=row + 3, column=0, sticky="w", pady=(6, 0))

    def _build_preview(self, parent: tk.Frame) -> None:
        toolbar_container = tk.Frame(parent, background=_PREVIEW)
        toolbar_container.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 8))
        toolbar = tk.Frame(toolbar_container, background=_PREVIEW)
        toolbar.pack(fill="x")
        tk.Label(
            toolbar,
            text="ELEVATION PREVIEW",
            background=_PREVIEW,
            foreground="#dce8e3",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")
        tk.Checkbutton(
            toolbar, text="Drainage review", variable=self._show_drainage,
            command=self._draw_preview, background=_PREVIEW, foreground="#dce8e3",
            selectcolor=_PREVIEW, activebackground=_PREVIEW, activeforeground="white",
        ).pack(side="left", padx=10)
        self.preview_meta = tk.Label(
            toolbar_container,
            text="Awaiting land geometry",
            background=_PREVIEW,
            foreground="#80918e",
            font=("Consolas", 9),
        )
        self.preview_meta.pack(anchor="w", pady=(4, 0))
        self.render_style_input = ttk.Combobox(
            toolbar,
            values=tuple(_RENDER_STYLE_LABELS),
            textvariable=self._render_style_label,
            width=20,
            state="readonly",
            font=("Segoe UI", 8),
        )
        self.render_style_input.pack(side="right", padx=(12, 0))
        self.render_style_input.bind("<<ComboboxSelected>>", self._on_render_style_changed)
        tk.Label(
            toolbar,
            text="STYLE",
            background=_PREVIEW,
            foreground="#80918e",
            font=("Consolas", 8, "bold"),
        ).pack(side="right", padx=(12, 0))

        authoring = tk.Frame(parent, background="#203033", padx=10, pady=8)
        authoring.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        authoring.columnconfigure(5, weight=1)

        tk.Label(
            authoring,
            text="DRAW",
            background="#203033",
            foreground="#8fa5a1",
            font=("Consolas", 8, "bold"),
        ).grid(row=0, column=0, padx=(0, 7))
        for column, (tool, label) in enumerate(
            (
                ("brush", "Terrain brush"),
                ("height", "Height point"),
                ("ridge", "Ridge line"),
                ("valley", "Valley line"),
                ("region", "Landform region"),
            ),
            start=1,
        ):
            button = tk.Button(
                authoring,
                text=label,
                command=lambda selected=tool: self._set_authoring_tool(selected),
                relief="flat",
                borderwidth=0,
                padx=9,
                pady=5,
                cursor="hand2",
                font=("Segoe UI", 8, "bold"),
            )
            button.grid(row=0, column=column, padx=2)
            self._tool_buttons[tool] = button
            self._authoring_widgets.append(button)

        actions = tk.Frame(authoring, background="#203033")
        actions.grid(row=0, column=6, padx=(12, 0))
        self.finish_line_button = tk.Button(
            actions,
            text="Finish line",
            command=self._finish_structure,
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=5,
            font=("Segoe UI", 8),
        )
        self.finish_line_button.pack(side="left", padx=2)
        self.undo_constraint_button = tk.Button(
            actions,
            text="Undo",
            command=self._undo_constraint,
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=5,
            font=("Segoe UI", 8),
        )
        self.undo_constraint_button.pack(side="left", padx=2)
        self.clear_constraints_button = tk.Button(
            actions,
            text="Clear",
            command=self._clear_constraints,
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=5,
            font=("Segoe UI", 8),
        )
        self.clear_constraints_button.pack(side="left", padx=2)
        self._authoring_widgets.extend(
            [
                self.finish_line_button,
                self.undo_constraint_button,
                self.clear_constraints_button,
            ]
        )

        parameters = tk.Frame(authoring, background="#203033")
        self._feature_parameters = parameters
        parameters.grid(row=1, column=0, columnspan=7, sticky="w", pady=(7, 0))
        tk.Label(
            parameters,
            text="Mode",
            background="#203033",
            foreground="#a9bab7",
            font=("Segoe UI", 8),
        ).pack(side="left", padx=(0, 4))
        self.mode_input = ttk.Combobox(
            parameters,
            values=("Absolute", "Relative"),
            textvariable=self._tool_modes["brush"],
            width=9,
            state="readonly",
            font=("Segoe UI", 8),
        )
        self.mode_input.pack(side="left")
        self.mode_input.bind("<<ComboboxSelected>>", self._on_elevation_mode_changed)
        self.value_label = tk.Label(
            parameters,
            text="Height offset",
            background="#203033",
            foreground="#a9bab7",
            font=("Segoe UI", 8),
        )
        self.value_label.pack(side="left", padx=(12, 4))
        self.value_input = tk.Spinbox(
            parameters,
            from_=-10_000,
            to=10_000,
            increment=100,
            textvariable=self._tool_elevations["brush"],
            width=7,
            justify="right",
            font=("Consolas", 8),
        )
        self.value_input.pack(side="left")
        self._authoring_widgets.append(self.value_input)
        tk.Label(
            parameters,
            text="m",
            background="#203033",
            foreground="#a9bab7",
            font=("Segoe UI", 8),
        ).pack(side="left", padx=(3, 12))
        self.width_label = tk.Label(
            parameters,
            text="Influence radius",
            background="#203033",
            foreground="#a9bab7",
            font=("Segoe UI", 8),
        )
        self.width_label.pack(side="left", padx=(0, 4))
        self.width_input = tk.Spinbox(
            parameters,
            from_=1,
            to=4_000,
            increment=10,
            textvariable=self._tool_sizes["brush"],
            width=7,
            justify="right",
            font=("Consolas", 8),
        )
        self.width_input.pack(side="left")
        self._authoring_widgets.append(self.width_input)
        tk.Label(
            parameters,
            text="km",
            background="#203033",
            foreground="#a9bab7",
            font=("Segoe UI", 8),
        ).pack(side="left", padx=(3, 12))
        tk.Label(
            parameters,
            text="Brush strength",
            background="#203033",
            foreground="#a9bab7",
            font=("Segoe UI", 8),
        ).pack(side="left", padx=(0, 4))
        self.brush_strength_input = tk.Spinbox(
            parameters,
            from_=5,
            to=100,
            increment=5,
            textvariable=self._brush_intensity_percent,
            width=5,
            justify="right",
            font=("Consolas", 8),
        )
        self.brush_strength_input.pack(side="left")
        self._authoring_widgets.append(self.brush_strength_input)
        tk.Label(
            parameters,
            text="%",
            background="#203033",
            foreground="#a9bab7",
            font=("Segoe UI", 8),
        ).pack(side="left", padx=(3, 0))

        self._region_parameters = tk.Frame(authoring, background="#203033")
        self._region_parameters.grid(row=1, column=0, columnspan=7, sticky="w", pady=(7, 0))
        self._region_character_input = ttk.Combobox(
            self._region_parameters, textvariable=self._region_character,
            values=("plain", "hills", "plateau", "mountains"), width=12, state="readonly",
        )
        self._region_character_input.grid(row=0, column=0, padx=(0, 8))
        self._region_character_input.bind("<<ComboboxSelected>>", self._on_region_character)
        for index, (key, label, upper) in enumerate((
            ("elevation_m", "Base height m", 10000),
            ("relief_m", "Relief m", 10000),
            ("feature_size_km", "Feature size km", 4000),
            ("transition_km", "Transition km", 2000),
            ("orientation_deg", "Direction deg", 179),
        )):
            row, column = divmod(index, 3)
            frame = tk.Frame(self._region_parameters, background="#203033")
            frame.grid(row=row, column=column + 1, padx=6, pady=3, sticky="w")
            tk.Label(frame, text=label, background="#203033", foreground="#a9bab7",
                     font=("Segoe UI", 8)).pack(side="left", padx=(0, 4))
            entry = tk.Spinbox(frame, textvariable=self._region_values[key], width=6,
                               from_=1 if key.endswith("_km") else 0, to=upper,
                               increment=1 if key == "orientation_deg" else 10)
            entry.pack(side="left")
            self._authoring_widgets.append(entry)
        self._region_parameters.grid_remove()

        self.authoring_hint = tk.Label(
            authoring,
            text="Import land geometry to start drawing.",
            background="#203033",
            foreground="#8fa5a1",
            font=("Segoe UI", 8),
        )
        self.authoring_hint.grid(row=2, column=0, columnspan=7, sticky="w", pady=(6, 0))

        content = tk.Frame(parent, background=_PREVIEW)
        content.grid(row=2, column=0, sticky="nsew", padx=(16, 12), pady=(0, 14))
        content.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=1)
        self.preview = tk.Canvas(content, background=_MAP_BACKGROUND, highlightthickness=0)
        self.preview.grid(row=0, column=0, sticky="nsew")
        self.preview.create_text(
            20,
            20,
            text="Import SVG land shapes\nto establish the land mask.",
            anchor="nw",
            fill="#71817e",
            font=("Segoe UI", 14),
        )
        self.preview.bind("<Configure>", lambda _event: self._draw_preview())
        self.preview.bind("<ButtonPress-1>", self._on_map_press)
        self.preview.bind("<B1-Motion>", self._on_map_drag)
        self.preview.bind("<ButtonRelease-1>", self._on_map_release)
        self.preview.bind("<Motion>", self._on_map_motion)
        self.preview.bind("<Leave>", self._on_map_leave)
        self.preview.bind("<MouseWheel>", self._on_map_wheel)
        self.preview.bind("<Button-3>", lambda _event: self._finish_structure())

        legend = tk.Frame(content, background=_PREVIEW, width=64)
        legend.grid(row=0, column=1, sticky="ns", padx=(12, 0))
        self._legend_high_label = tk.Label(
            legend,
            text="10 km",
            background=_PREVIEW,
            foreground="#9eaaa8",
            font=("Segoe UI", 7, "bold"),
        )
        self._legend_high_label.pack()
        for colour in elevation_legend_colours():
            swatch = tk.Frame(legend, background=colour, width=22, height=34)
            swatch.pack()
            self._legend_swatches.append(swatch)
        tk.Label(
            legend,
            text="0 m",
            background=_PREVIEW,
            foreground="#9eaaa8",
            font=("Segoe UI", 7, "bold"),
        ).pack(pady=(3, 0))
        self._set_authoring_enabled(False)
        self._set_authoring_tool("brush")

    def _selected_render_style(self) -> RenderStyle:
        return _RENDER_STYLE_LABELS.get(self._render_style_label.get(), "cartographic")

    def _on_render_style_changed(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        style = self._selected_render_style()
        self._legend_high_label.configure(text="10 km" if style == "cartographic" else "MAX")
        for swatch, colour in zip(
            self._legend_swatches,
            elevation_legend_colours(style=style),
            strict=True,
        ):
            swatch.configure(background=colour)
        if self._terrain is None:
            return
        self._image = render_height_map(self._terrain, style=style)
        self.status_label.configure(
            text=(
                "Cartographic relief ready."
                if style == "cartographic"
                else "Scientific elevation view ready."
            )
        )
        self._draw_preview()

    def _set_authoring_enabled(self, enabled: bool) -> None:
        self._authoring_enabled = enabled
        state = "normal" if enabled else "disabled"
        for widget in self._authoring_widgets:
            widget["state"] = state
        self._refresh_authoring_controls()

    def _set_authoring_tool(self, tool: str) -> None:
        if tool not in ("brush", "height", "ridge", "valley", "region"):
            raise ValueError(f"Unknown authoring tool: {tool}")
        if self._draft_points and self._authoring_tool.get() != tool:
            self._draft_points.clear()
            self._active_brush_values = None
            self.status_label.configure(text="Unfinished structure discarded.")
        self._authoring_tool.set(tool)
        self._refresh_authoring_controls()
        self._draw_preview()

    def _selected_elevation_mode(self, tool: str | None = None) -> ElevationMode:
        selected = tool or self._authoring_tool.get()
        value = self._tool_modes[selected].get().lower()
        if value not in ("absolute", "relative"):
            raise ValueError(f"Unknown elevation mode: {value}")
        return value

    def _on_elevation_mode_changed(self, _event: tk.Event[tk.Misc]) -> None:
        self._refresh_authoring_controls()
        self._draw_brush_cursor()

    def _refresh_authoring_controls(self) -> None:
        selected = self._authoring_tool.get()
        colours = {
            "brush": _BRUSH_COLOUR,
            "height": _HEIGHT_COLOUR,
            "ridge": _RIDGE_COLOUR,
            "valley": _VALLEY_COLOUR,
            "region": _REGION_COLOUR,
        }
        for tool, button in self._tool_buttons.items():
            active = tool == selected
            button.configure(
                background=colours[tool] if active else "#2c3e40",
                foreground="#142022" if active else "#d6e0dd",
                activebackground=colours[tool],
                activeforeground="#142022",
                disabledforeground="#71817e",
            )

        line_ready = ((selected in ("ridge", "valley") and len(self._draft_points) >= 2)
                      or (selected == "region" and len(self._draft_points) >= 3))
        self.finish_line_button.configure(
            text="Finish region" if selected == "region" else "Finish line")
        self.finish_line_button.configure(
            state="normal" if self._authoring_enabled and line_ready else "disabled"
        )
        has_authored_work = bool(self._draft_points or self._constraints)
        self.undo_constraint_button.configure(
            state="normal" if self._authoring_enabled and has_authored_work else "disabled"
        )
        self.clear_constraints_button.configure(
            state="normal" if self._authoring_enabled and has_authored_work else "disabled"
        )
        self._region_character_input.configure(
            state="readonly" if self._authoring_enabled else "disabled")
        if selected == "region":
            self._feature_parameters.grid_remove()
            self._region_parameters.grid()
            self.authoring_hint.configure(text=(
                "Click 3+ corners, then Finish region. Regions affect land only."
                if self._authoring_enabled else "Import land geometry to start drawing."
            ))
            return
        self._region_parameters.grid_remove()
        self._feature_parameters.grid()
        elevation_mode = self._selected_elevation_mode(selected)
        self.mode_input.configure(
            textvariable=self._tool_modes[selected],
            state="readonly" if self._authoring_enabled else "disabled",
        )
        signed_relative = elevation_mode == "relative" and selected in ("brush", "height")
        self.value_input.configure(
            from_=-10_000 if signed_relative else 0,
            to=10_000,
            increment=100,
            textvariable=self._tool_elevations[selected],
        )
        value_labels = {
            ("brush", "absolute"): "Target height",
            ("brush", "relative"): "Height offset",
            ("height", "absolute"): "Exact height",
            ("height", "relative"): "Height offset",
            ("ridge", "absolute"): "Minimum crest",
            ("ridge", "relative"): "Ridge relief",
            ("valley", "absolute"): "Outlet floor",
            ("valley", "relative"): "Valley depth",
        }
        self.value_label.configure(text=value_labels[(selected, elevation_mode)])
        if selected == "brush":
            self.width_label.configure(text="Brush width")
            self.width_input.configure(
                from_=10,
                to=4_000,
                increment=20,
                textvariable=self._tool_sizes[selected],
            )
        else:
            self.width_label.configure(
                text="Influence radius" if selected == "height" else "Core radius"
            )
            self.width_input.configure(
                from_=1,
                to=2_000,
                increment=10,
                textvariable=self._tool_sizes[selected],
            )
        self.brush_strength_input.configure(
            state="normal" if self._authoring_enabled and selected == "brush" else "disabled"
        )

        if not self._authoring_enabled:
            hint = "Import land geometry to start drawing."
        elif selected == "brush":
            action = (
                "toward an absolute height"
                if elevation_mode == "absolute"
                else "a signed height offset onto the existing terrain"
            )
            hint = f"Drag to paint {action}. Wheel: width; Ctrl+wheel: strength."
        elif selected == "height":
            action = "an exact height" if elevation_mode == "absolute" else "a local height offset"
            hint = f"Click to place {action}; its smooth response extends past the core."
        else:
            feature = "ridge" if selected == "ridge" else "valley"
            behavior = (
                "uses an absolute crest or floor"
                if elevation_mode == "absolute"
                else "adds relief or incision relative to the terrain beneath it"
            )
            direction = " Draw from head toward outlet." if selected == "valley" else ""
            hint = (
                f"Click along the {feature}; Finish line or right-click at 2+ points. "
                f"It {behavior}.{direction}"
            )
        count = len(self._constraints)
        if count:
            hint = f"{count} authored feature{'s' if count != 1 else ''}.  {hint}"
        self.authoring_hint.configure(text=hint)

    def _map_rect(self) -> tuple[float, float, float, float] | None:
        if self._coastline is None:
            return None
        min_x, min_y, max_x, max_y = self._coastline.bounds
        span_x = max_x - min_x
        span_y = max_y - min_y
        if span_x <= 0 or span_y <= 0:
            return None
        canvas_width = max(1.0, float(self.preview.winfo_width()))
        canvas_height = max(1.0, float(self.preview.winfo_height()))
        scale = min(max(1.0, canvas_width - 36.0) / span_x, max(1.0, canvas_height - 36.0) / span_y)
        display_width = span_x * scale
        display_height = span_y * scale
        left = (canvas_width - display_width) / 2.0
        top = (canvas_height - display_height) / 2.0
        return left, top, left + display_width, top + display_height

    def _normalized_to_source(self, position: tuple[float, float]) -> tuple[float, float]:
        if self._coastline is None:
            raise RuntimeError("No coastline is loaded.")
        min_x, min_y, max_x, max_y = self._coastline.bounds
        return (
            min_x + position[0] * (max_x - min_x),
            min_y + position[1] * (max_y - min_y),
        )

    def _normalized_to_canvas(self, position: tuple[float, float]) -> tuple[float, float]:
        rect = self._map_rect()
        if rect is None:
            raise RuntimeError("No coastline is loaded.")
        left, top, right, bottom = rect
        return (
            left + position[0] * (right - left),
            top + position[1] * (bottom - top),
        )

    def _canvas_to_normalized(self, x: float, y: float) -> tuple[float, float] | None:
        rect = self._map_rect()
        if rect is None:
            return None
        left, top, right, bottom = rect
        if not left <= x <= right or not top <= y <= bottom:
            return None
        return (x - left) / (right - left), (y - top) / (bottom - top)

    def _read_constraint_values(self) -> tuple[float, float, ElevationMode] | None:
        tool = self._authoring_tool.get()
        try:
            elevation_m = float(self._tool_elevations[tool].get())
            radius_km = float(self._tool_sizes[tool].get())
            elevation_mode = self._selected_elevation_mode(tool)
            if elevation_mode == "absolute" and elevation_m < 0:
                raise ValueError("Absolute height must be at or above sea level.")
            if elevation_mode == "relative" and tool in ("ridge", "valley") and elevation_m < 0:
                raise ValueError("Ridge relief and valley depth must not be negative.")
            if radius_km <= 0:
                raise ValueError("Influence must be greater than zero.")
        except (tk.TclError, ValueError) as error:
            messagebox.showerror("Invalid authored feature", str(error), parent=self.root)
            return None
        return elevation_m, radius_km, elevation_mode

    def _read_brush_values(self) -> tuple[float, float, float, ElevationMode] | None:
        try:
            elevation_m = float(self._tool_elevations["brush"].get())
            width_km = float(self._tool_sizes["brush"].get())
            intensity = float(self._brush_intensity_percent.get()) / 100.0
            elevation_mode = self._selected_elevation_mode("brush")
            if elevation_mode == "absolute" and elevation_m < 0:
                raise ValueError("Target height must be at or above sea level.")
            if width_km <= 0:
                raise ValueError("Brush width must be greater than zero.")
            if not 0.0 < intensity <= 1.0:
                raise ValueError("Brush strength must be greater than 0% and at most 100%.")
        except (tk.TclError, ValueError) as error:
            messagebox.showerror("Invalid terrain brush", str(error), parent=self.root)
            return None
        return elevation_m, width_km / 2.0, intensity, elevation_mode

    def _brush_map_position(self, x: float, y: float) -> tuple[float, float] | None:
        if self._coast_polygon is None:
            return None
        position = self._canvas_to_normalized(x, y)
        if position is None:
            return None
        if not self._coast_polygon.covers(Point(self._normalized_to_source(position))):
            return None
        return position

    def _on_map_press(self, event: tk.Event[tk.Misc]) -> None:
        if self._authoring_tool.get() != "brush":
            self._on_map_click(event)
            return
        if not self._authoring_enabled:
            return
        position = self._brush_map_position(float(event.x), float(event.y))
        if position is None:
            self.root.bell()
            self.status_label.configure(text="Paint on a land component.")
            return
        values = self._read_brush_values()
        if values is None:
            return
        self._active_brush_values = values
        self._draft_points[:] = [position]
        self._brush_cursor = position
        self.status_label.configure(text="Painting terrain guidance…")
        self._refresh_authoring_controls()
        self._draw_brush_draft()
        self._draw_brush_cursor()

    def _on_map_drag(self, event: tk.Event[tk.Misc]) -> None:
        if self._authoring_tool.get() != "brush" or self._active_brush_values is None:
            return
        position = self._brush_map_position(float(event.x), float(event.y))
        if position is None:
            self._brush_cursor = None
            self._draw_brush_cursor()
            return
        self._brush_cursor = position
        if not self._draft_points:
            self._draft_points.append(position)
        else:
            previous = self._draft_points[-1]
            segment = LineString(
                [self._normalized_to_source(previous), self._normalized_to_source(position)]
            )
            if self._coast_polygon is None or not self._coast_polygon.covers(segment):
                self.status_label.configure(text="The brush centre cannot cross open water.")
                self._draw_brush_cursor()
                return
            previous_canvas = self._normalized_to_canvas(previous)
            radius_km = self._active_brush_values[1]
            spacing = max(2.0, min(16.0, self._influence_radius_pixels(radius_km) * 0.12))
            moved = hypot(
                float(event.x) - previous_canvas[0],
                float(event.y) - previous_canvas[1],
            )
            if moved >= spacing:
                self._draft_points.append(position)
        self._draw_brush_draft()
        self._draw_brush_cursor()

    def _on_map_release(self, _event: tk.Event[tk.Misc]) -> None:
        if self._authoring_tool.get() != "brush" or self._active_brush_values is None:
            return
        elevation_m, radius_km, intensity, elevation_mode = self._active_brush_values
        points = tuple(self._draft_points)
        self._active_brush_values = None
        self._draft_points.clear()
        if not points:
            self._refresh_authoring_controls()
            return
        self._constraints.append(
            TerrainBrushStroke(
                points=points,
                elevation_m=elevation_m,
                influence_radius_km=radius_km,
                intensity=intensity,
                elevation_mode=elevation_mode,
            )
        )
        self._invalidate_generated_terrain("Terrain brush stroke added. Generate to apply it.")

    def _on_map_motion(self, event: tk.Event[tk.Misc]) -> None:
        if self._authoring_tool.get() != "brush" or not self._authoring_enabled:
            return
        self._brush_cursor = self._brush_map_position(float(event.x), float(event.y))
        self._draw_brush_cursor()

    def _on_map_leave(self, _event: tk.Event[tk.Misc]) -> None:
        self._brush_cursor = None
        self._draw_brush_cursor()

    def _on_map_wheel(self, event: tk.Event[tk.Misc]) -> str | None:
        if self._authoring_tool.get() != "brush" or not self._authoring_enabled:
            return None
        delta = int(event.delta)
        if delta == 0:
            return "break"
        steps = int(delta / 120) if abs(delta) >= 120 else (1 if delta > 0 else -1)
        if int(event.state) & 0x0004:
            current = float(self._brush_intensity_percent.get())
            self._brush_intensity_percent.set(min(100.0, max(5.0, current + 5.0 * steps)))
        else:
            current = float(self._tool_sizes["brush"].get())
            increment = max(10.0, round(current * 0.08 / 10.0) * 10.0)
            self._tool_sizes["brush"].set(
                min(4_000.0, max(10.0, current + increment * steps))
            )
        self._brush_cursor = self._brush_map_position(float(event.x), float(event.y))
        self._refresh_authoring_controls()
        self._draw_brush_cursor()
        return "break"

    def _on_map_click(self, event: tk.Event[tk.Misc]) -> None:
        if not self._authoring_enabled or self._coast_polygon is None:
            return
        position = self._canvas_to_normalized(float(event.x), float(event.y))
        if position is None:
            return
        source_point = self._normalized_to_source(position)
        if (self._authoring_tool.get() != "region"
                and not self._coast_polygon.covers(Point(source_point))):
            self.root.bell()
            self.status_label.configure(text="Place authored features on a land component.")
            return

        tool = self._authoring_tool.get()
        if tool == "height":
            values = self._read_constraint_values()
            if values is None:
                return
            elevation_m, radius_km, elevation_mode = values
            self._constraints.append(
                ElevationPoint(
                    position=position,
                    elevation_m=elevation_m,
                    influence_radius_km=radius_km,
                    elevation_mode=elevation_mode,
                )
            )
            self._invalidate_generated_terrain("Height point added. Generate to apply it.")
        else:
            if self._draft_points:
                segment = LineString(
                    [
                        self._normalized_to_source(self._draft_points[-1]),
                        source_point,
                    ]
                )
                if tool != "region" and not self._coast_polygon.covers(segment):
                    self.root.bell()
                    self.status_label.configure(
                        text="That segment leaves the coastline; choose a different point."
                    )
                    return
            self._draft_points.append(position)
            self.status_label.configure(
                text=f"{tool.capitalize()} vertex {len(self._draft_points)} added."
            )
            self._refresh_authoring_controls()
            self._draw_preview()

    def _finish_structure(self) -> None:
        tool = self._authoring_tool.get()
        if tool == "region":
            self._finish_region()
            return
        if tool not in ("ridge", "valley") or len(self._draft_points) < 2:
            return
        values = self._read_constraint_values()
        if values is None:
            return
        elevation_m, radius_km, elevation_mode = values
        self._constraints.append(
            TerrainStructure(
                kind=tool,
                points=tuple(self._draft_points),
                elevation_m=elevation_m,
                influence_radius_km=radius_km,
                elevation_mode=elevation_mode,
            )
        )
        self._draft_points.clear()
        self._invalidate_generated_terrain(f"{tool.capitalize()} added. Generate to apply it.")

    def _read_region_settings(self) -> LandformSettings:
        character = self._region_character.get()
        if character not in ("plain", "hills", "plateau", "mountains"):
            raise ValueError("Unknown landform character.")
        return LandformSettings(
            character=character,
            **{key: float(value.get()) for key, value in self._region_values.items()},
        )

    def _on_region_character(self, _event: tk.Event[tk.Misc]) -> None:
        character = self._region_character.get()
        if character not in ("plain", "hills", "plateau", "mountains"):
            return
        preset = landform_preset(character)
        for key, value in self._region_values.items():
            value.set(float(getattr(preset, key)))

    def _finish_region(self) -> None:
        if len(self._draft_points) < 3:
            return
        points = tuple(self._draft_points)
        if points[0] != points[-1]:
            points += (points[0],)
        try:
            region = TerrainRegion(points, self._read_region_settings())
            geometry = Polygon([self._normalized_to_source(point) for point in points])
            if not geometry.is_valid or geometry.area <= 0:
                raise ValueError("Use a simple polygon without crossing edges.")
            if self._coast_polygon is None or geometry.intersection(self._coast_polygon).area <= 0:
                raise ValueError("The region must cover some land.")
            if region.settings.elevation_m > float(self._variables["maximum_elevation_m"].get()):
                raise ValueError("Regional base height exceeds the elevation ceiling.")
        except (ValueError, tk.TclError) as error:
            messagebox.showerror("Invalid landform region", str(error), parent=self.root)
            return
        self._constraints.append(region)
        self._draft_points.clear()
        self._invalidate_generated_terrain("Landform region added. Generate to apply it.")

    def _undo_constraint(self) -> None:
        if self._draft_points:
            self._draft_points.pop()
            self.status_label.configure(text="Removed the last unfinished line vertex.")
            self._refresh_authoring_controls()
            self._draw_preview()
            return
        if self._constraints:
            self._constraints.pop()
            self._invalidate_generated_terrain("Removed the last authored feature.")

    def _clear_constraints(self) -> None:
        if not self._draft_points and not self._constraints:
            return
        if self._constraints and not messagebox.askyesno(
            "Clear authored topography?",
            "Remove every terrain brush stroke, height point, ridge, and valley "
            "and landform regions from this coastline?",
            parent=self.root,
        ):
            return
        self._draft_points.clear()
        self._active_brush_values = None
        self._constraints.clear()
        self._invalidate_generated_terrain("All authored topography cleared.")

    def _invalidate_generated_terrain(self, status: str) -> None:
        self._terrain = None
        self._image = None
        self._preview_photo = None
        self.export_button.configure(state="disabled")
        self.progress.configure(value=0)
        self.status_label.configure(text=status)
        suffix = "s" if len(self._constraints) != 1 else ""
        self.preview_meta.configure(text=f"{len(self._constraints)} authored feature{suffix}")
        self._refresh_authoring_controls()
        self._draw_preview()

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
            title="Import SVG land geometry",
            filetypes=(("SVG vector", "*.svg"), ("All files", "*.*")),
        )
        if not selected:
            return
        if (self._constraints or self._draft_points) and not messagebox.askyesno(
            "Replace the coastline?",
            "Importing different land geometry clears the authored terrain brush strokes, "
            "height points, ridges, and valleys.",
            parent=self.root,
        ):
            return
        source = Path(selected)
        self.import_button.configure(state="disabled")
        self.open_project_button.configure(state="disabled")
        self.save_project_button.configure(state="disabled")
        self.generate_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        self._set_authoring_enabled(False)
        self.source_label.configure(text=f"Reading {source.name}…")
        self.status_label.configure(text="Validating coastline in the background…")
        self.progress.configure(mode="indeterminate", value=0)
        self.progress.start(12)

        def worker() -> None:
            try:
                self._events.put(_CoastlineEvent(load_svg_coastline_source(source)))
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

    def _choose_project(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self.root,
            title="Open terrain project",
            filetypes=(
                ("DM Tools terrain project", f"*{PROJECT_EXTENSION}"),
                ("JSON document", "*.json"),
                ("All files", "*.*"),
            ),
        )
        if not selected:
            return
        if (self._constraints or self._draft_points) and not messagebox.askyesno(
            "Replace the current project?",
            "Opening a project replaces the current coastline, settings, and authored terrain.",
            parent=self.root,
        ):
            return

        source = Path(selected)
        self.import_button.configure(state="disabled")
        self.open_project_button.configure(state="disabled")
        self.save_project_button.configure(state="disabled")
        self.generate_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        self._set_authoring_enabled(False)
        self.source_label.configure(text=f"Reading {source.name}…")
        self.status_label.configure(text="Validating project and coastline…")
        self.progress.configure(mode="indeterminate", value=0)
        self.progress.start(12)

        def worker() -> None:
            try:
                self._events.put(_ProjectEvent(load_terrain_project(source)))
            except TerrainProjectInputError as error:
                self._events.put(
                    _ErrorEvent(
                        title="Terrain project could not be opened",
                        status="Project open failed.",
                        error=error,
                    )
                )
            except Exception as error:
                self._events.put(
                    _ErrorEvent(
                        title="Unexpected project failure",
                        status="Project open failed.",
                        error=error,
                    )
                )

        threading.Thread(target=worker, name="terrain-project-loader", daemon=True).start()

    def _save_project(self) -> None:
        if self._coastline is None or self._coastline_source is None:
            messagebox.showinfo(
                "Import land geometry",
                "Import closed SVG land shapes before saving a terrain project.",
                parent=self.root,
            )
            return
        if self._draft_points:
            messagebox.showinfo(
                "Finish the current feature",
                "Finish or undo the current stroke or line before saving.",
                parent=self.root,
            )
            return
        try:
            project = TerrainProject(
                coastline=self._coastline,
                settings=self._read_settings(),
                constraints=tuple(self._constraints),
                authoring=self._read_authoring_state(),
            )
        except (ValueError, tk.TclError) as error:
            messagebox.showerror("Invalid project settings", str(error), parent=self.root)
            return

        initial_file = (
            self._project_path.name
            if self._project_path is not None
            else f"{Path(self._coastline.source_name).stem}{PROJECT_EXTENSION}"
        )
        selected = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save terrain project",
            initialfile=initial_file,
            defaultextension=PROJECT_EXTENSION,
            filetypes=(("DM Tools terrain project", f"*{PROJECT_EXTENSION}"),),
        )
        if not selected:
            return
        destination = Path(selected)
        coastline_source = self._coastline_source

        self.import_button.configure(state="disabled")
        self.open_project_button.configure(state="disabled")
        self.save_project_button.configure(state="disabled")
        self.generate_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        self._set_authoring_enabled(False)
        self.status_label.configure(text="Saving authored terrain project…")
        self.progress.configure(mode="indeterminate", value=0)
        self.progress.start(12)

        def worker() -> None:
            try:
                save_terrain_project(project, coastline_source, destination)
                self._events.put(_ProjectSavedEvent(destination.resolve()))
            except (OSError, TerrainProjectInputError) as error:
                self._events.put(
                    _ErrorEvent(
                        title="Terrain project could not be saved",
                        status="Project save failed.",
                        error=error,
                    )
                )
            except Exception as error:
                self._events.put(
                    _ErrorEvent(
                        title="Unexpected project save failure",
                        status="Project save failed.",
                        error=error,
                    )
                )

        threading.Thread(target=worker, name="terrain-project-saver", daemon=True).start()

    def _accept_coastline(
        self,
        coastline: Coastline,
        source: CoastlineSource | None = None,
    ) -> None:
        self._coastline = coastline
        self._coastline_source = source
        self._project_path = None
        land_geometry = unary_union(
            [
                Polygon(component.exterior, holes=component.holes)
                for component in coastline.components
            ]
        )
        if not isinstance(land_geometry, (Polygon, MultiPolygon)):
            raise ValueError("The imported coastlines do not form polygonal land geometry.")
        self._coast_polygon = land_geometry
        self._constraints.clear()
        self._draft_points.clear()
        self._active_brush_values = None
        self._brush_cursor = None
        self._terrain = None
        self._image = None
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)
        self.import_button.configure(state="normal")
        self.open_project_button.configure(state="normal")
        self.save_project_button.configure(state="normal" if source is not None else "disabled")
        self.generate_button.configure(state="normal")
        self.export_button.configure(state="disabled")
        self._set_authoring_enabled(True)
        self.source_label.configure(text=coastline.source_name)
        self.status_label.configure(
            text="Land geometry valid. Draw controls or generate directly."
        )
        component_label = "component" if coastline.component_count == 1 else "components"
        self.preview_meta.configure(
            text=(
                f"{coastline.boundary_point_count:,} sampled boundary points · "
                f"{coastline.component_count} land {component_label}"
            )
        )
        self._refresh_authoring_controls()
        self._draw_preview()

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

    def _apply_settings(self, settings: TerrainSettings) -> None:
        for key, variable in self._variables.items():
            variable.set(float(getattr(settings, key)))
            self._refresh_value(key)

    def _read_authoring_state(self) -> TerrainAuthoringState:
        active_tool = self._authoring_tool.get()
        if active_tool not in ("brush", "height", "ridge", "valley", "region"):
            raise ValueError(f"Unknown authoring tool: {active_tool}")

        def feature(tool: str) -> FeatureToolSettings:
            return FeatureToolSettings(
                elevation_mode=self._selected_elevation_mode(tool),
                elevation_m=float(self._tool_elevations[tool].get()),
                radius_km=float(self._tool_sizes[tool].get()),
            )

        return TerrainAuthoringState(
            active_tool=active_tool,
            region=self._read_region_settings(),
            brush=BrushToolSettings(
                elevation_mode=self._selected_elevation_mode("brush"),
                elevation_m=float(self._tool_elevations["brush"].get()),
                width_km=float(self._tool_sizes["brush"].get()),
                intensity=float(self._brush_intensity_percent.get()) / 100.0,
            ),
            height=feature("height"),
            ridge=feature("ridge"),
            valley=feature("valley"),
        )

    def _apply_authoring_state(self, authoring: TerrainAuthoringState) -> None:
        self._authoring_tool.set(authoring.active_tool)
        self._region_character.set(authoring.region.character)
        for key, value in self._region_values.items():
            value.set(float(getattr(authoring.region, key)))
        self._tool_modes["brush"].set(authoring.brush.elevation_mode.title())
        self._tool_elevations["brush"].set(authoring.brush.elevation_m)
        self._tool_sizes["brush"].set(authoring.brush.width_km)
        self._brush_intensity_percent.set(authoring.brush.intensity * 100.0)
        for tool, settings in (
            ("height", authoring.height),
            ("ridge", authoring.ridge),
            ("valley", authoring.valley),
        ):
            self._tool_modes[tool].set(settings.elevation_mode.title())
            self._tool_elevations[tool].set(settings.elevation_m)
            self._tool_sizes[tool].set(settings.radius_km)
        self._refresh_authoring_controls()

    def _accept_project(self, loaded: LoadedTerrainProject) -> None:
        project = loaded.project
        self._accept_coastline(project.coastline, loaded.coastline_source)
        self._project_path = loaded.path
        self._apply_settings(project.settings)
        self._constraints[:] = project.constraints
        self._apply_authoring_state(project.authoring)
        count = len(self._constraints)
        suffix = "s" if count != 1 else ""
        self.status_label.configure(
            text=f"Opened {loaded.path.name} with {count} authored feature{suffix}."
        )
        self.preview_meta.configure(text=f"{count} authored feature{suffix}")
        self._draw_preview()

    def _generate(self) -> None:
        if self._coastline is None:
            messagebox.showinfo(
                "Import land geometry",
                "Choose one or more closed SVG land objects first.",
                parent=self.root,
            )
            return
        try:
            settings = self._read_settings()
        except (ValueError, tk.TclError) as error:
            messagebox.showerror("Invalid settings", str(error), parent=self.root)
            return

        self.generate_button.configure(state="disabled")
        self.import_button.configure(state="disabled")
        self.open_project_button.configure(state="disabled")
        self.save_project_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        self.render_style_input.configure(state="disabled")
        self._set_authoring_enabled(False)
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)
        self.status_label.configure(text="Starting deterministic generation…")
        coastline = self._coastline
        constraints = tuple(self._constraints)
        render_style = self._selected_render_style()

        def worker() -> None:
            try:
                terrain = generate_terrain(
                    coastline,
                    settings,
                    lambda fraction, message: self._events.put(_ProgressEvent(fraction, message)),
                    constraints=constraints,
                )
                self._events.put(_ProgressEvent(0.97, "Rendering colour relief"))
                image = render_height_map(terrain, style=render_style)
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
                    self._accept_coastline(event.source.coastline, event.source)
                elif isinstance(event, _ProjectEvent):
                    self._accept_project(event.loaded)
                elif isinstance(event, _ProjectSavedEvent):
                    self._project_path = event.path
                    self.progress.stop()
                    self.progress.configure(mode="determinate", value=100)
                    self.import_button.configure(state="normal")
                    self.open_project_button.configure(state="normal")
                    self.save_project_button.configure(state="normal")
                    self.generate_button.configure(state="normal")
                    self.export_button.configure(
                        state="normal" if self._terrain is not None else "disabled"
                    )
                    self._set_authoring_enabled(True)
                    self.status_label.configure(text=f"Saved project {event.path.name}")
                elif isinstance(event, _ResultEvent):
                    self._terrain = event.terrain
                    self._image = event.image
                    self.progress.stop()
                    self.progress.configure(mode="determinate")
                    self.progress.configure(value=100)
                    drainage = event.terrain.drainage
                    if drainage.basin_candidate_count:
                        drainage_status = (
                            f"Drainage check grouped "
                            f"{drainage.potential_sink_cell_count:,} potential terminal cells "
                            f"into {drainage.basin_candidate_count:,} basin candidates."
                        )
                    elif drainage.potential_sink_cell_count:
                        drainage_status = (
                            f"Drainage check found {drainage.potential_sink_cell_count:,} "
                            "flat or sub-tolerance terminal cells."
                        )
                    else:
                        drainage_status = "No potential sinks on the canonical grid."
                    agreement = event.terrain.routing_agreement
                    conflicts = event.terrain.routing_conflicts.summary
                    self.status_label.configure(text=(
                        f"Terrain ready. {drainage_status} "
                        f"Planned channels: {agreement.uphill_channel_edge_count:,} uphill edges; "
                        f"{conflicts.insufficient_cut_edge_count:,} exceed cut allowance, "
                        f"{conflicts.depression_edge_count:,} touch depressions (may overlap)."
                    ))
                    peak = float(event.terrain.elevation_m[event.terrain.land_mask].max())
                    connected_percent = (
                        100.0
                        * drainage.directly_connected_land_cell_count
                        / drainage.land_cell_count
                    )
                    self.preview_meta.configure(
                        text=(
                            f"{event.terrain.width} x {event.terrain.height} px"
                            f"  ·  peak {peak:,.0f} m"
                            f"  ·  direct drainage {connected_percent:.1f}%"
                            f"  ·  {drainage.basin_candidate_count:,} basin candidates"
                        )
                    )
                    self.import_button.configure(state="normal")
                    self.open_project_button.configure(state="normal")
                    self.save_project_button.configure(
                        state="normal" if self._coastline_source is not None else "disabled"
                    )
                    self.generate_button.configure(state="normal")
                    self.export_button.configure(state="normal")
                    self.render_style_input.configure(state="readonly")
                    self._set_authoring_enabled(True)
                    self._draw_preview()
                else:
                    self.progress.stop()
                    self.progress.configure(mode="determinate", value=0)
                    self.import_button.configure(state="normal")
                    self.open_project_button.configure(state="normal")
                    self.save_project_button.configure(
                        state="normal" if self._coastline_source is not None else "disabled"
                    )
                    self._set_authoring_enabled(self._coastline is not None)
                    self.generate_button.configure(
                        state="normal" if self._coastline is not None else "disabled"
                    )
                    self.export_button.configure(
                        state="normal" if self._terrain is not None else "disabled"
                    )
                    self.render_style_input.configure(state="readonly")
                    source_name = (
                        self._coastline.source_name
                        if self._coastline is not None
                        else "No land geometry loaded"
                    )
                    self.source_label.configure(text=source_name)
                    self.status_label.configure(text=event.status)
                    messagebox.showerror(event.title, str(event.error), parent=self.root)
        except queue.Empty:
            pass
        self.root.after(80, self._poll_events)

    def _draw_preview(self) -> None:
        self.preview.delete("all")
        if self._coastline is None:
            self.preview.create_text(
                20,
                20,
                text="Import SVG land shapes\nto establish the land mask.",
                anchor="nw",
                fill="#71817e",
                font=("Segoe UI", 14),
            )
            return
        rect = self._map_rect()
        if rect is None:
            return
        left, top, right, bottom = rect
        display_width = max(1, round(right - left))
        display_height = max(1, round(bottom - top))

        if self._image is not None:
            display = self._image.resize(
                (display_width, display_height),
                Image.Resampling.LANCZOS,
            )
            self._preview_photo = ImageTk.PhotoImage(display)
            self.preview.create_image(left, top, image=self._preview_photo, anchor="nw")
        else:
            for exterior, holes in self._coastline_canvas_coordinates():
                self.preview.create_polygon(
                    exterior,
                    fill="#243638",
                    outline="",
                )
                for hole in holes:
                    self.preview.create_polygon(
                        hole,
                        fill=_MAP_BACKGROUND,
                        outline="",
                    )

        for exterior, holes in self._coastline_canvas_coordinates():
            for boundary_coordinates in (exterior, *holes):
                self.preview.create_line(
                    boundary_coordinates,
                    fill="#b9cbc6",
                    width=1.5,
                    joinstyle="round",
                )
        if self._terrain is not None and self._show_drainage.get():
            with render_drainage_overlay(self._terrain, (display_width, display_height)) as overlay:
                self._drainage_photo = ImageTk.PhotoImage(overlay)
            self.preview.create_image(left, top, image=self._drainage_photo, anchor="nw")
            self.preview.create_text(
                left + 8, top + 8, anchor="nw", fill="white",
                text="Blue: planned channels. Red: uphill. Coarse-grid review only.",
            )
        self._draw_drainage_candidates()
        for constraint in self._constraints:
            self._draw_constraint(constraint)
        self._draw_draft_structure()
        self._draw_brush_cursor()

    def _draw_drainage_candidates(self) -> None:
        """Overlay the most significant derived basins without altering the image."""

        if self._terrain is None:
            return
        candidates = self._terrain.drainage.basin_candidates
        for rank, candidate in enumerate(candidates[:20], start=1):
            x, y = self._normalized_to_canvas(
                (candidate.normalized_x, candidate.normalized_y)
            )
            radius = min(12.0, 4.0 + 0.012 * candidate.maximum_fill_depth_m)
            self.preview.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                outline="#d889ff",
                width=2,
                dash=(3, 2),
            )
            self.preview.create_line(
                x - 3,
                y,
                x + 3,
                y,
                fill="#f1c6ff",
                width=1,
            )
            self.preview.create_line(
                x,
                y - 3,
                x,
                y + 3,
                fill="#f1c6ff",
                width=1,
            )
            if rank <= 8:
                self.preview.create_text(
                    x + radius + 3,
                    y - radius,
                    text=f"basin {rank}  {candidate.maximum_fill_depth_m:,.0f} m fill",
                    anchor="sw",
                    fill="#f1c6ff",
                    font=("Consolas", 8, "bold"),
                )

    def _coastline_canvas_coordinates(
        self,
    ) -> list[tuple[list[float], tuple[list[float], ...]]]:
        if self._coastline is None:
            return []
        min_x, min_y, max_x, max_y = self._coastline.bounds
        span_x = max_x - min_x
        span_y = max_y - min_y
        def canvas_ring(points: tuple[tuple[float, float], ...]) -> list[float]:
            step = max(1, (len(points) - 1) // 1_200)
            sampled = list(points[:-1:step])
            sampled.append(points[-1])
            coordinates: list[float] = []
            for x, y in sampled:
                canvas_x, canvas_y = self._normalized_to_canvas(
                    ((x - min_x) / span_x, (y - min_y) / span_y)
                )
                coordinates.extend((canvas_x, canvas_y))
            return coordinates

        return [
            (
                canvas_ring(component.exterior),
                tuple(canvas_ring(hole) for hole in component.holes),
            )
            for component in self._coastline.components
        ]

    def _influence_radius_pixels(self, influence_radius_km: float) -> float:
        rect = self._map_rect()
        if rect is None:
            return 0.0
        try:
            object_scale_km = float(self._variables["object_scale_km"].get())
        except (tk.TclError, ValueError):
            return 0.0
        if object_scale_km <= 0:
            return 0.0
        left, top, right, bottom = rect
        return influence_radius_km / object_scale_km * max(right - left, bottom - top)

    def _draw_constraint(self, constraint: TerrainConstraint) -> None:
        if isinstance(constraint, TerrainRegion):
            coordinates = [value for point in constraint.points
                           for value in self._normalized_to_canvas(point)]
            self.preview.create_polygon(coordinates, fill="", outline=_REGION_COLOUR,
                                        width=2, dash=(6, 3))
            self.preview.create_text(coordinates[0] + 6, coordinates[1] - 6,
                                     text=constraint.settings.character, anchor="sw",
                                     fill=_REGION_COLOUR)
            return
        if isinstance(constraint, TerrainBrushStroke):
            canvas_points = [self._normalized_to_canvas(point) for point in constraint.points]
            radius = max(2.0, self._influence_radius_pixels(constraint.influence_radius_km))
            if len(canvas_points) == 1:
                x, y = canvas_points[0]
                self.preview.create_oval(
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                    fill=_BRUSH_COLOUR,
                    outline="#d7e7bd",
                    width=1,
                    stipple="gray50",
                )
                label_x, label_y = x, y
            else:
                coordinates = [value for point in canvas_points for value in point]
                self.preview.create_line(
                    coordinates,
                    fill=_BRUSH_COLOUR,
                    width=max(3.0, 2.0 * radius),
                    capstyle="round",
                    joinstyle="round",
                    smooth=True,
                    splinesteps=12,
                    stipple="gray50",
                )
                self.preview.create_line(
                    coordinates,
                    fill="#d7e7bd",
                    width=2,
                    capstyle="round",
                    joinstyle="round",
                    smooth=True,
                    splinesteps=12,
                )
                label_x, label_y = canvas_points[len(canvas_points) // 2]
            self.preview.create_text(
                label_x + 7,
                label_y - 6,
                text=(
                    "brush  "
                    + (
                        f"{constraint.elevation_m:+,.0f} m relative"
                        if constraint.elevation_mode == "relative"
                        else f"{constraint.elevation_m:,.0f} m absolute"
                    )
                    + f"  {2.0 * constraint.influence_radius_km:,.0f} km  "
                    + f"{constraint.intensity:.0%}"
                ),
                anchor="sw",
                fill="#d7e7bd",
                font=("Consolas", 8, "bold"),
            )
            return

        if isinstance(constraint, ElevationPoint):
            x, y = self._normalized_to_canvas(constraint.position)
            radius = max(4.0, self._influence_radius_pixels(constraint.influence_radius_km))
            self.preview.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                outline=_HEIGHT_COLOUR,
                dash=(3, 3),
            )
            self.preview.create_oval(
                x - 4,
                y - 4,
                x + 4,
                y + 4,
                fill=_HEIGHT_COLOUR,
                outline=_MAP_BACKGROUND,
                width=1,
            )
            self.preview.create_text(
                x + 8,
                y - 7,
                text=(
                    f"{constraint.elevation_m:+,.0f} m relative"
                    if constraint.elevation_mode == "relative"
                    else f"{constraint.elevation_m:,.0f} m absolute"
                ),
                anchor="sw",
                fill="#fff3bf",
                font=("Consolas", 8, "bold"),
            )
            return

        colour = _RIDGE_COLOUR if constraint.kind == "ridge" else _VALLEY_COLOUR
        coordinates: list[float] = []
        canvas_points: list[tuple[float, float]] = []
        for point in constraint.points:
            canvas_point = self._normalized_to_canvas(point)
            canvas_points.append(canvas_point)
            coordinates.extend(canvas_point)
        if constraint.kind == "valley":
            self.preview.create_line(
                coordinates,
                fill=colour,
                width=3,
                joinstyle="round",
                capstyle="round",
                smooth=True,
                splinesteps=16,
                arrow=tk.LAST,
                arrowshape=(9, 11, 4),
            )
        else:
            self.preview.create_line(
                coordinates,
                fill=colour,
                width=3,
                joinstyle="round",
                capstyle="round",
                smooth=True,
                splinesteps=16,
            )
        for x, y in canvas_points:
            self.preview.create_oval(x - 3, y - 3, x + 3, y + 3, fill=colour, outline="")
        label_x, label_y = canvas_points[len(canvas_points) // 2]
        self.preview.create_text(
            label_x + 7,
            label_y - 6,
            text=(
                f"{constraint.kind}  "
                + (
                    f"{'relief' if constraint.kind == 'ridge' else 'depth'} "
                    f"{constraint.elevation_m:,.0f} m"
                    if constraint.elevation_mode == "relative"
                    else (
                        f"outlet floor {constraint.elevation_m:,.0f} m"
                        if constraint.kind == "valley"
                        else f"{constraint.elevation_m:,.0f} m absolute"
                    )
                )
            ),
            anchor="sw",
            fill=colour,
            font=("Consolas", 8, "bold"),
        )

    def _draw_draft_structure(self) -> None:
        if self._authoring_tool.get() == "brush":
            self._draw_brush_draft()
            return
        if not self._draft_points:
            return
        tool = self._authoring_tool.get()
        colour = {"ridge": _RIDGE_COLOUR, "valley": _VALLEY_COLOUR,
                  "region": _REGION_COLOUR}.get(tool, _REGION_COLOUR)
        coordinates: list[float] = []
        canvas_points: list[tuple[float, float]] = []
        for point in self._draft_points:
            canvas_point = self._normalized_to_canvas(point)
            canvas_points.append(canvas_point)
            coordinates.extend(canvas_point)
        if len(canvas_points) >= 2:
            if tool == "region":
                self.preview.create_line(coordinates, fill=colour, width=2, dash=(6, 4))
                if len(canvas_points) >= 3:
                    self.preview.create_line(*canvas_points[-1], *canvas_points[0],
                                             fill=colour, width=1, dash=(2, 4))
            elif tool == "valley":
                self.preview.create_line(
                    coordinates,
                    fill=colour,
                    width=2,
                    dash=(6, 4),
                    joinstyle="round",
                    smooth=True,
                    splinesteps=16,
                    arrow=tk.LAST,
                    arrowshape=(9, 11, 4),
                )
            else:
                self.preview.create_line(
                    coordinates,
                    fill=colour,
                    width=2,
                    dash=(6, 4),
                    joinstyle="round",
                    smooth=True,
                    splinesteps=16,
                )
        for x, y in canvas_points:
            self.preview.create_oval(
                x - 4,
                y - 4,
                x + 4,
                y + 4,
                fill=_MAP_BACKGROUND,
                outline=colour,
                width=2,
            )

    def _draw_brush_draft(self) -> None:
        self.preview.delete("brush-draft")
        if self._authoring_tool.get() != "brush" or not self._draft_points:
            return
        canvas_points = [self._normalized_to_canvas(point) for point in self._draft_points]
        radius_km = (
            self._active_brush_values[1]
            if self._active_brush_values is not None
            else float(self._tool_sizes["brush"].get()) / 2.0
        )
        radius = max(2.0, self._influence_radius_pixels(radius_km))
        if len(canvas_points) == 1:
            x, y = canvas_points[0]
            self.preview.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                fill=_BRUSH_COLOUR,
                outline="#e2efca",
                stipple="gray50",
                tags=("brush-draft",),
            )
            return
        coordinates = [value for point in canvas_points for value in point]
        self.preview.create_line(
            coordinates,
            fill=_BRUSH_COLOUR,
            width=max(3.0, 2.0 * radius),
            capstyle="round",
            joinstyle="round",
            smooth=True,
            splinesteps=12,
            stipple="gray50",
            tags=("brush-draft",),
        )
        self.preview.create_line(
            coordinates,
            fill="#e2efca",
            width=2,
            capstyle="round",
            joinstyle="round",
            smooth=True,
            splinesteps=12,
            tags=("brush-draft",),
        )

    def _draw_brush_cursor(self) -> None:
        self.preview.delete("brush-cursor")
        if (
            self._authoring_tool.get() != "brush"
            or not self._authoring_enabled
            or self._brush_cursor is None
        ):
            return
        x, y = self._normalized_to_canvas(self._brush_cursor)
        width_km = float(self._tool_sizes["brush"].get())
        radius = max(3.0, self._influence_radius_pixels(width_km / 2.0))
        strength = float(self._brush_intensity_percent.get())
        self.preview.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            outline="#e2efca",
            width=2,
            dash=(4, 3),
            tags=("brush-cursor",),
        )
        self.preview.create_oval(
            x - 2,
            y - 2,
            x + 2,
            y + 2,
            fill="#e2efca",
            outline="",
            tags=("brush-cursor",),
        )
        self.preview.create_text(
            x + radius + 7,
            y,
            text=f"{width_km:,.0f} km  {strength:.0f}%",
            anchor="w",
            fill="#e2efca",
            font=("Consolas", 8, "bold"),
            tags=("brush-cursor",),
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
