#!/usr/bin/env python3
"""One-call-pair probe for the advertised texture override boundary."""
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root, load_selected_generator

TICKET_ID = "ticket-6e4e0446a4bfbf97"
TASK_ID = "2f0b1cb87615"
TICKET_SEED_HEX = "e2f6ec1f859c3ee1e6fd45649eba26313a1b95665dd3ba77de05f4c5231d6f4f"
PINNED_SOURCE_SHA256 = "366e081abbab1cf88fa7fb5dfe9627eb08ec9f23aaee53d1774ba33194707b54"
VALID_TEXTURE = "warm"
INVALID_TEXTURE = "not-a-texture"


def canonical_json_sha256(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def describe_call(generator, base_module, *, seed: int, texture: str) -> dict[str, Any]:
    observed = []
    base_module.set_ctx_observer(observed.append)
    try:
        try:
            grid = generator.generate(seed, 0, texture=texture)
        except Exception as exc:  # Retain actual API behavior rather than prescribe it.
            return {
                "accepted": False,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "requested_override": {"texture": texture},
            }
    finally:
        base_module.set_ctx_observer(None)

    if len(observed) != 1:
        raise RuntimeError(f"expected one GenCtx, observed {len(observed)}")
    ctx = observed[0]
    findings = generator.self_check(grid)
    return {
        "accepted": True,
        "requested_override": {"texture": texture},
        "overrides_used": ctx.overrides_used(),
        "recorded_draws": ctx.recorded_draws(),
        "grid_shape": [len(grid), len(grid[0])],
        "grid_sha256": canonical_json_sha256(grid),
        "self_check": findings,
    }


def main() -> int:
    root = find_root(__file__)
    generator, source, digest = load_selected_generator(TASK_ID, root=root)
    if digest != PINNED_SOURCE_SHA256:
        raise RuntimeError(
            f"source drift for {TASK_ID}: expected {PINNED_SOURCE_SHA256}, got {digest}"
        )
    declared = generator.AXES["texture"]["valid"].split("|")
    if VALID_TEXTURE not in declared or INVALID_TEXTURE in declared:
        raise RuntimeError("probe values do not form the advertised valid/invalid pair")

    base_module = inspect.getmodule(generator.gen_ctx)
    if base_module is None or not hasattr(base_module, "set_ctx_observer"):
        raise RuntimeError("could not access the selected runtime's GenCtx observer")

    seed = int(TICKET_SEED_HEX, 16)
    valid = describe_call(generator, base_module, seed=seed, texture=VALID_TEXTURE)
    invalid = describe_call(generator, base_module, seed=seed, texture=INVALID_TEXTURE)
    same_result = (
        valid.get("accepted") is True
        and invalid.get("accepted") is True
        and valid.get("grid_sha256") == invalid.get("grid_sha256")
    )
    ignored_both = (
        valid.get("overrides_used") == {}
        and invalid.get("overrides_used") == {}
        and valid.get("accepted") is True
        and invalid.get("accepted") is True
    )

    report = {
        "schema": "arcpuzzles-api-boundary-probe-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "source": {
            "path": str(source.relative_to(root)),
            "sha256": digest,
            "version": generator.VERSION,
            "rule_hash": "65fad7861ecf",
        },
        "boundary": {
            "axis": "texture",
            "advertised_valid": generator.AXES["texture"]["valid"],
            "valid_value": VALID_TEXTURE,
            "invalid_value": INVALID_TEXTURE,
            "comparison": "same ticket-derived seed and sample_index=0; only texture differs",
        },
        "valid_call": valid,
        "invalid_call": invalid,
        "observed": {
            "both_calls_accepted": valid.get("accepted") is True and invalid.get("accepted") is True,
            "both_overrides_unconsumed": ignored_both,
            "identical_grid": same_result,
        },
        "finding": (
            "The advertised finite texture boundary is not enforced: both the declared-valid "
            "'warm' value and an undeclared value were accepted, neither override was consumed, "
            "and both calls returned the same grid."
            if ignored_both and same_result
            else None
        ),
        "limits": [
            "One source-bound valid/invalid comparison only, as required by the ticket.",
            "No claim is made about unrelated axes or other generator versions.",
        ],
    }
    out = Path(__file__).with_name("report.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ticket_id": TICKET_ID,
        "source_sha256": digest,
        "both_calls_accepted": report["observed"]["both_calls_accepted"],
        "both_overrides_unconsumed": ignored_both,
        "identical_grid": same_result,
        "finding": report["finding"],
        "report": str(out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
