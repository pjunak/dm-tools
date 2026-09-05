# pyright: reportPrivateUsage=false
"""Seed compatibility vectors and their actual generation/settings boundaries."""

import tkinter as tk
from dataclasses import replace
from typing import cast

import numpy as np
import pytest

from benchmarks.terrain import fixture
from dmtools.terrain.domain import TerrainSettings
from dmtools.terrain.domain.seeds import (
    LEGACY_SEED_POLICY,
    NAMED_SEED_POLICY,
    RELIEF_STAGE_ID,
    SeedPolicy,
    stage_seed,
)
from dmtools.terrain.pipeline.generate import generate_terrain
from dmtools.terrain.ui import _CONTROLS, TerrainApp


# Independently calculated using .NET SHA256, ASCII and big-endian UInt32.
@pytest.mark.parametrize(
    ("master", "stage", "expected"),
    [
        (0, "terrain.relief", 1845932015),
        (0, "test.rainfall", 1509020038),
        (42, "terrain.relief", 2355644248),
        (42, "test.rainfall", 3354607557),
        (20260902, "terrain.relief", 3486507418),
        (20260902, "test.rainfall", 3681552239),
        (4294967295, "terrain.relief", 380401938),
        (4294967295, "test.rainfall", 377551747),
    ],
)
def test_portable_seed_vectors(master: int, stage: str, expected: int) -> None:
    assert stage_seed(master, stage, NAMED_SEED_POLICY) == expected
    assert stage_seed(master, stage, LEGACY_SEED_POLICY) == master


def test_unrelated_stage_insertion_and_order_do_not_change_existing_streams() -> None:
    before = {
        name: stage_seed(42, name, NAMED_SEED_POLICY) for name in (RELIEF_STAGE_ID, "test.rainfall")
    }
    after = {
        name: stage_seed(42, name, NAMED_SEED_POLICY)
        for name in ("test.rainfall", "test.new-stage", RELIEF_STAGE_ID)
    }
    assert before == {name: after[name] for name in before}
    assert before[RELIEF_STAGE_ID] != before["test.rainfall"]


@pytest.mark.parametrize("seed", [-1, 4294967296, True, 1.5, "42"])
def test_invalid_master_seed_is_rejected_at_domain_boundary(seed: object) -> None:
    with pytest.raises(ValueError, match="Seed must be an integer"):
        TerrainSettings(seed=cast("int", seed))
    with pytest.raises(ValueError, match="Seed must be an integer"):
        stage_seed(cast("int", seed), RELIEF_STAGE_ID, NAMED_SEED_POLICY)


@pytest.mark.parametrize("name", ["", "Terrain.relief", "a\x00b", "a/b", "é", "a" * 129])
def test_invalid_stage_names_are_rejected(name: str) -> None:
    with pytest.raises(ValueError, match="Stage identifier"):
        stage_seed(42, name, NAMED_SEED_POLICY)


def test_unknown_policy_is_rejected() -> None:
    policy = cast("SeedPolicy", "unknown@9")
    with pytest.raises(ValueError, match="Unsupported seed policy"):
        TerrainSettings(seed_policy=policy)
    with pytest.raises(ValueError, match="Unsupported seed policy"):
        stage_seed(42, RELIEF_STAGE_ID, policy)


@pytest.mark.parametrize("case", ["square", "archipelago", "authored"])
def test_named_generation_uses_one_resolved_relief_stream(case: str) -> None:
    coast, settings, constraints = fixture(case, 65, 42)
    named_settings = replace(settings, seed_policy=NAMED_SEED_POLICY)
    named = generate_terrain(coast, named_settings, constraints=constraints)
    resolved = replace(settings, seed=2355644248)
    reference = generate_terrain(coast, resolved, constraints=constraints)
    np.testing.assert_array_equal(named.elevation_m, reference.elevation_m)
    np.testing.assert_array_equal(named.land_mask, reference.land_mask)
    assert named.drainage == reference.drainage
    assert named.settings == named_settings


def test_named_policy_preserves_nested_samples_and_determinism() -> None:
    coast, settings, constraints = fixture("square", 65, 42)
    settings = replace(settings, seed_policy=NAMED_SEED_POLICY)
    coarse = generate_terrain(coast, settings, constraints=constraints)
    fine = generate_terrain(coast, replace(settings, resolution_px=129), constraints=constraints)
    repeated = generate_terrain(coast, settings, constraints=constraints)
    np.testing.assert_array_equal(coarse.elevation_m, fine.elevation_m[::2, ::2])
    assert coarse.elevation_m.tobytes() == repeated.elevation_m.tobytes()
    assert coarse.drainage == fine.drainage == repeated.drainage


@pytest.mark.parametrize("policy", [LEGACY_SEED_POLICY, NAMED_SEED_POLICY])
def test_workbench_settings_round_trip_retains_policy(
    policy: SeedPolicy,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Tcl variables exercise settings persistence without needing a display.
    interpreter = tk.Tcl()
    app = TerrainApp.__new__(TerrainApp)
    app._variables = {spec.key: tk.DoubleVar(interpreter, value=spec.default) for spec in _CONTROLS}
    app._seed_policy_label = tk.StringVar(interpreter, value="Original terrain")
    def refresh_value(key: str) -> None:
        pass

    monkeypatch.setattr(app, "_refresh_value", refresh_value)
    expected = TerrainSettings(seed=42, resolution_px=129, seed_policy=policy)
    app._apply_settings(expected)
    assert app._read_settings() == expected
