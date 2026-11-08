#!/usr/bin/env python3
"""Separate two-parameter rule prototype for task 1c1ef857c9e2.

The selected production generator and canonical Racket authority stay fixed.
This prototype chooses two nearby rule parameters once per episode:

* ``measure_mode``: count output sections (canonical, separators + 1) or count
  separator lines directly;
* ``axis_order``: preserve row/column order (canonical) or transpose it.

All retained labels are checked against exact materialized Racket programs.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
from itertools import product
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable

TASK_ID = "1c1ef857c9e2"
PROTOTYPE_VERSION = "1.0.0"
MEASURE_MODES = ("sections", "separators")
AXIS_ORDERS = ("row_col", "col_row")
DEFAULT_PARAMETERS = {"measure_mode": "sections", "axis_order": "row_col"}
EPISODE_SIZE = 4  # three demonstrations plus one query

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]
REPO = HERE.parents[3]
RULES_DIR = HERE / "rules"
CHALLENGES_DIR = HERE / "challenges"
EPISODES_DIR = HERE / "episodes"
EVIDENCE_DIR = HERE / "evidence"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(payload)


def _load_generator():
    path = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"parametric_source_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load selected generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_setting(*, measure_mode: str, axis_order: str) -> dict[str, str]:
    if measure_mode not in MEASURE_MODES:
        raise ValueError(f"unsupported measure_mode={measure_mode!r}")
    if axis_order not in AXIS_ORDERS:
        raise ValueError(f"unsupported axis_order={axis_order!r}")
    return {"measure_mode": measure_mode, "axis_order": axis_order}


def all_parameter_settings() -> Iterable[dict[str, str]]:
    for measure_mode, axis_order in product(MEASURE_MODES, AXIS_ORDERS):
        yield {"measure_mode": measure_mode, "axis_order": axis_order}


def parameter_for_seed(seed: int) -> dict[str, str]:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    settings = tuple(all_parameter_settings())
    return dict(settings[seed % len(settings)])


def setting_slug(setting: dict[str, str]) -> str:
    value = _validate_setting(**setting)
    return f"{value['measure_mode']}__{value['axis_order']}"


def python_mirror(
    grid: list[list[int]], *, measure_mode: str, axis_order: str
) -> list[list[int]]:
    """Independent Python audit mirror for one prototype rule setting."""
    setting = _validate_setting(measure_mode=measure_mode, axis_order=axis_order)
    generator = _load_generator()
    facts = generator.observe_overrides(grid)
    offset = 1 if setting["measure_mode"] == "sections" else 0
    row_size = facts["n_sep_rows"] + offset
    col_size = facts["n_sep_cols"] + offset
    if setting["axis_order"] == "col_row":
        row_size, col_size = col_size, row_size
    return [[facts["bg_color"] for _ in range(col_size)] for _ in range(row_size)]


def rule_source(*, measure_mode: str, axis_order: str) -> str:
    """Return the exact Racket rule program for one parameter setting."""
    setting = _validate_setting(measure_mode=measure_mode, axis_order=axis_order)
    offset = 1 if setting["measure_mode"] == "sections" else 0
    output_rows = "col-size" if setting["axis_order"] == "col_row" else "row-size"
    output_cols = "row-size" if setting["axis_order"] == "col_row" else "col-size"
    return f"""(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((bg (mode g 0))
                  (sep-rows (filter (lambda (r)
                                      (all? (lambda (c) (!= (at g r c) bg)) (range 0 w)))
                                    (range 0 h)))
                  (sep-color (at g (first sep-rows) 0))
                  (s-rows (filter (lambda (r)
                                    (all? (lambda (c) (= (at g r c) sep-color))
                                          (range 0 w)))
                                  (range 0 h)))
                  (s-cols (filter (lambda (c)
                                    (all? (lambda (r) (= (at g r c) sep-color))
                                          (range 0 h)))
                                  (range 0 w)))
                  (row-size (+ {offset} (length s-rows)))
                  (col-size (+ {offset} (length s-cols))))
             (build-grid {output_rows} {output_cols} (r c) bg)))))
