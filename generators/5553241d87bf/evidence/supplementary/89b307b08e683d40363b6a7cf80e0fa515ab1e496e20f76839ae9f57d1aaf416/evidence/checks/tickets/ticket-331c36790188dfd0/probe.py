#!/usr/bin/env python3
"""One bounded probe of the advertised scene_profile override boundary."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

TICKET_ID = "ticket-331c36790188dfd0"
TASK_ID = "5553241d87bf"
PINNED_SOURCE_SHA256 = "b5f6ba93ce67123cb4c48e979b323277bdd284e400329a1e4f332a24707fc23d"
VALID_PROFILE = "cell3_corner_template"
INVALID_PROFILE = "not-a-declared-profile"


def main() -> int:
    started = time.monotonic()
    here = Path(__file__).resolve()
    workspace = next(parent for parent in here.parents if (parent / "repo").is_dir())
    repo = workspace / "repo"
    sys.path.insert(0, str(repo / "shared/runtime"))
    from reviewer_support import load_selected_generator

    module, source, digest = load_selected_generator(TASK_ID, root=repo)
    assert digest == PINNED_SOURCE_SHA256
    assert hashlib.sha256(source.read_bytes()).hexdigest() == PINNED_SOURCE_SHA256
    assert VALID_PROFILE in module.SCENE_PROFILES
    assert "scene_profile" in module.AXES

    grid = module.generate(
        20261023,
        0,
        difficulty="easy",
        scene_profile=VALID_PROFILE,
    )
    observed = module.observe_overrides(grid)
    valid_errors = module.self_check(grid, difficulty="easy")
    assert observed == {"scene_profile": VALID_PROFILE}
    assert valid_errors == []
    assert module.rule_mirror(grid) != grid

    invalid_error = None
    try:
        module.generate(
            20261023,
            0,
            difficulty="easy",
            scene_profile=INVALID_PROFILE,
        )
    except ValueError as error:
        invalid_error = {"type": type(error).__name__, "message": str(error)}
    assert invalid_error is not None
    assert "draw_choice('scene_profile')" in invalid_error["message"]
    assert "not in options" in invalid_error["message"]

    result = {
        "schema": "arcpuzzles-ticket-api-boundary-v1",
        "ticket_id": TICKET_ID,
        "status": "completed",
        "disposition": "boundary_behaves_as_advertised",
        "task_id": TASK_ID,
        "source_path": str(source.relative_to(repo)),
        "source_sha256": digest,
        "axis": "scene_profile",
        "valid_call": {
            "seed": 20261023,
            "sample_index": 0,
            "difficulty": "easy",
            "override": VALID_PROFILE,
            "observed_overrides": observed,
            "self_check_errors": valid_errors,
            "height": len(grid),
            "width": len(grid[0]),
            "visible_change": module.rule_mirror(grid) != grid,
        },
        "invalid_call": {
            "override": INVALID_PROFILE,
            "error": invalid_error,
        },
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "finding": None,
    }
    out = here.with_name("result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
