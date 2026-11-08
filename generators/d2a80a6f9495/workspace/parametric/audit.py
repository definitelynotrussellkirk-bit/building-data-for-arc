"""Finite learnability audit for the d2a80a6f9495 swap-scope family."""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("swap_scope_audit_prototype", _HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling swap-scope prototype")
P = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(P)

Grid = list[list[int]]
Rule = Callable[[Grid], Grid]


def _apply_selected(grid: Grid, selected: set[tuple[int, int]]) -> Grid:
    result = [row[:] for row in grid]
    for row in P.object_facts(grid)["two_color_objects"]:
        pair = tuple(row["pair"])
        if pair not in selected:
            continue
        a, b = pair
        for r, c in row["cells"]:
            result[r][c] = b if grid[r][c] == a else a
    return result


def _pairs_and_counts(grid: Grid):
    facts = P.object_facts(grid)
    pairs = [tuple(row["pair"]) for row in facts["two_color_objects"]]
    return pairs, Counter(pairs), facts


def _unique_only(grid: Grid) -> Grid:
    pairs, counts, _ = _pairs_and_counts(grid)
    return _apply_selected(grid, {pair for pair in pairs if counts[pair] == 1})


def _most_frequent(grid: Grid) -> Grid:
    pairs, counts, _ = _pairs_and_counts(grid)
    maximum = max(counts.values())
    return _apply_selected(grid, {pair for pair in pairs if counts[pair] == maximum})


def _least_numeric_pair(grid: Grid) -> Grid:
    pairs, _, _ = _pairs_and_counts(grid)
    return _apply_selected(grid, {min(set(pairs))})


def _first_pair(grid: Grid) -> Grid:
    _, _, facts = _pairs_and_counts(grid)
    ordered = sorted(facts["two_color_objects"], key=lambda row: (row["bbox"][0], row["bbox"][1]))
    return _apply_selected(grid, {tuple(ordered[0]["pair"])})


def _exactly_two(grid: Grid) -> Grid:
    pairs, counts, _ = _pairs_and_counts(grid)
    return _apply_selected(grid, {pair for pair in pairs if counts[pair] == 2})


def _largest_objects(grid: Grid) -> Grid:
    facts = P.object_facts(grid)
    maximum = max(row["size"] for row in facts["two_color_objects"])
    result = [row[:] for row in grid]
    for row in facts["two_color_objects"]:
        if row["size"] != maximum:
            continue
        a, b = row["pair"]
        for r, c in row["cells"]:
            result[r][c] = b if grid[r][c] == a else a
    return result


def _pair_with_lowest_color(grid: Grid) -> Grid:
    pairs, _, _ = _pairs_and_counts(grid)
    low = min(min(pair) for pair in pairs)
    return _apply_selected(grid, {pair for pair in pairs if low in pair})


def _repeated_shape(grid: Grid) -> Grid:
    facts = P.object_facts(grid)
    signatures = [
        tuple(sorted((r - row["bbox"][0], c - row["bbox"][1]) for r, c in row["cells"]))
        for row in facts["two_color_objects"]
    ]
    counts = Counter(signatures)
    result = [row[:] for row in grid]
    for row, signature in zip(facts["two_color_objects"], signatures):
        if counts[signature] <= 1:
            continue
        a, b = row["pair"]
        for r, c in row["cells"]:
            result[r][c] = b if grid[r][c] == a else a
    return result


def rivals() -> dict[str, Rule]:
    return {
        "always all two-color": lambda grid: P.apply_scope(grid, "all_two_color"),
        "always repeated pairs": lambda grid: P.apply_scope(grid, "repeated_pair"),
        "identity": lambda grid: [row[:] for row in grid],
        "unique pairs only": _unique_only,
        "most frequent pair only": _most_frequent,
        "least numeric pair only": _least_numeric_pair,
        "first pair in reading order only": _first_pair,
        "pairs occurring exactly twice": _exactly_two,
        "largest two-color objects only": _largest_objects,
        "pairs containing the lowest color": _pair_with_lowest_color,
        "repeated geometric shapes": _repeated_shape,
    }


def _scene_errors(grid: Grid) -> list[str]:
    try:
        facts = P.object_facts(grid)
    except Exception as exc:
        return [f"{type(exc).__name__}: {exc}"]
    counts = sorted(facts["pair_counts"].values(), reverse=True)
    errors = []
    if len(counts) < 3 or sum(value > 1 for value in counts) < 2 or 1 not in counts:
        errors.append(f"missing two repeated classes plus unique class: {counts}")
    if facts["negative_object_count"] < 2:
        errors.append("missing negative controls")
    return errors


def run_audit(*, seeds=(0, 17), demo_counts=(2, 3, 6), queries=4) -> dict[str, Any]:
    named = rivals()
    harmful: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    survivor_counts = {name: 0 for name in named}
    episodes = 0
    queries_checked = 0

    for selected in P.SCOPES:
        for seed in seeds:
            for demos in demo_counts:
                episode = P.generate_episode(seed, selected, demos, queries)
                episodes += 1
                queries_checked += len(episode["test"])
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        errors = _scene_errors(pair["input"])
                        if errors:
                            failures.append({
                                "setting": selected,
                                "seed": seed,
                                "demos": demos,
                                "split": split,
                                "index": index,
                                "errors": errors,
                            })
                for name, rule in named.items():
                    try:
                        survives = all(rule(pair["input"]) == pair["output"] for pair in episode["train"])
                    except Exception as exc:
                        survives = False
                        failures.append({
                            "setting": selected,
                            "seed": seed,
                            "demos": demos,
                            "rival": name,
                            "error": f"{type(exc).__name__}: {exc}",
                        })
                    if not survives:
                        continue
                    survivor_counts[name] += 1
                    for query_index, pair in enumerate(episode["test"]):
                        rival_output = rule(pair["input"])
                        if rival_output != pair["output"]:
                            harmful.append({
                                "setting": selected,
                                "seed": seed,
                                "demos": demos,
                                "query_index": query_index,
                                "rival": name,
                                "input": pair["input"],
                                "intended_output": pair["output"],
                                "rival_output": rival_output,
                            })
                            break

    return {
        "schema": "arcpuzzles-parametric-swap-scope-audit-v1",
        "task_id": P.TASK_ID,
        "settings_checked": list(P.SCOPES),
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "queries_per_episode": queries,
        "episodes": episodes,
        "queries_checked": queries_checked,
        "rival_names": list(named),
        "survivor_counts": survivor_counts,
        "harmful_survivors": harmful,
        "input_failures": failures,
        "scope": "Finite source-bound audit against named executable Python rivals; intended labels are separately protected-Racket qualified.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_audit()
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
