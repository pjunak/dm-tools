"""Dependency-light terrain concepts and validation rules."""

from dmtools.terrain.domain.coordinates import EndpointGrid, LocalMetricFrame
from dmtools.terrain.domain.models import (
    Coastline,
    ElevationMode,
    ElevationPoint,
    LandComponent,
    LandformKind,
    LandformSettings,
    TerrainBrushStroke,
    TerrainConstraint,
    TerrainRegion,
    TerrainSettings,
    TerrainStructure,
    landform_preset,
)
from dmtools.terrain.domain.project import (
    AuthoringTool,
    BrushToolSettings,
    FeatureToolSettings,
    TerrainAuthoringState,
    TerrainProject,
)

__all__ = [
    "AuthoringTool",
    "BrushToolSettings",
    "Coastline",
    "ElevationMode",
    "ElevationPoint",
    "EndpointGrid",
    "FeatureToolSettings",
    "LandComponent",
    "LandformKind",
    "LandformSettings",
    "LocalMetricFrame",
    "TerrainAuthoringState",
    "TerrainBrushStroke",
    "TerrainConstraint",
    "TerrainProject",
    "TerrainRegion",
    "TerrainSettings",
    "TerrainStructure",
    "landform_preset",
]
