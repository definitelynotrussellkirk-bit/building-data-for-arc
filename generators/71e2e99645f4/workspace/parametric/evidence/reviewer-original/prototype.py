#!/usr/bin/env python3
"""Proposed episode-level output-order and palette variants for 71e2e99645f4.

The canonical/default setting is byte-identical to the selected Racket rule.
Alternative settings change only the final ordering of classified sections and/or
swap the center-hole and bottom-hole class colors. Inputs remain in the selected
production generator's exact 4×14 grammar. This module is an unapproved task-local
authoring prototype, not a production API.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

TASK_ID = "71e2e99645f4"
VERSION = "proposed-order-palette-v1"
CANONICAL_RULE_HASH = "d38a7d9b0fc4"
CANONICAL_SHA256 = "4c0a9e13b111d722867ab8519d03504c09fe23c1da7f1185a0fa55351fceaef8"
CANONICAL_FINAL_EXPRESSION = "(classify r)"

ALLOWED_SECTION_ORDERS = ("left_to_right", "right_to_left")
ALLOWED_PALETTES = ("canonical", "swap_center_bottom")
DEFAULT_SECTION_ORDER = "left_to_right"
DEFAULT_PALETTE = "canonical"
PARAMETER_SETTINGS = (
    ("left_to_right", "canonical"),
    ("left_to_right", "swap_center_bottom"),
    ("right_to_left", "canonical"),
    ("right_to_left", "swap_center_bottom"),
)
COVERAGE_SEEDS = (0, 1, 2, 3)

# Every triple below makes all four parameter settings produce distinct outputs.
EPISODE_PATTERN_TRIPLES = (
    ("no_hole", "center_hole", "bottom_hole"),
    ("edge_hole", "center_hole", "no_hole"),
    ("bottom_hole", "edge_hole", "no_hole"),
    ("center_hole", "bottom_hole", "edge_hole"),
)

TASK_HOME = Path(__file__).resolve().parents[2]
GENERATOR_PATH = TASK_HOME / "generator.py"


def _sha256(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def grid_sha256(grid: Any) -> str:
    return _sha256(_json(normalize_grid(grid)))


def _validate_seed(seed: Any) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"parametric_input_source_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check_canonical_source(source: Any) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CANONICAL_FINAL_EXPRESSION) != 1:
        raise ValueError("canonical source must contain one final classify expression")
    return source


def canonical_source(*, root: Path | None = None) -> str:
    root = find_root(__file__) if root is None else Path(root)
    sources: set[Any] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row.get("program_solution"))
    if len(sources) != 1:
        raise ValueError(f"expected exactly one canonical source for {TASK_ID}")
    return _check_canonical_source(sources.pop())


def _validate_parameters(section_order: Any, palette: Any) -> tuple[str, str]:
    if type(section_order) is not str or section_order not in ALLOWED_SECTION_ORDERS:
        raise ValueError(
            "section_order must be one of: " + ", ".join(ALLOWED_SECTION_ORDERS)
        )
    if type(palette) is not str or palette not in ALLOWED_PALETTES:
        raise ValueError("palette must be one of: " + ", ".join(ALLOWED_PALETTES))
    return section_order, palette


def materialize_rule(
    section_order: str = DEFAULT_SECTION_ORDER,
    palette: str = DEFAULT_PALETTE,
    *,
    root: Path | None = None,
    source: str | None = None,
) -> str:
    """Return exact Racket for one bounded setting.

    The default returns canonical source byte-for-byte. Non-default settings
    replace only the unique final ``(classify r)`` expression.
    """
    section_order, palette = _validate_parameters(section_order, palette)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if (section_order, palette) == (DEFAULT_SECTION_ORDER, DEFAULT_PALETTE):
        return canonical

    if section_order == "right_to_left":
        index_expression = "(- 2 r)"
    else:
        # Keep the same index while ensuring the non-default source no longer
        # contains the exact canonical final expression.
        index_expression = "(+ r 0)"
    classify_expression = f"(classify {index_expression})"
    if palette == "swap_center_bottom":
        replacement = (
            f"(let ((v {classify_expression})) "
            "(cond ((= v 8) 4) ((= v 4) 8) (else v)))"
        )
    else:
        replacement = classify_expression

    variant = canonical.replace(CANONICAL_FINAL_EXPRESSION, replacement, 1)
    if variant == canonical or variant.count(CANONICAL_FINAL_EXPRESSION):
        raise ValueError("failed to materialize a guarded final-expression variant")
    return variant


def rule_callable(source: str) -> str:
    if not isinstance(source, str) or not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("unexpected Racket rule wrapper")
    return source[len("(rule! ") : -1]


def execute_rule(source: str, grid: Any, *, bridge: RacketBridge | None = None):
    """Execute one materialized rule through the bundled Racket runtime."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def parameters_for_seed(seed: int) -> dict[str, str]:
    _validate_seed(seed)
    section_order, palette = PARAMETER_SETTINGS[seed % len(PARAMETER_SETTINGS)]
    return {"section_order": section_order, "palette": palette}


