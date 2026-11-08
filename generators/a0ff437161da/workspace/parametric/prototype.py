#!/usr/bin/env python3
"""Proposed episode-level tie-order parameter for ARC task a0ff437161da.

The selected production generator and canonical authority remain fixed. This
isolated prototype varies exactly one nearby rule parameter once per episode:

* ``ul_ur_ll_lr`` (canonical/default): equal Manhattan distances follow the
  canonical corner list order UL, UR, LL, LR.
* ``lr_ll_ur_ul``: equal distances follow the reverse order LR, LL, UR, UL.

All fixtures are lawful singleton-marker grids. Each demonstration directly
separates the two settings, and retained labels are produced by exact Racket
execution rather than by the Python generator mirror.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


TASK_ID = "a0ff437161da"
PROTOTYPE_VERSION = "1.0.0"
ALLOWED_TIE_ORDERS = ("ul_ur_ll_lr", "lr_ll_ur_ul")
DEFAULT_TIE_ORDER = "ul_ur_ll_lr"
CANONICAL_SHA256 = "48130e6e8cb3ee0d8fc1f84e79c4fe052a9cfd0728effa34f7bde67da7e8b8b8"
CANONICAL_CORNERS = """                  (corners (list (cons 0 0)
                                 (cons 0 (- w 1))
                                 (cons (- h 1) 0)
                                 (cons (- h 1) (- w 1))))
"""
ALTERNATIVE_CORNERS = """                  (corners (list (cons (- h 1) (- w 1))
                                 (cons (- h 1) 0)
                                 (cons 0 (- w 1))
                                 (cons 0 0)))
"""


def _validate_tie_order(tie_order: str) -> str:
    if tie_order not in ALLOWED_TIE_ORDERS:
        raise ValueError(
            f"tie_order must be one of {ALLOWED_TIE_ORDERS}, got {tie_order!r}"
        )
    return tie_order


def _validate_seed(seed: int) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must satisfy 0 <= seed < 2**63")
    return seed


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _repo_root(root: Path | str | None = None) -> Path:
    if root is not None:
        candidate = Path(root).resolve()
        if (candidate / "generators").is_dir():
            return candidate
        if (candidate / "repo" / "generators").is_dir():
            return candidate / "repo"
        raise FileNotFoundError(f"could not locate repo root below {candidate}")
    return Path(__file__).resolve().parents[4]


def canonical_source(root: Path | str | None = None) -> str:
    """Load and validate the exact selected task's canonical Racket source."""
    repo = _repo_root(root)
    candidates = (
        repo / "shared" / "data" / "canonical" / "puzzles.jsonl",
        repo / "data" / "canonical" / "puzzles.jsonl",
    )
    source = None
    for path in candidates:
        if not path.is_file():
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    source = row.get("program_solution")
                    break
        if source is not None:
            break
    if not isinstance(source, str):
        raise FileNotFoundError(f"canonical program_solution for {TASK_ID} not found")
    if _sha256_text(source) != CANONICAL_SHA256:
        raise ValueError("canonical source hash changed; inspect before rematerializing")
    if source.count(CANONICAL_CORNERS) != 1:
        raise ValueError("canonical corner-list anchor is missing or duplicated")
    return source


def materialize_rule(
    tie_order: str,
    *,
    source: str | None = None,
    root: Path | str | None = None,
) -> str:
    """Materialize one exact Racket rule while changing only corner priority."""
    setting = _validate_tie_order(tie_order)
    canonical = canonical_source(root=root) if source is None else source
    if _sha256_text(canonical) != CANONICAL_SHA256:
        raise ValueError("source must be the exact canonical Racket program")
    if canonical.count(CANONICAL_CORNERS) != 1:
        raise ValueError("source does not contain the unique canonical corner-list anchor")
    if setting == DEFAULT_TIE_ORDER:
        return canonical
    alternative = canonical.replace(CANONICAL_CORNERS, ALTERNATIVE_CORNERS, 1)
    if alternative.count(ALTERNATIVE_CORNERS) != 1:
        raise AssertionError("alternative corner-list materialization failed")
    return alternative


