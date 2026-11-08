#!/usr/bin/env python3
"""Independent, source-bound semantic probe for task 5b4fd0a9c80e.

The probe intentionally reimplements connected components, cropping, sorting,
centering, and rival scoring instead of importing implementation helpers from
``generator.py``.  Future reviewers can use it to detect authority drift,
canonical shortcuts, or schedule regressions and save a machine-readable report.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

TASK_ID = "5b4fd0a9c80e"
HERE = Path(__file__).resolve()


def _load_reviewer_support():
    """Load public path helpers in both source-tree and copied-runtime layouts."""
    try:
        import reviewer_support as support
        return support
    except ImportError:
        for ancestor in HERE.parents:
            for candidate in (ancestor / "shared" / "runtime", ancestor):
                if (candidate / "reviewer_support.py").is_file():
                    sys.path.insert(0, str(candidate))
                    import reviewer_support as support
                    return support
        raise


_REVIEWER_SUPPORT = _load_reviewer_support()
REPO_ROOT = _REVIEWER_SUPPORT.find_root(HERE)
DEFAULT_CANONICAL = _REVIEWER_SUPPORT.canonical_path(REPO_ROOT)

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_key(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def load_generator(path: str | Path | None = None):
    source = Path(path) if path is not None else HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}_probe", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs(path: str | Path | None = None) -> list[dict[str, Any]]:
    source = Path(path) if path is not None else DEFAULT_CANONICAL
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            task = json.loads(line)
            if task.get("task_id") != TASK_ID:
                continue
            rows: list[dict[str, Any]] = []
            for split in ("train", "test"):
                values = task.get(split, [])
                if isinstance(values, dict):
                    values = [values]
                for index, pair in enumerate(values):
                    rows.append({**pair, "split": split, "index": index})
            return rows
    raise KeyError(f"canonical task {TASK_ID} not found in {source}")


def components(grid: list[list[int]]) -> list[dict[str, Any]]:
    if not isinstance(grid, list) or not grid or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a nonempty rectangular grid")

    seen: set[tuple[int, int]] = set()
    found: list[dict[str, Any]] = []
    for row in range(len(grid)):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < len(grid)
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            found.append(
                {
                    "color": color,
                    "size": len(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return found


def oracle(
    grid: list[list[int]],
    *,
    order: str = "area",
    alignment: str = "center",
    gap: int = 1,
) -> list[list[int]]:
    """Independent transcription of the canonical stack-crops transform."""
    items = components(grid)
    if not items:
        raise ValueError("grid contains no components")
    if order == "area":
        items.sort(key=lambda item: (item["size"], item["bbox"][0], item["bbox"][1]))
    elif order == "source":
        items.sort(key=lambda item: (item["bbox"][0], item["bbox"][1]))
    elif order == "color_tie":
        items.sort(key=lambda item: (item["size"], item["color"], item["bbox"][0], item["bbox"][1]))
    else:
        raise ValueError(f"unknown order {order!r}")
    if alignment not in {"center", "left"}:
        raise ValueError(f"unknown alignment {alignment!r}")

    crops: list[list[list[int]]] = []
    for item in items:
        top, left, bottom, right = item["bbox"]
        crops.append([row[left : right + 1] for row in grid[top : bottom + 1]])
    output_width = max(len(crop[0]) for crop in crops)
    output_height = sum(len(crop) for crop in crops) + gap * (len(crops) - 1)
    output = [[0] * output_width for _ in range(output_height)]
    output_top = 0
    for crop in crops:
        output_left = 0 if alignment == "left" else (output_width - len(crop[0])) // 2
        for row_index, row in enumerate(crop):
            output[output_top + row_index][output_left : output_left + len(row)] = row
        output_top += len(crop) + gap
    return output


def _callable_mapping(module: Any, name: str) -> dict[str, Callable[[Any], Any]]:
    raw = getattr(module, name, {})
    if not isinstance(raw, dict):
        raise TypeError(f"{name} must be a mapping")
    invalid = [key for key, value in raw.items() if not isinstance(key, str) or not callable(value)]
    if invalid:
        raise TypeError(f"{name} contains non-callable entries: {invalid}")
    return dict(raw)


def run_probe(
    *,
    generator_path: str | Path | None = None,
    canonical_path: str | Path | None = None,
    lessons_per_band: int = 20,
    seed_start: int = 0,
) -> dict[str, Any]:
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")
    generator_source = Path(generator_path) if generator_path is not None else HERE.parents[1] / "generator.py"
    canonical_source = (
        Path(canonical_path)
        if canonical_path is not None
        else DEFAULT_CANONICAL
    )
    gen = load_generator(generator_source)
    canonical = canonical_pairs(canonical_source)
    shortcuts = _callable_mapping(gen, "CANONICAL_SHORTCUTS")
    competitors = _callable_mapping(gen, "LESSON_COMPETITORS")
    failures: list[str] = []

    canonical_summary: dict[str, Any] = {
        "pair_count": len(canonical),
        "train_count": sum(pair["split"] == "train" for pair in canonical),
        "test_count": sum(pair["split"] == "test" for pair in canonical),
        "invalid_inputs": 0,
        "oracle_mismatches": 0,
        "mirror_mismatches": 0,
        "shortcut_fit": {},
    }
    for pair in canonical:
        label = f"canonical {pair['split']}[{pair['index']}]"
        findings = gen.self_check(pair["input"])
        if findings:
            canonical_summary["invalid_inputs"] += 1
            failures.append(f"{label}: self_check: {findings[0]}")
        expected = oracle(pair["input"])
        if expected != pair["output"]:
            canonical_summary["oracle_mismatches"] += 1
            failures.append(f"{label}: independent oracle disagrees with label")
        if gen.rule_mirror(pair["input"]) != pair["output"]:
            canonical_summary["mirror_mismatches"] += 1
            failures.append(f"{label}: generator rule_mirror disagrees with label")

    train = [pair for pair in canonical if pair["split"] == "train"]
    for name, shortcut in shortcuts.items():
        train_agreements = sum(shortcut(pair["input"]) == pair["output"] for pair in train)
        all_agreements = sum(shortcut(pair["input"]) == pair["output"] for pair in canonical)
        canonical_summary["shortcut_fit"][name] = {
            "train_agreements": train_agreements,
            "train_pairs": len(train),
            "all_agreements": all_agreements,
            "all_pairs": len(canonical),
        }

    bands: dict[str, Any] = {}
    for band_label, difficulty in (("default", None), ("easy", "easy"), ("medium", "medium"), ("hard", "hard")):
        row = {
            "lessons": lessons_per_band,
            "pairs_seen": 0,
            "unique_inputs": 0,
            "invalid_inputs": 0,
            "oracle_mismatches": 0,
            "mirror_mismatches": 0,
            "unidentifiable_lessons": 0,
            "competitor_survivors": {name: 0 for name in competitors},
        }
        input_keys: set[str] = set()
        for lesson_index in range(lessons_per_band):
            pairs: list[dict[str, Any]] = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                sample_index = lesson_index * (gen.EXAMPLES_NEEDED + 1) + offset
                grid = gen.generate(seed_start + lesson_index, sample_index, difficulty=difficulty)
                expected = oracle(grid)
                pair = {"input": grid, "output": expected}
                pairs.append(pair)
                row["pairs_seen"] += 1
                input_keys.add(_grid_key(grid))
                findings = gen.self_check(grid)
                if findings:
                    row["invalid_inputs"] += 1
                    failures.append(f"{band_label} lesson {lesson_index} pair {offset}: {findings[0]}")
                if gen.rule_mirror(grid) != expected:
                    row["mirror_mismatches"] += 1
                    failures.append(f"{band_label} lesson {lesson_index} pair {offset}: mirror mismatch")
                # The generated output is independent-oracle derived; this catches
                # accidental future use of another transform in the probe itself.
                if expected != oracle(grid):
                    row["oracle_mismatches"] += 1
                    failures.append(f"{band_label} lesson {lesson_index} pair {offset}: oracle instability")

            demos = pairs[: gen.EXAMPLES_NEEDED]
            query = pairs[gen.EXAMPLES_NEEDED]
            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                row["unidentifiable_lessons"] += 1
                failures.append(f"{band_label} lesson {lesson_index}: {'; '.join(reasons)}")
            for name, competitor in competitors.items():
                if all(competitor(pair["input"]) == pair["output"] for pair in demos):
                    row["competitor_survivors"][name] += 1
        row["unique_inputs"] = len(input_keys)
        bands[band_label] = row

    return {
        "schema": f"{TASK_ID}-reference-probe-v1",
        "task_id": TASK_ID,
        "source_binding": {
            "probe_path": str(HERE),
            "probe_sha256": _sha256(HERE),
            "generator_path": str(generator_source.resolve()),
            "generator_sha256": _sha256(generator_source),
            "generator_version": gen.VERSION,
            "rule_hash": gen.RULE_HASH,
            "canonical_path": str(canonical_source.resolve()),
            "canonical_sha256": _sha256(canonical_source),
        },
        "options": {"lessons_per_band": lessons_per_band, "seed_start": seed_start},
        "canonical": canonical_summary,
        "bands": bands,
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=HERE.parents[1] / "generator.py")
    parser.add_argument("--canonical", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--lessons-per-band", type=int, default=20)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run_probe(
        generator_path=args.generator,
        canonical_path=args.canonical,
        lessons_per_band=args.lessons_per_band,
        seed_start=args.seed_start,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(rendered, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
        print(args.out)
    return 0 if not report["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
