"""Run a bounded protected-Racket study for the halo family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import evaluate_contract


HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK_ID = "7e826540d45d"


def _load_adapter():
    path = HOME / "adapter.py"
    spec = importlib.util.spec_from_file_location("_halo_probe_adapter", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _expand_color(impl, grid, selected):
    intermediate = impl.one_ring_halo(grid)
    h, w = len(intermediate), len(intermediate[0])
    out = [row[:] for row in intermediate]
    for r in range(h):
        for c in range(w):
            if intermediate[r][c] != selected:
                continue
            for dr, dc in impl.CARDINAL:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and intermediate[nr][nc] == 0:
                    out[nr][nc] = selected
    return out


def _widest_object_shortcut(impl, grid):
    color, _cells = max(
        impl._components(grid),
        key=lambda item: (
            max(c for _r, c in item[1]) - min(c for _r, c in item[1]) + 1,
            -len(item[1]),
            -item[0],
        ),
    )
    return _expand_color(impl, grid, color)


def _bottommost_object_shortcut(impl, grid):
    color, _cells = max(
        impl._components(grid),
        key=lambda item: (
            sum(r for r, _c in item[1]) / len(item[1]),
            max(r for r, _c in item[1]),
            -item[0],
        ),
    )
    return _expand_color(impl, grid, color)



def _longest_straight_object_shortcut(impl, grid):
    straight = [
        item
        for item in impl._components(grid)
        if len({r for r, _c in item[1]}) == 1
        or len({c for _r, c in item[1]}) == 1
    ]
    if not straight:
        return [row[:] for row in grid]
    color, _cells = max(straight, key=lambda item: (len(item[1]), -item[0]))
    return _expand_color(impl, grid, color)


def _source_size_rank_shortcut(impl, grid, rank):
    ordered = sorted(
        impl._components(grid),
        key=lambda item: (-len(item[1]), item[0]),
    )
    color, _cells = ordered[rank - 1]
    return _expand_color(impl, grid, color)

def _shortcut_sweep(adapter, seeds=200):
    impl = adapter._impl
    checked_pairs = 0
    for seed in range(seeds):
        episode = adapter.generate(seed, {"halo_mode": "selected_two_step"}, 3, 4)
        orientations = set()
        halves = set()
        source_sizes = set()
        source_size_ranks = set()
        topologies = set()
        widest_matches = []
        bottom_matches = []
        straight_matches = []
        rank_two_matches = []
        rank_three_matches = []
        for pair in episode["train"]:
            grid = pair["input"]
            selected = impl.selected_color(impl.one_ring_halo(grid))
            cells = next(
                cells for color, cells in impl._components(grid) if color == selected
            )
            height = max(r for r, _c in cells) - min(r for r, _c in cells) + 1
            width = max(c for _r, c in cells) - min(c for _r, c in cells) + 1
            orientations.add("horizontal" if width > height else "vertical")
            source_sizes.add(len(cells))
            ordered = sorted(
                impl._components(grid),
                key=lambda item: (-len(item[1]), item[0]),
            )
            source_size_ranks.add(
                next(
                    index + 1
                    for index, (color, _cells) in enumerate(ordered)
                    if color == selected
                )
            )
            topologies.add(
                "straight"
                if len({r for r, _c in cells}) == 1
                or len({c for _r, c in cells}) == 1
                else "bent"
            )
            centroid = sum(r for r, _c in cells) / len(cells)
            halves.add("top" if centroid < len(grid) / 2 else "bottom")
            widest_matches.append(
                _widest_object_shortcut(impl, grid) == pair["output"]
            )
            bottom_matches.append(
                _bottommost_object_shortcut(impl, grid) == pair["output"]
            )
            straight_matches.append(
                _longest_straight_object_shortcut(impl, grid) == pair["output"]
            )
            rank_two_matches.append(
                _source_size_rank_shortcut(impl, grid, 2) == pair["output"]
            )
            rank_three_matches.append(
                _source_size_rank_shortcut(impl, grid, 3) == pair["output"]
            )
            checked_pairs += 1
        if (
            orientations != {"horizontal", "vertical"}
            or halves != {"top", "bottom"}
            or source_sizes != {6, 8}
            or source_size_ranks != {2, 3}
            or topologies != {"straight", "bent"}
            or all(widest_matches)
            or all(bottom_matches)
            or all(straight_matches)
            or all(rank_two_matches)
            or all(rank_three_matches)
        ):
            raise AssertionError(f"shape/location shortcut survived seed {seed}")
    return {
        "seeds": seeds,
        "demonstrations_per_seed": 3,
        "checked_pairs": checked_pairs,
        "selected_orientations": ["horizontal", "vertical"],
        "selected_vertical_halves": ["bottom", "top"],
        "selected_source_sizes": [6, 8],
        "selected_source_size_ranks": [2, 3],
        "selected_topologies": ["bent", "straight"],
        "widest_object_rejected": True,
        "bottommost_object_rejected": True,
        "longest_straight_object_rejected": True,
        "always_second_largest_source_rejected": True,
        "always_third_largest_source_rejected": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    contract = json.loads((HOME / "promotion.json").read_text())
    settings = [{"halo_mode": "one_ring"}, {"halo_mode": "selected_two_step"}]
    jobs = [
        {"seed": seed, "settings": setting, "demos": 3, "queries": 4}
        for setting in settings
        for seed in (0, 17)
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    adapter = _load_adapter()
    prefix_checks = []
    for setting in settings:
        full = adapter.generate(29, setting, 3, 4)
        one = adapter.generate(29, setting, 3, 1)
        prefix_checks.append(
            {
                "settings": setting,
                "same_train": full["train"] == one["train"],
                "same_first_query": full["test"][0] == one["test"][0],
            }
        )
    shortcut_sweep = _shortcut_sweep(adapter)
    matched_inputs = []
    for seed in (0, 17):
        a = adapter.generate(seed, settings[0], 3, 4)
        b = adapter.generate(seed, settings[1], 3, 4)
        matched_inputs.append(
            {
                "seed": seed,
                "matched": all(
                    [pair["input"] for pair in a[split]]
                    == [pair["input"] for pair in b[split]]
                    for split in ("train", "test")
                ),
            }
        )
    report = {
        "schema": "arcpuzzles-parametric-focused-study-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "jobs": jobs,
        "racket": result["racket"],
        "racket_evaluations": result["racket_evaluations"],
        "checks": result["checks"],
        "matched_inputs": matched_inputs,
        "prefix_checks": prefix_checks,
        "shortcut_sweep": shortcut_sweep,
        "limits": "Protected Racket: two settings, seeds 0 and 17, three demos and four queries. Python shortcut audit: 200 seeds x three demonstrations.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "passed", "out": str(args.out), "racket_evaluations": result["racket_evaluations"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