def episode_inputs(seed: int) -> list[list[list[int]]]:
    """Create four lawful, controlled inputs that distinguish all settings."""
    _validate_seed(seed)
    generator = _load_generator()
    difficulty = ("easy", "medium", "hard")[seed % 3]
    input_seed = 710_000_000 + seed
    grids = []
    for index, patterns in enumerate(EPISODE_PATTERN_TRIPLES):
        fill_color = 1 + ((seed + 2 * index) % 9)
        grid = generator.generate(
            input_seed,
            index,
            difficulty=difficulty,
            fill_color=fill_color,
            hole_patterns=list(patterns),
        )
        findings = generator.self_check(grid, difficulty=difficulty)
        if findings:
            raise ValueError("prototype input left canonical domain: " + "; ".join(findings))
        grids.append(grid)
    return grids


def _setting_id(setting: tuple[str, str]) -> str:
    return f"order-{setting[0]}__palette-{setting[1]}"


def _build_episode(seed: int, *, root: Path, bridge: RacketBridge) -> dict[str, Any]:
    parameters = parameters_for_seed(seed)
    selected = (parameters["section_order"], parameters["palette"])
    sources = {
        setting: materialize_rule(*setting, root=root)
        for setting in PARAMETER_SETTINGS
    }
    inputs = episode_inputs(seed)
    outputs = {
        setting: [execute_rule(source, grid, bridge=bridge) for grid in inputs]
        for setting, source in sources.items()
    }
    selected_outputs = outputs[selected]
    train = [
        {"input": copy.deepcopy(inputs[index]), "output": copy.deepcopy(selected_outputs[index])}
        for index in range(3)
    ]
    test = [{"input": copy.deepcopy(inputs[3]), "output": copy.deepcopy(selected_outputs[3])}]

    rivals = []
    ambiguities = []
    for setting in PARAMETER_SETTINGS:
        if setting == selected:
            continue
        demo_mismatches = [
            index for index in range(3) if outputs[setting][index] != selected_outputs[index]
        ]
        query_mismatches = [0] if outputs[setting][3] != selected_outputs[3] else []
        status = "refuted_by_demonstrations" if demo_mismatches else "survives_demonstrations"
        row = {
            "section_order": setting[0],
            "palette": setting[1],
            "status": status,
            "racket_sha256": _sha256(sources[setting]),
            "demonstration_mismatch_indices": demo_mismatches,
            "query_mismatch_indices": query_mismatches,
        }
        rivals.append(row)
        if not demo_mismatches:
            ambiguities.append(row)

    return {
        "schema": "arcpuzzles-parametric-episode-v1",
        "task_id": TASK_ID,
        "version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "racket_source": sources[selected],
        "racket_sha256": _sha256(sources[selected]),
        "input_sha256": [grid_sha256(grid) for grid in inputs],
        "train": train,
        "test": test,
        "parameter_rivals": rivals,
        "ambiguities": ambiguities,
    }


