"""Versioned, language-neutral seed derivation for named terrain stages."""

import re
from hashlib import sha256
from typing import Literal

type SeedPolicy = Literal["legacy-shared-coordinate-seed@1", "named-stage-sha256@1"]

LEGACY_SEED_POLICY: SeedPolicy = "legacy-shared-coordinate-seed@1"
NAMED_SEED_POLICY: SeedPolicy = "named-stage-sha256@1"
RELIEF_STAGE_ID = "terrain.relief"
_SEED_DOMAIN = b"dmtools.terrain-stage-seed@1\x00"
_STAGE_NAME = re.compile(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*", re.ASCII)


def validate_master_seed(seed: object) -> None:
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 0xFFFFFFFF:
        raise ValueError("Seed must be an integer between 0 and 4,294,967,295.")


def stage_seed(master_seed: int, stage_id: str, policy: SeedPolicy) -> int:
    """Resolve one stream without depending on stage order, grid or process state.

    Named policy hashes the domain bytes, a four-byte big-endian unsigned
    master seed and an ASCII stage identifier; the first four digest bytes
    are interpreted as an unsigned big-endian integer. Names are compatibility
    identifiers, not user-facing labels. This is not a cryptographic secret.
    """
    validate_master_seed(master_seed)
    if not 1 <= len(stage_id) <= 128 or _STAGE_NAME.fullmatch(stage_id) is None:
        raise ValueError("Stage identifier must be 1-128 lowercase ASCII name characters.")
    if policy == LEGACY_SEED_POLICY:
        return master_seed
    if policy != NAMED_SEED_POLICY:
        raise ValueError(f"Unsupported seed policy: {policy!r}.")
    payload = _SEED_DOMAIN + master_seed.to_bytes(4, "big") + stage_id.encode("ascii")
    return int.from_bytes(sha256(payload).digest()[:4], "big")
