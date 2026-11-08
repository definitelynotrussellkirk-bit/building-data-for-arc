#!/usr/bin/env python3
"""Bounded parametric prototype for ARC task 4ca8a7b38652.

The production/canonical setting is ``count_scope='nonzero'``: the upscale
factor is the number of distinct nonzero colors.  The proposed ``'all'``
setting counts every distinct color, including zero.  A setting is selected
once for the whole episode; inputs are generated independently of that hidden
setting, and zero-present demonstrations distinguish the two rules.

This module is authoring evidence only.  It does not modify the selected
canonical rule or production sampler.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "4ca8a7b38652"
PROTOTYPE_VERSION = "count-scope-v1"
PARAMETER_NAME = "count_scope"
SETTINGS = ("nonzero", "all")
DEFAULT_SETTING = "nonzero"
CANONICAL_RULE_SHA256 = (
    "d91346f9bf6dbc10251783f3ea5e16533a63631db37bec02b3f21d3735d214c6"
)

# A complete five-pair curriculum contains both zero-present and zero-free
# inputs.  Four demonstrations retain both kinds, so either setting is
# identifiable before the held-out query.
PROFILE_SEQUENCE: tuple[tuple[int, bool], ...] = (
    (2, True),
    (3, False),
    (4, True),
    (2, False),
    (4, True),
)

_NONZERO_COLOR_EXPR = """(unique (filter (lambda (v) (!= v 0))
                                          (flatmap (lambda (r)
                                                     (map (lambda (c) (at g r c))
                                                          (range 0 w)))
                                                   (range 0 h))))"""
_ALL_COLOR_EXPR = """(unique (flatmap (lambda (r)
                             (map (lambda (c) (at g r c))
                                  (range 0 w)))
                           (range 0 h)))"""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _validate_seed(seed: int) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def _validate_setting(setting: str) -> str:
    if setting not in SETTINGS:
        raise ValueError(f"count_scope must be one of {SETTINGS}, got {setting!r}")
    return setting


def choose_setting(seed: int) -> str:
    """Choose one hidden setting deterministically for the complete episode."""
    _validate_seed(seed)
    return SETTINGS[seed % len(SETTINGS)]


def canonical_source(*, root: Path | str | None = None) -> str:
    """Read and content-bind the one canonical Racket program for this task."""
    if root is None:
        root = find_root(__file__)
    matches: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if not isinstance(program, str) or not program.strip():
                    raise ValueError(f"{TASK_ID}: canonical program_solution missing")
                matches.append(program)
    if len(matches) != 1:
        raise ValueError(
            f"{TASK_ID}: expected one canonical program, found {len(matches)}"
        )
    source = matches[0]
    digest = _sha256_bytes(source.encode("utf-8"))
    if digest != CANONICAL_RULE_SHA256:
        raise ValueError(
            f"{TASK_ID}: canonical rule hash drifted: {digest} != "
            f"{CANONICAL_RULE_SHA256}"
        )
    return source


def materialize_rule(
    setting: str,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    """Return an exact executable ``(rule! ...)`` program for one setting."""
    setting = _validate_setting(setting)
    canonical = canonical_source(root=root) if source is None else source
    if setting == DEFAULT_SETTING:
        return canonical
    occurrences = canonical.count(_NONZERO_COLOR_EXPR)
    if occurrences != 1:
        raise ValueError(
            "canonical rule no longer has the single expected nonzero-color expression"
        )
    alternative = canonical.replace(_NONZERO_COLOR_EXPR, _ALL_COLOR_EXPR, 1)
    if "(filter (lambda (v) (!= v 0))" in alternative:
        raise AssertionError("alternative rule still excludes zero")
    return alternative


def _rule_body(program: str) -> str:
    text = program.strip()
    if not text.startswith("(rule!") or not text.endswith(")"):
        raise ValueError("program must be a complete (rule! BODY) form")
    return text[len("(rule!") : -1].strip()


def _grid_literal(grid: list[list[int]]) -> str:
    normalized = normalize_grid(grid)
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in normalized)
    return f"'({rows})"


def apply_racket(bridge: Any, program: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute one materialized rule in the protected persistent Racket bridge."""
    expression = f"({_rule_body(program)} {_grid_literal(grid)})"
    return normalize_grid(bridge.eval_text(expression))


