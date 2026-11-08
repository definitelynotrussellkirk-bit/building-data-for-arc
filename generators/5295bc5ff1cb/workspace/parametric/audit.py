"""Bounded adversarial self-review for reconstruct-then-mark-span.

This receipt is finite evidence against named direct shortcuts. It does not
replace native qualification, protected-Racket execution, owner acceptance, or
training admission.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

HERE = Path(__file__).resolve().parent
TASK_ID = "5295bc5ff1cb"
SEEDS = tuple(range(32))
DEMO_COUNTS = (2, 3, 6)
QUERIES = 4


def _load(filename: str) -> ModuleType:
    path = (HERE / filename).resolve()
    if path.parent != HERE or path.is_symlink() or not path.is_file():
        raise ValueError(f"missing regular adjacent source: {filename}")
    name = "_audit_5295_" + path.stem + "_" + hashlib.sha256(path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _facts(grid: list[list[int]]) -> dict[str, int]:
    cover = grid[-1][-1]
    top_h = next(r for r in range(len(grid)) if grid[r][0] == cover)
    prefix_width = next(c for c in range(len(grid[0])) if grid[0][c] == cover)
    prefix = grid[0][:prefix_width]
    col_period = next(
        p for p in range(1, len(prefix) + 1)
        if all(value == prefix[i % p] for i, value in enumerate(prefix))
    )
    row_period = next(
        p for p in range(1, top_h + 1)
        if all(grid[r][c] == grid[r % p][c] for r in range(top_h) for c in range(col_period))
    )
    return {
        "cover": cover,
        "top_h": top_h,
        "prefix_width": prefix_width,
        "row_period": row_period,
        "col_period": col_period,
    }


def _tile(grid: list[list[int]], shift: int) -> list[list[int]]:
    info = _facts(grid)
    return [
        [grid[r % info["row_period"]][(c + shift) % info["col_period"]] for c in range(len(grid[0]))]
        for r in range(len(grid))
    ]


def _replace(grid: list[list[int]], old: int, new: int) -> list[list[int]]:
    return [[new if value == old else value for value in row] for row in grid]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict[str, object]:
    adapter = _load("adapter.py")
    family = _load("family.py")
    rival_survivors = Counter({name: 0 for name in (
        "tile_only", "no_shift", "visible_only", "most_frequent_visible", "fixed_lowest_visible"
    )})
    spanning_colors: set[int] = set()
    episodes = 0
    generated_pairs = 0
    stress_30 = 0

    for seed in SEEDS:
        for demos in DEMO_COUNTS:
            plain = adapter.generate(seed, {"mode": "tile_only"}, demos, QUERIES)
            marked = adapter.generate(seed, {"mode": "tile_then_mark_span"}, demos, QUERIES)
            left = [*plain["train"], *plain["test"]]
            right = [*marked["train"], *marked["test"]]
            assert [pair["input"] for pair in left] == [pair["input"] for pair in right]
            assert len({json.dumps(pair["input"], separators=(",", ":")) for pair in left}) == demos + QUERIES
            assert all(a["output"] != b["output"] for a, b in zip(left, right, strict=True))
            assert any(len(pair["input"]) == len(pair["input"][0]) == 30 for pair in plain["test"])
            stress_30 += sum(len(pair["input"]) == len(pair["input"][0]) == 30 for pair in plain["test"])

            episode_ok = {name: True for name in rival_survivors}
            for pair in marked["train"]:
                grid, target = pair["input"], pair["output"]
                info = _facts(grid)
                stage_a = _tile(grid, 1)
                analysis = family.analyze(grid)
                spanning_colors.add(int(analysis["spanning_color"]))
                assert info["cover"] not in {value for row in stage_a for value in row}
                visible_only = [row[:] for row in grid]
                for r in range(info["top_h"]):
                    for c in range(info["prefix_width"]):
                        visible_only[r][c] = stage_a[r][c]
                visible_counts = Counter(
                    grid[r][c]
                    for r in range(info["top_h"])
                    for c in range(info["prefix_width"])
                )
                most = visible_counts.most_common(1)[0][0]
                lowest = min(visible_counts)
                rivals = {
                    "tile_only": stage_a,
                    "no_shift": _tile(grid, 0),
                    "visible_only": visible_only,
                    "most_frequent_visible": _replace(stage_a, most, info["cover"]),
                    "fixed_lowest_visible": _replace(stage_a, lowest, info["cover"]),
                }
                for name, output in rivals.items():
                    episode_ok[name] &= output == target
            for name, survived in episode_ok.items():
                rival_survivors[name] += int(survived)
            episodes += 1
            generated_pairs += 2 * (demos + QUERIES)

    assert all(count == 0 for count in rival_survivors.values())
    assert len(spanning_colors) >= 4
    return {
        "schema": "arcpuzzles-parametric-self-review-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "scope": {
            "seeds": list(SEEDS),
            "demo_counts": list(DEMO_COUNTS),
            "queries": QUERIES,
            "episodes_per_setting_pair": episodes,
            "generated_labeled_pairs": generated_pairs,
            "thirty_by_thirty_queries": stress_30,
        },
        "settings": ["tile_only", "tile_then_mark_span"],
        "spanning_colors": sorted(spanning_colors),
        "named_rivals": {
            name: {"demo_episodes_survived": count}
            for name, count in sorted(rival_survivors.items())
        },
        "source_sha256": {
            name: _sha256(HERE / name)
            for name in ("adapter.py", "family.py", "canonical.rkt", "mark_spanning.rkt", "promotion.json")
        },
        "limits": [
            "Finite deterministic seeds and named rivals only; this is not universal uniqueness evidence.",
            "Python mirror labels are checked here; protected-Racket labels are established separately by native qualification.",
            "This receipt does not grant owner acceptance or training admission.",
        ],
    }


def main() -> int:
    report = audit()
    out = HERE / "evidence" / "current" / "self-review.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = out.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(out)
    print(json.dumps({"status": report["status"], "path": str(out), "episodes": report["scope"]["episodes_per_setting_pair"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
