"""Prototype canonical-vs-generated semantic-support probe for this task.

This is intentionally independent of generator.self_check: it extracts the
omitted block occupancy directly from the grid.  That catches a generator that
is structurally valid but collapses a canonical-varying sufficient statistic.

Run from repo root:
    PYTHONPATH=shared/runtime python3 \
      generators/3108da8bf9e8/workspace/semantic_support_probe.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PACKET_ROOT = REPO.parent
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
TASK_ID = "3108da8bf9e8"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row() -> dict:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise KeyError(TASK_ID)


def omitted_count_signature(grid) -> int:
    counts = {
        sum(
            grid[br * 4 + dr][bc * 4 + dc] == 1
            for dr in range(3)
            for dc in range(3)
        )
        for br in range(3)
        for bc in range(3)
    }
    missing = sorted(set(range(10)) - counts)
    if len(counts) != 9 or len(missing) != 1:
        raise ValueError(f"not a unique nine-of-ten occupancy lesson: {sorted(counts)}")
    return missing[0]


def _canonical_signatures() -> list[int]:
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [
        omitted_count_signature(pair["input"])
        for pair in [*row["train"], *test]
    ]


def _sample(module, per_band: int = 80) -> dict[str, dict[str, int]]:
    report = {}
    for band in ("easy", "medium", "hard"):
        counts = Counter()
        for index in range(per_band):
            grid = module.generate(90210, index, difficulty=band)
            counts[omitted_count_signature(grid)] += 1
        report[band] = {str(key): counts[key] for key in sorted(counts)}
    return report


def main() -> None:
    current_path = REPO / "generators" / TASK_ID / "generator.py"
    baseline_path = (
        PACKET_ROOT
        / ".review"
        / "baseline"
        / "repo"
        / "generators"
        / TASK_ID
        / "generator.py"
    )
    current = _load(current_path, "support_probe_current")
    baseline = _load(baseline_path, "support_probe_baseline")
    canonical = _canonical_signatures()
    report = {
        "task_id": TASK_ID,
        "signature": "the sole omitted color-1 count among 0..9",
        "canonical_sequence": canonical,
        "canonical_support": sorted(set(canonical)),
        "baseline_generated": _sample(baseline),
        "repaired_generated": _sample(current),
        "failure_rule": (
            "flag a generated signature that is constant while the canonical "
            "signature varies, or a canonical-supported value that has zero "
            "generated support in the deterministic census"
        ),
    }
    out = Path(__file__).with_name("semantic_support_probe_report.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