def apply_python(grid: list[list[int]], setting: str) -> list[list[int]]:
    """Small independent mirror used for tests and Racket parity checks."""
    setting = _validate_setting(setting)
    source = normalize_grid(grid)
    colors = {value for row in source for value in row}
    if setting == "nonzero":
        colors.discard(0)
    factor = len(colors)
    if factor <= 1:
        return [row[:] for row in source]
    output: list[list[int]] = []
    for row in source:
        expanded = [value for value in row for _ in range(factor)]
        output.extend(expanded[:] for _ in range(factor))
    return output


def build_input(
    seed: int,
    pair_index: int,
    *,
    root: Path | str | None = None,
) -> list[list[int]]:
    """Build one setting-independent input from the selected production sampler."""
    _validate_seed(seed)
    if type(pair_index) is not int or not 0 <= pair_index < len(PROFILE_SEQUENCE):
        raise ValueError(f"pair_index must be 0..{len(PROFILE_SEQUENCE) - 1}")
    if root is None:
        root = find_root(__file__)
    generator, _path, _digest = load_selected_generator(TASK_ID, root=root)
    color_count, zero_present = PROFILE_SEQUENCE[pair_index]
    # Explicit axes keep input semantics independent of the hidden rule setting.
    # The derived seed/index vary layout/palette while remaining reproducible.
    derived_seed = seed * 101 + 17
    difficulty = ("easy", "medium", "hard", "medium", "hard")[pair_index]
    return generator.generate(
        derived_seed,
        pair_index,
        difficulty=difficulty,
        color_count=color_count,
        zero_present=zero_present,
    )


def _build_pairs(
    seed: int,
    setting: str,
    *,
    root: Path | str,
    bridge: Any | None,
) -> tuple[list[dict[str, Any]], list[int]]:
    program = materialize_rule(setting, root=root)
    rival = next(value for value in SETTINGS if value != setting)
    pairs: list[dict[str, Any]] = []
    rival_diff_cells: list[int] = []
    for pair_index in range(len(PROFILE_SEQUENCE)):
        grid = build_input(seed, pair_index, root=root)
        expected = apply_python(grid, setting)
        if bridge is not None:
            actual = apply_racket(bridge, program, grid)
            if actual != expected:
                raise AssertionError(
                    f"Racket/Python mismatch for {setting=} {seed=} {pair_index=}"
                )
            output = actual
        else:
            output = expected
        rival_output = apply_python(grid, rival)
        diff = sum(
            1
            for row_a, row_b in zip(output, rival_output)
            for a, b in zip(row_a, row_b)
            if a != b
        ) if (
            len(output) == len(rival_output)
            and len(output[0]) == len(rival_output[0])
        ) else -1
        rival_diff_cells.append(diff)
        pairs.append({"input": copy.deepcopy(grid), "output": output})
    return pairs, rival_diff_cells


