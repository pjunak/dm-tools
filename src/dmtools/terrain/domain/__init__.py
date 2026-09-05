"""Dependency-light terrain concepts and validation rules."""

from dmtools.terrain.domain.coordinates import EndpointGrid, LocalMetricFrame
from dmtools.terrain.domain.models import (
    Coastline,
    ElevationMode,
    ElevationPoint,
    LandComponent,
    TerrainBrushStroke,
    TerrainConstraint,
    TerrainSettings,
    TerrainStructure,
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
    "LocalMetricFrame",
    "TerrainAuthoringState",
    "TerrainBrushStroke",
    "TerrainConstraint",
    "TerrainProject",
    "TerrainSettings",
    "TerrainStructure",
]