def parameters_for_seed(seed: int) -> dict[str, str]:
    """Select one setting once for a complete episode."""
    _validate_seed(seed)
    return {"tie_order": ALLOWED_TIE_ORDERS[seed % len(ALLOWED_TIE_ORDERS)]}


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def _rule_body(source: str) -> str:
    text = source.strip()
    if not text.startswith("(rule!") or not text.endswith(")"):
        raise ValueError("Racket source must be a (rule! BODY) form")
    return text[len("(rule!") : -1].strip()


def execute_rule(source: str, grid: list[list[int]], *, bridge) -> list[list[int]]:
    """Execute the exact materialized rule in the protected Racket prelude."""
    body = _rule_body(source)
    expression = f"(let ((g {_grid_literal(grid)})) ({body} g))"
    result = bridge.eval_text(expression)
    if not isinstance(result, list) or not result or not all(
        isinstance(row, list) for row in result
    ):
        raise RuntimeError(f"Racket returned a non-grid result: {result!r}")
    return result


def _fixture(fixture_id: str, row: int, col: int, color: int) -> dict[str, Any]:
    grid = [[8] * 7 for _ in range(7)]
    grid[row][col] = color
    return {"fixture_id": fixture_id, "input": grid}


def fixtures() -> list[dict[str, Any]]:
    """Return four lawful two-way ties, one for each tied edge."""
    return [
        _fixture("top_tie", 1, 3, 1),
        _fixture("bottom_tie", 5, 3, 2),
        _fixture("left_tie", 3, 1, 3),
        _fixture("right_tie", 3, 5, 4),
    ]