def make_episode(
    seed: int,
    setting: str | None = None,
    *,
    root: Path | str | None = None,
    verify_racket: bool = True,
) -> dict[str, Any]:
    """Build four demonstrations and one query for one fixed hidden setting."""
    _validate_seed(seed)
    selected = choose_setting(seed) if setting is None else _validate_setting(setting)
    if root is None:
        root = find_root(__file__)
    root = Path(root).resolve()

    bridge = None
    try:
        if verify_racket:
            from arc_repl.racket_bridge import RacketBridge

            bridge = RacketBridge(max_calls_before_restart=64, timeout=30.0)
        pairs, rival_diff_cells = _build_pairs(
            seed, selected, root=root, bridge=bridge
        )
    finally:
        if bridge is not None:
            bridge.shutdown()

    rival = next(value for value in SETTINGS if value != selected)
    if not any(apply_python(pair["input"], rival) != pair["output"] for pair in pairs[:4]):
        raise AssertionError("demonstrations do not distinguish the other setting")

    program = materialize_rule(selected, root=root)
    return {
        "schema": "arcpuzzles-parametric-count-scope-episode-v1",
        "train": pairs[:4],
        "test": pairs[4:],
        "program": program,
        "meta": {
            "task_id": TASK_ID,
            "seed": seed,
            PARAMETER_NAME: selected,
            "canonical_default": DEFAULT_SETTING,
            "prototype_version": PROTOTYPE_VERSION,
            "profile_sequence": [
                {"color_count": n, "zero_present": zero}
                for n, zero in PROFILE_SEQUENCE
            ],
            "program_sha256": _sha256_bytes(program.encode("utf-8")),
            "canonical_rule_sha256": CANONICAL_RULE_SHA256,
            "racket_verified": verify_racket,
            "rival_setting": rival,
            "rival_diff_cells": rival_diff_cells,
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Hide the parameter, program, and held-out query answer."""
    return {
        "schema": "arcpuzzles-parametric-count-scope-public-v1",
        "train": copy.deepcopy(episode["train"]),
        "test": [
            {"input": copy.deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def write_evidence(
    out_dir: Path,
    *,
    seeds: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Materialize Racket-verified public/private examples for both settings."""
    if out_dir.exists():
        raise FileExistsError(f"choose a new output directory: {out_dir}")
    seeds = {"nonzero": 0, "all": 1} if seeds is None else dict(seeds)
    if set(seeds) != set(SETTINGS):
        raise ValueError(f"seeds must provide exactly {SETTINGS}")

    private_dir = out_dir / "private"
    public_dir = out_dir / "public"
    rules_dir = private_dir / "rules"
    episodes_dir = private_dir / "episodes"
    for directory in (rules_dir, episodes_dir, public_dir):
        directory.mkdir(parents=True, exist_ok=False)

    root = find_root(__file__)
    source_path = Path(__file__).resolve()
    generator, generator_path, generator_sha = load_selected_generator(
        TASK_ID, root=root
    )
    del generator

    records: dict[str, Any] = {}
    for setting in SETTINGS:
        seed = _validate_seed(seeds[setting])
        if choose_setting(seed) != setting:
            raise ValueError(
                f"seed {seed} naturally selects {choose_setting(seed)!r}, not {setting!r}"
            )
        episode = make_episode(
            seed, setting=setting, root=root, verify_racket=True
        )
        public = public_challenge(episode)
        rule_path = rules_dir / f"{setting}.rkt"
        episode_path = episodes_dir / f"{setting}.json"
        public_path = public_dir / f"{setting}.json"
        rule_path.write_text(episode["program"] + "\n", encoding="utf-8")
        episode_path.write_text(
            json.dumps(episode, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        public_path.write_text(
            json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        records[setting] = {
            "seed": seed,
            "rule": str(rule_path.relative_to(out_dir)),
            "rule_sha256": _sha256_bytes(episode["program"].encode("utf-8")),
            "private_episode": str(episode_path.relative_to(out_dir)),
            "private_episode_sha256": _sha256_json(episode),
            "public_challenge": str(public_path.relative_to(out_dir)),
            "public_challenge_sha256": _sha256_json(public),
            "rival_diff_cells": episode["meta"]["rival_diff_cells"],
            "demonstrations_refute_rival": any(
                value != 0 for value in episode["meta"]["rival_diff_cells"][:4]
            ),
        }

    manifest = {
        "schema": "arcpuzzles-parametric-count-scope-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": PARAMETER_NAME,
        "settings": list(SETTINGS),
        "canonical_default": DEFAULT_SETTING,
        "canonical_rule_sha256": CANONICAL_RULE_SHA256,
        "prototype_source": str(source_path.relative_to(root)),
        "prototype_source_sha256": _sha256_bytes(source_path.read_bytes()),
        "selected_generator": str(generator_path.relative_to(root)),
        "selected_generator_sha256": generator_sha,
        "label_authority": "protected Racket execution of each materialized rule",
        "production_path_modified": False,
        "records": records,
        "limitations": [
            "This is a bounded authoring prototype, not an approved production rule.",
            "Only two count scopes are tested; no universal identifiability claim is made.",
            "Zero-free inputs are invariant across settings, so at least one zero-present demonstration is required.",
        ],
    }
    manifest_path = out_dir / "evidence.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = write_evidence(args.out)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