def make_episode(
    seed: int,
    *,
    root: Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    _validate_seed(seed)
    root = find_root(__file__) if root is None else Path(root)
    if bridge is None:
        with RacketBridge() as owned:
            return _build_episode(seed, root=root, bridge=owned)
    return _build_episode(seed, root=root, bridge=bridge)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def canonical_replay(*, root: Path, bridge: RacketBridge) -> dict[str, Any]:
    source = materialize_rule(root=root)
    rows = []
    for index, pair in enumerate(canonical_pairs(TASK_ID, root=root)):
        actual = execute_rule(source, pair["input"], bridge=bridge)
        rows.append(
            {
                "index": index,
                "input_sha256": grid_sha256(pair["input"]),
                "expected_sha256": grid_sha256(pair["output"]),
                "actual_sha256": grid_sha256(actual),
                "matches": actual == pair["output"],
            }
        )
    return {
        "status": "pass" if all(row["matches"] for row in rows) else "fail",
        "rule_hash": CANONICAL_RULE_HASH,
        "racket_sha256": _sha256(source),
        "pairs_checked": len(rows),
        "pairs": rows,
    }


def _manifest_rows(out: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(candidate for candidate in out.rglob("*") if candidate.is_file()):
        relative = path.relative_to(out).as_posix()
        if relative in {"report.json", "failure.json"}:
            continue
        body = path.read_bytes()
        rows.append({"path": relative, "bytes": len(body), "sha256": _sha256(body)})
    return rows


def write_evidence(
    seeds: Iterable[int],
    *,
    out: Path,
    root: Path | None = None,
) -> dict[str, Any]:
    seeds = tuple(seeds)
    if not seeds:
        raise ValueError("at least one seed is required")
    for seed in seeds:
        _validate_seed(seed)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__) if root is None else Path(root)

    with RacketBridge() as bridge:
        rules: dict[tuple[str, str], dict[str, str]] = {}
        for setting in PARAMETER_SETTINGS:
            source = materialize_rule(*setting, root=root)
            path = out / "private" / "rules" / f"{_setting_id(setting)}.rkt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")
            rules[setting] = {
                "path": path.relative_to(out).as_posix(),
                "sha256": _sha256(source),
            }

        replay = canonical_replay(root=root, bridge=bridge)
        episode_rows = []
        private_episodes = []
        settings_seen = set()
        ambiguity_count = 0
        for seed in seeds:
            episode = make_episode(seed, root=root, bridge=bridge)
            selected = (
                episode["parameters"]["section_order"],
                episode["parameters"]["palette"],
            )
            settings_seen.add(selected)
            ambiguity_count += len(episode["ambiguities"])
            episode["racket_path"] = rules[selected]["path"]
            private_path = out / "private" / "episodes" / f"episode-{seed:03d}.json"
            public_path = out / "public" / f"episode-{seed:03d}.json"
            _write_json(private_path, episode)
            _write_json(public_path, public_challenge(episode))
            private_episodes.append(episode)
            episode_rows.append(
                {
                    "seed": seed,
                    "section_order": selected[0],
                    "palette": selected[1],
                    "private_path": private_path.relative_to(out).as_posix(),
                    "public_path": public_path.relative_to(out).as_posix(),
                    "racket_path": rules[selected]["path"],
                    "racket_sha256": rules[selected]["sha256"],
                }
            )

        witness_grid = copy.deepcopy(private_episodes[0]["train"][0]["input"])
        witness_outputs = {
            _setting_id(setting): execute_rule(
                materialize_rule(*setting, root=root), witness_grid, bridge=bridge
            )
            for setting in PARAMETER_SETTINGS
        }
        witness = {
            "input": witness_grid,
            "input_sha256": grid_sha256(witness_grid),
            "outputs": witness_outputs,
            "outputs_sha256": {
                name: grid_sha256(output) for name, output in witness_outputs.items()
            },
        }
        _write_json(out / "private" / "shared-setting-witness.json", witness)

    report = {
        "schema": "arcpuzzles-parametric-evidence-v1",
        "task_id": TASK_ID,
        "version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "parameters": {
            "section_order": {
                "allowed": list(ALLOWED_SECTION_ORDERS),
                "default": DEFAULT_SECTION_ORDER,
            },
            "palette": {
                "allowed": list(ALLOWED_PALETTES),
                "default": DEFAULT_PALETTE,
            },
        },
        "counts": {
            "episodes": len(seeds),
            "settings_covered": len(settings_seen),
            "ambiguous_parameter_rivals": ambiguity_count,
            "canonical_pairs_checked": replay["pairs_checked"],
        },
        "canonical_replay": replay,
        "shared_witness": witness,
        "episodes": episode_rows,
        "runtime": {
            "python": sys.version,
            "executable": sys.executable,
            "cwd": os.getcwd(),
            "racket_path": os.environ.get("RACKET_PATH"),
        },
    }
    report["files"] = _manifest_rows(out)
    _write_json(out / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(COVERAGE_SEEDS))
    args = parser.parse_args(argv)
    try:
        report = write_evidence(args.seeds, out=args.out)
    except Exception as exc:
        if args.out.exists() and args.out.is_dir():
            _write_json(
                args.out / "failure.json",
                {"type": type(exc).__name__, "message": str(exc)},
            )
        raise
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