"""


def materialize_rules(directory: Path = RULES_DIR) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for setting in all_parameter_settings():
        slug = setting_slug(setting)
        path = directory / f"{slug}.rkt"
        path.write_text(rule_source(**setting), encoding="utf-8")
        paths[slug] = path
    return paths


def build_episode(
    seed: int, *, parameter: dict[str, str] | None = None
) -> dict[str, Any]:
    """Build one complete episode with a single fixed hidden rule setting."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    chosen = parameter_for_seed(seed) if parameter is None else _validate_setting(**parameter)
    generator = _load_generator()
    pairs = []
    # Valid production inputs already require asymmetric row/column counts, so
    # every pair distinguishes both parameters and all four combined settings.
    source_seed = 10_000 + seed
    for index in range(EPISODE_SIZE):
        grid = generator.generate(
            source_seed,
            200 + index,
            difficulty="medium",
        )
        pairs.append(
            {
                "input": grid,
                "output": python_mirror(grid, **chosen),
            }
        )
    return {
        "schema": "arcpuzzles-parametric-section-axis-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameter": dict(chosen),
        "train": pairs[:3],
        "test": pairs[3:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return a model-visible challenge without hidden settings or query labels."""
    return {
        "schema": "arcpuzzles-parametric-section-axis-public-v1",
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def canonical_parity_python() -> list[dict[str, Any]]:
    """Check that the canonical/default setting preserves every official pair."""
    from reviewer_support import canonical_pairs

    rows = []
    for index, pair in enumerate(canonical_pairs(TASK_ID, root=REPO, labeled_only=True)):
        output = python_mirror(pair["input"], **DEFAULT_PARAMETERS)
        rows.append(
            {
                "pair_index": index,
                "input_shape": [len(pair["input"]), len(pair["input"][0])],
                "expected_output_shape": [
                    len(pair["output"]),
                    len(pair["output"][0]),
                ],
                "mirror_output_shape": [len(output), len(output[0])],
                "matches_canonical_output": output == pair["output"],
                "input_sha256": _grid_sha256(pair["input"]),
                "expected_output_sha256": _grid_sha256(pair["output"]),
                "mirror_output_sha256": _grid_sha256(output),
            }
        )
    return rows


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"'({rows})"


def _install_rule_wrap_namespace() -> None:
    """Expose shared/tools under the staged ``scripts`` package name."""
    import types

    tools_dir = REPO / "shared" / "tools"
    if "scripts" not in sys.modules and tools_dir.is_dir():
        package = types.ModuleType("scripts")
        package.__path__ = [str(tools_dir)]
        sys.modules["scripts"] = package


def racket_apply(bridge: Any, source: str, grid: list[list[int]]) -> list[list[int]]:
    _install_rule_wrap_namespace()
    from puzzle_generators.rule_wrap import wrap_rule

    result = bridge.eval_text(f"({wrap_rule(source)} {_grid_literal(grid)})")
    if not isinstance(result, list) or any(not isinstance(row, list) for row in result):
        raise RuntimeError(f"Racket returned a non-grid value: {result!r}")
    return result


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _choose_cycle_seeds(base_seed: int) -> list[int]:
    if type(base_seed) is not int:
        raise TypeError("base_seed must be an integer (not bool)")
    start = base_seed - (base_seed % 4)
    return [start + index for index in range(4)]


def run_probe(out_dir: Path, *, base_seed: int = 2400) -> dict[str, Any]:
    """Execute all four rule settings and retain source-bound evidence."""
    from arc_repl.racket_bridge import RacketBridge

    out_dir.mkdir(parents=True, exist_ok=False)
    rule_paths = materialize_rules(RULES_DIR)
    CHALLENGES_DIR.mkdir(parents=True, exist_ok=True)
    EPISODES_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    generator_path = TASK_HOME / "generator.py"
    report: dict[str, Any] = {
        "schema": "arcpuzzles-parametric-section-axis-evidence-v1",
        "status": "running",
        "task_id": TASK_ID,
        "prototype_scope": "proposed_not_selected_production_rule",
        "prototype_version": PROTOTYPE_VERSION,
        "parameters": {
            "measure_mode": {
                "allowed_values": list(MEASURE_MODES),
                "canonical_default": DEFAULT_PARAMETERS["measure_mode"],
                "meaning": "count output sections (separator count + 1) or separator lines directly",
            },
            "axis_order": {
                "allowed_values": list(AXIS_ORDERS),
                "canonical_default": DEFAULT_PARAMETERS["axis_order"],
                "meaning": "preserve or transpose row/column count roles in the output shape",
            },
        },
        "selection": "the two-value pair is chosen once as all_parameter_settings()[seed % 4] and reused for all four pairs",
        "input_constraints": "selected production grammar; asymmetric separator counts make all four settings distinguishable",
        "canonical_behavior_preserved_by": dict(DEFAULT_PARAMETERS),
        "prototype_source": str(Path(__file__).relative_to(REPO)),
        "prototype_source_sha256": _sha256_bytes(Path(__file__).read_bytes()),
        "selected_generator": str(generator_path.relative_to(REPO)),
        "selected_generator_sha256": _sha256_bytes(generator_path.read_bytes()),
        "selected_rule_hash": getattr(_load_generator(), "RULE_HASH"),
        "cwd": os.getcwd(),
        "argv": list(sys.argv),
        "episodes": [],
        "limits": [
            "This is bounded prototype evidence, not production or training approval.",
            "The selected generator and canonical Racket authority remain unchanged apart from the separate invalid-index validation repair.",
            "All three alternative settings are refuted on retained pairs; undeclared rule families are not exhausted.",
        ],
    }

    settings = tuple(all_parameter_settings())
    with RacketBridge(max_calls_before_restart=48) as bridge:
        canonical_rows = canonical_parity_python()
        default_source = rule_source(**DEFAULT_PARAMETERS)
        from reviewer_support import canonical_pairs

        canonical_pairs_value = canonical_pairs(TASK_ID, root=REPO, labeled_only=True)
        if len(canonical_rows) != len(canonical_pairs_value):
            raise AssertionError("canonical parity inventory changed during probe")
        for row, pair in zip(canonical_rows, canonical_pairs_value):
            racket_output = racket_apply(bridge, default_source, pair["input"])
            row["racket_output_shape"] = [len(racket_output), len(racket_output[0])]
            row["racket_output_sha256"] = _grid_sha256(racket_output)
            row["racket_matches_canonical_output"] = racket_output == pair["output"]
            if not row["matches_canonical_output"] or not row["racket_matches_canonical_output"]:
                raise AssertionError(f"canonical default mismatch at pair {row['pair_index']}")
        report["canonical_parity"] = {
            "setting": dict(DEFAULT_PARAMETERS),
            "pairs_checked": len(canonical_rows),
            "all_python_match": all(row["matches_canonical_output"] for row in canonical_rows),
            "all_racket_match": all(
                row["racket_matches_canonical_output"] for row in canonical_rows
            ),
            "rows": canonical_rows,
        }

        for episode_index, seed in enumerate(_choose_cycle_seeds(base_seed)):
            chosen = parameter_for_seed(seed)
            expected_setting = settings[episode_index]
            if chosen != expected_setting:
                raise AssertionError((seed, chosen, expected_setting))
            episode = build_episode(seed)
            selected_source = rule_source(**chosen)
            pair_receipts = []
            racket_episode = deepcopy(episode)

            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    selected_output = racket_apply(bridge, selected_source, pair["input"])
                    mirror_output = python_mirror(pair["input"], **chosen)
                    if selected_output != mirror_output:
                        raise AssertionError(
                            f"Racket/Python mismatch seed={seed} {split}[{pair_index}]"
                        )
                    racket_episode[split][pair_index]["output"] = selected_output

                    rival_rows = []
                    for rival in settings:
                        if rival == chosen:
                            continue
                        rival_output = racket_apply(
                            bridge,
                            rule_source(**rival),
                            pair["input"],
                        )
                        rival_rows.append(
                            {
                                "parameter": rival,
                                "output_shape": [len(rival_output), len(rival_output[0])],
                                "output_sha256": _grid_sha256(rival_output),
                                "differs_from_selected": rival_output != selected_output,
                            }
                        )
                    if not all(row["differs_from_selected"] for row in rival_rows):
                        raise AssertionError(
                            f"ambiguous setting seed={seed} {split}[{pair_index}]"
                        )
                    pair_receipts.append(
                        {
                            "split": split,
                            "pair_index": pair_index,
                            "input_shape": [len(pair["input"]), len(pair["input"][0])],
                            "input_sha256": _grid_sha256(pair["input"]),
                            "selected_output_shape": [
                                len(selected_output),
                                len(selected_output[0]),
                            ],
                            "selected_output_sha256": _grid_sha256(selected_output),
                            "rivals": rival_rows,
                        }
                    )

            public = public_challenge(racket_episode)
            public_path = CHALLENGES_DIR / f"challenge_seed_{seed}.json"
            episode_path = EPISODES_DIR / f"episode_seed_{seed}.json"
            _write_json(public_path, public)
            _write_json(episode_path, racket_episode)
            slug = setting_slug(chosen)
            source_path = rule_paths[slug]
            report["episodes"].append(
                {
                    "seed": seed,
                    "parameter": chosen,
                    "is_canonical_default": chosen == DEFAULT_PARAMETERS,
                    "rule_path": str(source_path.relative_to(REPO)),
                    "rule_text": selected_source,
                    "rule_sha256": _sha256_text(selected_source),
                    "private_episode_path": str(episode_path.relative_to(REPO)),
                    "private_episode_sha256": _sha256_bytes(episode_path.read_bytes()),
                    "public_challenge_path": str(public_path.relative_to(REPO)),
                    "public_challenge_sha256": _sha256_bytes(public_path.read_bytes()),
                    "all_labels_from_racket_and_match_python": True,
                    "every_pair_refutes_all_other_settings": True,
                    "pair_receipts": pair_receipts,
                }
            )

    report["status"] = "prototype_pass"
    report["summary"] = {
        "settings_executed": len(report["episodes"]),
        "pairs_executed": sum(len(row["pair_receipts"]) for row in report["episodes"]),
        "rival_comparisons": sum(
            len(pair["rivals"])
            for row in report["episodes"]
            for pair in row["pair_receipts"]
        ),
        "racket_python_mismatches": 0,
        "ambiguous_pair_settings": 0,
    }

    report_path = out_dir / "report.json"
    _write_json(report_path, report)
    manifest = {
        "schema": "arcpuzzles-parametric-workspace-manifest-v1",
        "status": report["status"],
        "task_id": TASK_ID,
        "external_evidence_path": str(report_path),
        "external_evidence_sha256": _sha256_bytes(report_path.read_bytes()),
        "prototype_source_sha256": report["prototype_source_sha256"],
        "selected_generator_sha256": report["selected_generator_sha256"],
        "rule_sources": {
            slug: {
                "path": str(path.relative_to(REPO)),
                "sha256": _sha256_bytes(path.read_bytes()),
            }
            for slug, path in sorted(rule_paths.items())
        },
        "summary": report["summary"],
    }
    _write_json(EVIDENCE_DIR / "manifest.json", manifest)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--base-seed", type=int, default=2400)
    args = parser.parse_args()
    report = run_probe(args.out, base_seed=args.base_seed)
    print(
        json.dumps(
            {
                "status": report["status"],
                "summary": report["summary"],
                "out": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
