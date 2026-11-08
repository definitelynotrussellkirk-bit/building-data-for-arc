"""Measure whether a row-local color-presence shortcut survives lessons.

Run from the packet root with:
  python3 run_with_racket.py python3 generators/5949237e2737/workspace/probe_row_color_presence.py [GENERATOR_PATH]

The wrapper's effective cwd is repo/.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

GENERATOR_PATH = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else Path("generators/5949237e2737/generator.py")
)
spec = importlib.util.spec_from_file_location("reviewed_generator_5949237e2737", GENERATOR_PATH)
GEN = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(GEN)


def row_color_presence(grid):
    facts = GEN._analysis(grid)
    output = [[0 for _ in row] for row in grid]
    half = facts["half_w"]
    for row, col, value in facts["left"]:
        if value in grid[row][half + 1 :]:
            output[row][2 * half - col] = value
    return output


def main() -> int:
    forced_survivors = []
    lesson_survivors = []
    for band in ("easy", "medium", "hard"):
        for seed in range(200):
            grid = GEN.generate(seed, 4, difficulty=band, scene_profile="wrong_color_decoy")
            if row_color_presence(grid) == GEN.rule_mirror(grid):
                forced_survivors.append((band, seed))

            demos = [GEN.generate(seed, index, difficulty=band) for index in range(5)]
            if all(row_color_presence(grid) == GEN.rule_mirror(grid) for grid in demos):
                lesson_survivors.append((band, seed))

    print(f"forced_profile_survivors={len(forced_survivors)}/600")
    print(f"five_demo_lesson_survivors={len(lesson_survivors)}/600")
    print(f"first_forced_survivors={forced_survivors[:20]}")
    print(f"first_lesson_survivors={lesson_survivors[:20]}")
    return 1 if forced_survivors or lesson_survivors else 0


if __name__ == "__main__":
    raise SystemExit(main())
