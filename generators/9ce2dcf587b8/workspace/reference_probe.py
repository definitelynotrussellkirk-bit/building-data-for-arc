"""Independent, source-bound probe for 9ce2dcf587b8.

This helper deliberately does not import the production generator for its oracle.
It can verify canonical pairs, inspect active/archival rule sources, and exhaust
all single-query rotations of consecutive five-pair teaching windows.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

from reviewer_support import canonical_path, find_root

TASK_ID = "9ce2dcf587b8"
DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def intended_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror of the pinned canonical Racket semantics."""
    h, w = len(grid), len(grid[0])
    source = [list(row) for row in grid]
    output = [list(row) for row in grid]
    markers = [
        (r, c, value)
        for r, row in enumerate(source)
        for c, value in enumerate(row)
        if value != 0
    ]
    for r, c, value in markers:
        for dr, dc in DIAGONALS:
            for distance in range(1, max(h, w)):
                nr, nc = r + dr * distance, c + dc * distance
                if 0 <= nr < h and 0 <= nc < w:
                    if source[nr][nc] == 0 and output[nr][nc] == 0:
                        output[nr][nc] = value
    return output


def _base_solution_path(root: Path) -> Path:
    relative = "base/solutions/training/623ea044__9ce2dcf587b8.json"
    for prefix in ("data", "shared/data"):
        path = root / prefix / relative
        if path.is_file():
            return path
    raise FileNotFoundError(f"no selected rule source under {root}")


def authority_sources(root: str | Path) -> dict[str, str]:
    root = Path(root).resolve()
    canonical = None
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                canonical = row["program_solution"]
                break
    if canonical is None:
        raise KeyError(TASK_ID)
    selected = json.loads(_base_solution_path(root).read_text(encoding="utf-8"))[
        "racket_target"
    ]
    return {
        "canonical": canonical,
        "target": selected["target_code"],
        "raw": selected["raw_code"],
        "target_status": selected["target_status"],
    }


def analyze_schedule(generator, *, seed: int, starts: Iterable[int]) -> dict[str, Any]:
    """Check all five query rotations for each consecutive teaching window."""
    ambiguities = []
    self_check_failures = []
    profiles = set()
    refuted = set()
    lesson_count = 0

    for start in starts:
        pairs = []
        for sample_index in range(start, start + generator.EXAMPLES_NEEDED + 1):
            grid = generator.generate(seed, sample_index, difficulty="medium")
            errors = generator.self_check(grid)
            if errors:
                self_check_failures.append(
                    {"start": start, "sample_index": sample_index, "errors": errors}
                )
            observation = generator.observe_overrides(grid)
            profiles.add({1: "single", 2: "double", 3: "triple"}[observation["n_dots"]])
            expected = intended_output(grid)
            pairs.append({"input": grid, "output": expected, "sample_index": sample_index})
            for name, rival in generator.LESSON_COMPETITORS.items():
                if rival(grid) != expected:
                    refuted.add(name)

        for query_position, query in enumerate(pairs):
            lesson_count += 1
            demos = [pair for index, pair in enumerate(pairs) if index != query_position]
            for name, rival in generator.LESSON_COMPETITORS.items():
                if all(rival(pair["input"]) == pair["output"] for pair in demos):
                    prediction = rival(query["input"])
                    if prediction != query["output"]:
                        ambiguities.append(
                            {
                                "start": start,
                                "query_position": query_position,
                                "query_sample_index": query["sample_index"],
                                "competitor": name,
                                "prediction": prediction,
                                "expected": query["output"],
                            }
                        )

    order = {"single": 0, "double": 1, "triple": 2}
    return {
        "lesson_count": lesson_count,
        "ambiguities": ambiguities,
        "self_check_failures": self_check_failures,
        "profiles_seen": sorted(profiles, key=order.__getitem__),
        "refuted_competitors": sorted(refuted),
    }


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("generator_9ce2dcf587b8_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, default=Path(__file__).resolve().parents[1] / "generator.py")
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--starts", type=int, default=9)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    generator = _load_generator(args.generator.resolve())
    root = find_root(__file__)
    report = {
        "task_id": TASK_ID,
        "authority": {
            key: value if key == "target_status" else __import__("hashlib").sha256(value.encode()).hexdigest()
            for key, value in authority_sources(root).items()
        },
        "schedule": analyze_schedule(generator, seed=args.seed, starts=range(args.starts)),
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if not report["schedule"]["ambiguities"] and not report["schedule"]["self_check_failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
