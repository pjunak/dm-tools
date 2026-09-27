"""Dependency-light terrain concepts and validation rules."""

from dmtools.terrain.domain.coordinates import EndpointGrid, LocalMetricFrame
from dmtools.terrain.domain.models import (
    Coastline,
    ElevationMode,
    ElevationPoint,
    LandComponent,
    LandformKind,
    LandformSettings,
    TerrainBasin,
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
    LakeToolSettings,
    TerrainAuthoringState,
    TerrainProject,
)
from dmtools.terrain.domain.structure_profiles import StructureProfileKnot

__all__ = [
    "AuthoringTool",
    "BrushToolSettings",
    "Coastline",
    "ElevationMode",
    "ElevationPoint",
    "EndpointGrid",
    "FeatureToolSettings",
    "LakeToolSettings",
    "LandComponent",
    "LandformKind",
    "LandformSettings",
    "LocalMetricFrame",
    "StructureProfileKnot",
    "TerrainAuthoringState",
    "TerrainBasin",
    "TerrainBrushStroke",
    "TerrainConstraint",
    "TerrainProject",
    "TerrainRegion",
    "TerrainSettings",
    "TerrainStructure",
    "landform_preset",
]
