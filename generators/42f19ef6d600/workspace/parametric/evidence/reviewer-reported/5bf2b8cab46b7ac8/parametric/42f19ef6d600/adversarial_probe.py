#!/usr/bin/env python3
"""Re-run bounded verifier attacks for the 42f19ef6d600 prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root


HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators/42f19ef6d600/workspace/parametric/prototype.py"
CANONICAL_PRIVATE = HERE / "canonical.private.json"
SWAPPED_PRIVATE = HERE / "swapped.private.json"
CANONICAL_GENERATION = HERE / "canonical.generate.stdout.json"
OUT = HERE / "adversarial-manifest.json"


def load_prototype():
    spec = importlib.util.spec_from_file_location("parametric_42f19ef6d600_probe", PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(value) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def expect_rejection(call, expected: str) -> str:
    try:
        call()
    except ValueError as error:
        message = str(error)
        if expected not in message:
            raise AssertionError(f"wrong rejection: {message!r}") from error
        return message
    raise AssertionError(f"expected rejection containing {expected!r}")


def main() -> int:
    prototype = load_prototype()
    canonical = json.loads(CANONICAL_PRIVATE.read_text(encoding="utf-8"))
    swapped = json.loads(SWAPPED_PRIVATE.read_text(encoding="utf-8"))
    generation = json.loads(CANONICAL_GENERATION.read_text(encoding="utf-8"))
    public_path = (ROOT / generation["public"]).resolve()
    if not public_path.is_relative_to(ROOT.parent / "checks"):
        raise RuntimeError(f"public evidence escapes checks: {public_path}")
    public = json.loads(public_path.read_text(encoding="utf-8"))

    cross_setting = copy.deepcopy(canonical)
    original = cross_setting["test"][0]["output"]
    substitute = copy.deepcopy(swapped["test"][0]["output"])
    cross_setting["test"][0]["output"] = substitute
    cross_setting["test"][0]["output_sha256"] = digest(substitute)
    cross_error = expect_rejection(
        lambda: prototype.verify_episode(cross_setting),
        "stored output is not the Racket label",
    )

    provenance_errors = {}
    mutations = {
        "seed": lambda episode: episode.__setitem__("seed", episode["seed"] + 1),
        "profile": lambda episode: episode["test"][0].__setitem__("profile", "solid_square"),
        "sample_index": lambda episode: episode["train"][0].__setitem__(
            "sample_index", episode["train"][0]["sample_index"] + 1
        ),
    }
    for name, mutate in mutations.items():
        tampered = copy.deepcopy(canonical)
        mutate(tampered)
        provenance_errors[name] = expect_rejection(
            lambda tampered=tampered: prototype.verify_episode(tampered),
            "pair sampler provenance mismatch",
        )

    leaked = copy.deepcopy(public)
    leaked["test"][0]["output"] = copy.deepcopy(canonical["test"][0]["output"])
    leak_error = expect_rejection(
        lambda: prototype.verify_public_projection(canonical, leaked),
        "public artifact differs from visible-only projection",
    )

    report = {
        "schema": "arcpuzzles-parametric-adversarial-v2",
        "cross_setting": {
            "rejected": True,
            "error": cross_error,
            "private_setting": "canonical",
            "profile": cross_setting["test"][0]["profile"],
            "test_index": 0,
            "original_output_sha256": digest(original),
            "substituted_swapped_output_sha256": digest(substitute),
            "stored_hash_recomputed": True,
        },
        "sampler_provenance": {
            "rejected": True,
            "mutations": provenance_errors,
        },
        "public_label_leak": {
            "rejected": True,
            "error": leak_error,
            "public_id": generation["public_id"],
            "test_index": 0,
            "added_field": "output",
        },
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