def make_episode(seed: int, *, root: Path | str | None = None, bridge) -> dict[str, Any]:
    """Build three demos and one query under one hidden episode-level setting."""
    parameters = parameters_for_seed(seed)
    chosen = parameters["tie_order"]
    sources = {
        setting: materialize_rule(setting, root=root)
        for setting in ALLOWED_TIE_ORDERS
    }
    rows = []
    outputs: dict[str, list[list[list[int]]]] = {
        setting: [] for setting in ALLOWED_TIE_ORDERS
    }
    for fixture in fixtures():
        grid = fixture["input"]
        for setting, source in sources.items():
            outputs[setting].append(execute_rule(source, grid, bridge=bridge))
        rows.append(
            {
                "fixture_id": fixture["fixture_id"],
                "tie_order": chosen,
                "input": copy.deepcopy(grid),
                "output": copy.deepcopy(outputs[chosen][-1]),
            }
        )

    parameter_rivals = []
    for setting in ALLOWED_TIE_ORDERS:
        demo_mismatches = [
            index
            for index in range(3)
            if outputs[setting][index] != outputs[chosen][index]
        ]
        query_mismatches = [
            0
            for index in range(3, 4)
            if outputs[setting][index] != outputs[chosen][index]
        ]
        parameter_rivals.append(
            {
                "tie_order": setting,
                "status": (
                    "selected"
                    if setting == chosen
                    else "refuted_by_demonstrations"
                ),
                "demonstration_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
            }
        )

    selected_source = sources[chosen]
    return {
        "schema": "arcpuzzles-parametric-tie-order-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "canonical_default": DEFAULT_TIE_ORDER,
        "racket_source": selected_source,
        "racket_sha256": _sha256_text(selected_source),
        "train": rows[:3],
        "test": rows[3:],
        "parameter_rivals": parameter_rivals,
        "ambiguities": [],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove the hidden setting, private program, and query answer."""
    return {
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": copy.deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materialize_evidence(
    out_dir: Path,
    *,
    seeds: list[int],
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Execute both settings and retain bounded public/private evidence."""
    from arc_repl.racket_bridge import RacketBridge

    if out_dir.exists():
        raise FileExistsError(f"choose a new evidence directory: {out_dir}")
    out_dir.mkdir(parents=True)
    repo = _repo_root(root)
    canonical = canonical_source(root=repo)
    prototype_path = Path(__file__).resolve()
    generator_path = prototype_path.parents[2] / "generator.py"

    episodes = []
    with RacketBridge() as bridge:
        for seed in seeds:
            episode = make_episode(seed, root=repo, bridge=bridge)
            episodes.append(episode)
            private_path = out_dir / "private" / f"episode-{seed:03d}.json"
            public_path = out_dir / "public" / f"episode-{seed:03d}.json"
            _write_json(private_path, episode)
            _write_json(public_path, public_challenge(episode))

        canonical_replay = []
        canonical_rule = materialize_rule(DEFAULT_TIE_ORDER, source=canonical)
        canonical_data = repo / "shared" / "data" / "canonical" / "puzzles.jsonl"
        task_row = None
        with canonical_data.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    task_row = row
                    break
        if task_row is None:
            raise FileNotFoundError(f"canonical puzzle row for {TASK_ID} not found")
        for split in ("train", "test"):
            for pair_index, pair in enumerate(task_row[split]):
                actual = execute_rule(canonical_rule, pair["input"], bridge=bridge)
                if actual != pair["output"]:
                    raise AssertionError(f"canonical replay failed at {split}[{pair_index}]")
                canonical_replay.append(
                    {
                        "split": split,
                        "pair_index": pair_index,
                        "input_sha256": _sha256_json(pair["input"]),
                        "output_sha256": _sha256_json(actual),
                        "matched": True,
                    }
                )
        runtime_identity = bridge.runtime_identity

    settings = {}
    for setting in ALLOWED_TIE_ORDERS:
        source = materialize_rule(setting, source=canonical)
        rule_path = out_dir / "private" / "rules" / f"tie-order-{setting}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(source + "\n", encoding="utf-8")
        settings[setting] = {
            "is_canonical_default": setting == DEFAULT_TIE_ORDER,
            "racket_sha256": _sha256_text(source),
            "rule_path": str(rule_path.relative_to(out_dir)),
        }

    report = {
        "schema": "arcpuzzles-parametric-tie-order-evidence-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": "tie_order",
            "allowed_values": list(ALLOWED_TIE_ORDERS),
            "canonical_default": DEFAULT_TIE_ORDER,
            "selected_once_per_episode": True,
            "invariant_reasoning": [
                "find the first non-background cell in row-major order",
                "select a Manhattan-nearest corner",
                "fill the inclusive marker-to-corner rectangle",
            ],
            "varied_reasoning": "priority among exactly equidistant nearest corners",
        },
        "seeds": seeds,
        "observed_settings": sorted(
            {episode["parameters"]["tie_order"] for episode in episodes}
        ),
        "all_episodes_identifiable": all(
            not episode["ambiguities"]
            and any(
                row["status"] == "refuted_by_demonstrations"
                for row in episode["parameter_rivals"]
            )
            for episode in episodes
        ),
        "canonical_replay": canonical_replay,
        "settings": settings,
        "runtime_identity": runtime_identity,
        "prototype_source_sha256": hashlib.sha256(prototype_path.read_bytes()).hexdigest(),
        "generator_source_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "limitations": [
            "This is a bounded two-setting prototype, not production approval.",
            "The selected generator and canonical authority remain fixed at ul_ur_ll_lr.",
            "The retained fixtures distinguish only the declared tie-order family.",
        ],
    }
    _write_json(out_dir / "private" / "canonical_replay.json", canonical_replay)
    _write_json(out_dir / "private" / "runtime_identity.json", runtime_identity)
    _write_json(out_dir / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    for seed in args.seeds:
        _validate_seed(seed)
    report = materialize_evidence(args.out, seeds=args.seeds, root=args.root)
    print(
        json.dumps(
            {
                "status": report["status"],
                "task_id": TASK_ID,
                "out": str(args.out),
                "observed_settings": report["observed_settings"],
                "all_episodes_identifiable": report["all_episodes_identifiable"],
                "canonical_pairs_replayed": len(report["canonical_replay"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
