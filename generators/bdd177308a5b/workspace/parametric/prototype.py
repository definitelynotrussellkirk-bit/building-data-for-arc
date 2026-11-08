#!/usr/bin/env python3
"""Proposed match-relation parameter for bdd177308a5b.

This is a task-local authoring prototype, not a production generator change.
The parameter is selected once per episode and every retained label, rival
prediction, and canonical replay is executed by the bundled Racket runtime.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import shutil
from pathlib import Path
from typing import Iterable

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "bdd177308a5b"
VERSION = "proposed-match-relation-v1"
ALLOWED_MATCH_RELATIONS = ("exact", "quarter_turn_cw")
DEFAULT_MATCH_RELATION = "exact"
CANONICAL_RULE_HASH = "5b8904c8dace"
CANONICAL_SHA256 = "e0a2e834b234bf23ab2e3317a8659ecd2b264876b0eb4dcc5999f6fecbe97271"
CANONICAL_COMPARISON = "(equal? o-norm t-norm)"
ALTERNATIVE_COMPARISON = """(equal? o-norm (let* ((rotated (map (lambda (p) (list (second p) (- 0 (first p)))) t-norm)) (rot-rmin (min-of first rotated)) (rot-cmin (min-of second rotated))) (sort (map (lambda (p) (list (- (first p) rot-rmin) (- (second p) rot-cmin))) rotated) (lambda (a b) (if (= (first a) (first b)) (< (second a) (second b)) (< (first a) (first b)))))))"""

_CUE_CELLS = frozenset({(3, c) for c in range(4)} | {(r, 3) for r in range(4)})
_L3 = ((0, 0), (1, 0), (1, 1))
_T4 = ((0, 0), (0, 1), (0, 2), (1, 1))
_L4 = ((0, 0), (1, 0), (2, 0), (2, 1))
_ZIG5 = ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2))
_TEMPLATE_FIXTURES = (
    ("l_triomino", _L3, ((0, 0), (0, 1), (1, 0), (1, 1))),
    ("t_tetromino", _T4, ((0, 0), (0, 1), (0, 2))),
    ("l_tetromino", _L4, ((0, 0), (0, 1), (0, 2))),
    ("zig_pentomino", _ZIG5, ((0, 0), (0, 1), (0, 2))),
)

Shape = tuple[tuple[int, int], ...]


def _sha256(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def grid_sha256(grid) -> str:
    return _sha256(_json(normalize_grid(grid)))


def _validate_seed(seed) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1")


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CANONICAL_COMPARISON) != 1:
        raise ValueError("canonical source must contain exactly one match comparison")
    return source


def canonical_source(*, root=None) -> str:
    root = find_root(__file__) if root is None else Path(root)
    sources = set()
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


def materialize_rule(
    match_relation=DEFAULT_MATCH_RELATION, *, root=None, source=None
) -> str:
    if type(match_relation) is not str or match_relation not in ALLOWED_MATCH_RELATIONS:
        raise ValueError(
            "match_relation must be 'exact' or 'quarter_turn_cw'"
        )
    canonical = (
        canonical_source(root=root)
        if source is None
        else _check_canonical_source(source)
    )
    if match_relation == DEFAULT_MATCH_RELATION:
        return canonical
    alternative = canonical.replace(
        CANONICAL_COMPARISON,
        ALTERNATIVE_COMPARISON,
        1,
    )
    if alternative.count(ALTERNATIVE_COMPARISON) != 1:
        raise ValueError("failed to materialize one guarded relation change")
    return alternative


def rule_callable(source: str) -> str:
    if not isinstance(source, str):
        raise ValueError("Racket source must be text")
    restored = source.replace(
        ALTERNATIVE_COMPARISON,
        CANONICAL_COMPARISON,
        1,
    )
    _check_canonical_source(restored)
    if not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    return source[len("(rule! ") : -1]


def execute_rule(source: str, grid, *, bridge=None):
    grid = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    points = tuple(cells)
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _quarter_turn_cw(shape: Shape) -> Shape:
    return _normalize((c, -r) for r, c in shape)


def _paint(grid: list[list[int]], shape: Shape, row: int, col: int, color: int) -> None:
    for dr, dc in shape:
        rr, cc = row + dr, col + dc
        if not (0 <= rr < len(grid) and 0 <= cc < len(grid[0])):
            raise ValueError("fixture shape falls outside the grid")
        if grid[rr][cc] != 0:
            raise ValueError("fixture shapes overlap")
        grid[rr][cc] = color


def _fixture(fixture_id: str, template: Shape, decoy: Shape, *, colour_shift: int):
    template = _normalize(template)
    rotated = _quarter_turn_cw(template)
    if rotated == template:
        raise ValueError("fixtures require a quarter-turn-sensitive template")
    grid = [[0] * 10 for _ in range(10)]
    for row, col in _CUE_CELLS:
        grid[row][col] = 5
    palette = tuple(((base + colour_shift - 1) % 9) + 1 for base in (1, 2, 4, 7))
    if 5 in palette or len(set(palette)) != 4:
        # Fixed shifts below never hit this branch; fail rather than silently
        # reusing a role colour in a future fixture edit.
        raise ValueError("fixture colour shift produced an invalid role palette")
    template_color, exact_color, rotated_color, decoy_color = palette
    _paint(grid, template, 0, 0, template_color)
    _paint(grid, template, 0, 6, exact_color)
    _paint(grid, rotated, 6, 0, rotated_color)
    _paint(grid, _normalize(decoy), 6, 6, decoy_color)
    return {
        "fixture_id": fixture_id,
        "input": grid,
        "roles": {
            "template_shape": [list(p) for p in template],
            "exact_candidate_shape": [list(p) for p in template],
            "quarter_turn_candidate_shape": [list(p) for p in rotated],
        },
    }


def fixtures():
    """Four lawful inputs that distinguish exact from clockwise-quarter-turn matching."""
    # Colour shifts are zero intentionally: role geometry, not palette, is the
    # varied parameter. Distinct shapes make all four fixtures independent.
    return [
        _fixture(fixture_id, shape, decoy, colour_shift=0)
        for fixture_id, shape, decoy in _TEMPLATE_FIXTURES
    ]


def parameters_for_seed(seed: int) -> dict[str, str]:
    _validate_seed(seed)
    return {
        "match_relation": random.Random(seed).choice(ALLOWED_MATCH_RELATIONS)
    }


def _make_episode(seed: int, *, root: Path, bridge: RacketBridge):
    rng = random.Random(seed)
    relation = rng.choice(ALLOWED_MATCH_RELATIONS)
    authored = copy.deepcopy(fixtures())
    rng.shuffle(authored)
    selected_source = materialize_rule(relation, root=root)
    rival_relation = next(
        value for value in ALLOWED_MATCH_RELATIONS if value != relation
    )
    rival_source = materialize_rule(rival_relation, root=root)

    labeled = []
    rival_outputs = []
    for fixture in authored:
        grid = fixture["input"]
        labeled.append(
            {
                "fixture_id": fixture["fixture_id"],
                "input": copy.deepcopy(grid),
                "output": execute_rule(selected_source, grid, bridge=bridge),
            }
        )
        rival_outputs.append(execute_rule(rival_source, grid, bridge=bridge))

    train = labeled[:3]
    test = labeled[3:]
    demonstration_mismatches = [
        index
        for index, pair in enumerate(train)
        if pair["output"] != rival_outputs[index]
    ]
    query_mismatches = [
        index
        for index, pair in enumerate(test)
        if pair["output"] != rival_outputs[len(train) + index]
    ]
    ambiguities = []
    if demonstration_mismatches != list(range(len(train))):
        ambiguities.append(
            "the other declared relation was not refuted by every demonstration"
        )
    if query_mismatches != list(range(len(test))):
        ambiguities.append("the declared relations agree on a retained query")

    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": {"match_relation": relation},
        "parameter_selected_once": True,
        "input_constraints_depend_on_parameter": False,
        "racket_source": selected_source,
        "racket_sha256": _sha256(selected_source),
        "train": train,
        "test": test,
        "parameter_rivals": [
            {
                "match_relation": rival_relation,
                "racket_sha256": _sha256(rival_source),
                "status": (
                    "refuted_by_demonstrations"
                    if demonstration_mismatches
                    else "fits_all_demonstrations"
                ),
                "demonstration_mismatch_indices": demonstration_mismatches,
                "query_mismatch_indices": query_mismatches,
            }
        ],
        "ambiguities": ambiguities,
    }


def make_episode(seed: int, *, root=None, bridge=None):
    _validate_seed(seed)
    root = find_root(__file__) if root is None else Path(root)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(seed, root=root, bridge=owned)
    return _make_episode(seed, root=root, bridge=bridge)


def public_challenge(episode):
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


def _canonical_replay(*, root: Path, bridge: RacketBridge):
    source = canonical_source(root=root)
    rows = []
    for pair in canonical_pairs(TASK_ID, root=root):
        actual = execute_rule(source, pair["input"], bridge=bridge)
        if actual != pair["output"]:
            raise AssertionError(
                f"canonical replay mismatch at variant={pair['variant']} "
                f"split={pair['split']} pair={pair['pair_index']}"
            )
        rows.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input_sha256": grid_sha256(pair["input"]),
                "output_sha256": grid_sha256(actual),
            }
        )
    return {
        "status": "pass",
        "pairs_checked": len(rows),
        "canonical_source_sha256": _sha256(source),
        "pairs": rows,
    }


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _files_manifest(root: Path):
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in {"report.json", "failure.json"}:
            continue
        body = path.read_bytes()
        rows.append(
            {"path": relative, "bytes": len(body), "sha256": _sha256(body)}
        )
    return rows


def write_evidence(seeds, *, out, root=None):
    seeds = tuple(seeds)
    if not seeds:
        raise ValueError("at least one seed is required")
    for seed in seeds:
        _validate_seed(seed)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__) if root is None else Path(root)
    try:
        with RacketBridge() as bridge:
            replay = _canonical_replay(root=root, bridge=bridge)
            episodes = [
                make_episode(seed, root=root, bridge=bridge) for seed in seeds
            ]

        private = out / "private"
        public = out / "public"
        rules = private / "rules"
        snapshots = private / "source_snapshot"
        rules.mkdir(parents=True)
        public.mkdir(parents=True)
        snapshots.mkdir(parents=True)

        _write_json(private / "canonical_replay.json", replay)
        for relation in ALLOWED_MATCH_RELATIONS:
            (rules / f"{relation}.rkt").write_text(
                materialize_rule(relation, root=root), encoding="utf-8"
            )

        episode_rows = []
        ambiguous = 0
        for index, episode in enumerate(episodes):
            relation = episode["parameters"]["match_relation"]
            private_path = private / f"episode-{index:03d}.json"
            public_path = public / f"episode-{index:03d}.json"
            saved = copy.deepcopy(episode)
            saved["racket_path"] = f"private/rules/{relation}.rkt"
            _write_json(private_path, saved)
            _write_json(public_path, public_challenge(episode))
            ambiguous += len(episode["ambiguities"])
            episode_rows.append(
                {
                    "seed": episode["seed"],
                    "match_relation": relation,
                    "racket_sha256": episode["racket_sha256"],
                    "public_path": public_path.relative_to(out).as_posix(),
                    "private_path": private_path.relative_to(out).as_posix(),
                    "ambiguities": len(episode["ambiguities"]),
                }
            )

        source_path = Path(__file__).resolve()
        test_path = source_path.parents[2] / "tests" / "test_parametric_variant.py"
        shutil.copy2(source_path, snapshots / source_path.name)
        shutil.copy2(test_path, snapshots / test_path.name)

        covered = {row["match_relation"] for row in episode_rows}
        report = {
            "schema": "arcpuzzles-proposed-parametric-evidence-v1",
            "task_id": TASK_ID,
            "prototype_version": VERSION,
            "status": "proposed_unapproved",
            "approved": False,
            "canonical_rule_hash": CANONICAL_RULE_HASH,
            "canonical_source_sha256": CANONICAL_SHA256,
            "prototype_sha256": _sha256(source_path.read_bytes()),
            "parameter": {
                "name": "match_relation",
                "allowed_values": list(ALLOWED_MATCH_RELATIONS),
                "original_default": DEFAULT_MATCH_RELATION,
                "selected_once_per_episode": True,
                "input_constraints_depend_on_parameter": False,
            },
            "episodes": episode_rows,
            "counts": {
                "episodes": len(episodes),
                "settings_covered": len(covered),
                "demonstrations": 3 * len(episodes),
                "queries": len(episodes),
                "ambiguous_parameter_rivals": ambiguous,
                "canonical_pairs_checked": replay["pairs_checked"],
                "racket_rule_applications": replay["pairs_checked"] + 8 * len(episodes),
            },
            "limits": [
                "finite evidence for two declared relation settings and retained seeds",
                "four authored fixtures are not a replacement production distribution",
                "refuting the declared rival does not prove universal rule identifiability",
                "prototype status does not change canonical approval or production APIs",
            ],
        }
        report["files"] = _files_manifest(out)
        _write_json(out / "report.json", report)
        return report
    except Exception as exc:
        _write_json(
            out / "failure.json",
            {
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "seeds": list(seeds),
            },
        )
        raise


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(args.seeds, out=args.out)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
