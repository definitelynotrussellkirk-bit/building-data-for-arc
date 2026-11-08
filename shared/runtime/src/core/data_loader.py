"""Load ARC-AGI-2 data from raw JSON files.

The full Kaggle raw split is not always bundled with lightweight review
archives. When the official training JSON is absent, fall back to the repo's
canonical JSONL export so local tools/tests still have the same task ids used
by `solvers.grounded_rules`.
"""

import json, os
from pathlib import Path

# Primary: local repo data/raw/. Fallback: Kaggle competition mount.
_CANDIDATES = [
    Path(__file__).resolve().parents[2] / "data" / "raw",
    Path("/kaggle/input/competitions/arc-prize-2026-arc-agi-2"),
    Path("/kaggle/input/arc-prize-2026-arc-agi-2"),
]
DATA_DIR = next((p for p in _CANDIDATES if p.exists()), _CANDIDATES[0])


def _canonical_rows_for(dataset: str) -> dict:
    """Return canonical rows keyed by task_id for a local split fallback."""
    if dataset != "training":
        return {}
    path = Path(__file__).resolve().parents[2] / "data" / "canonical" / "puzzles.jsonl"
    if not path.exists():
        return {}

    rows = {}
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("source") == dataset:
                rows[row["task_id"]] = row
    return rows


def _canonical_challenges(dataset: str) -> dict:
    rows = _canonical_rows_for(dataset)
    return {
        task_id: {"train": row["train"], "test": row["test"]}
        for task_id, row in rows.items()
    }


def _canonical_solutions(dataset: str) -> dict:
    rows = _canonical_rows_for(dataset)
    solutions = {}
    for task_id, row in rows.items():
        outs = []
        for pair in row.get("test", []):
            if "output" not in pair:
                break
            outs.append(pair["output"])
        if outs:
            solutions[task_id] = outs
    return solutions


def load_challenges(dataset: str = "training") -> dict:
    """Load challenge tasks. dataset: 'training', 'evaluation', or 'test'."""
    fname = f"arc-agi_{dataset}_challenges.json"
    # Try each candidate directory — Kaggle mounts may differ from local
    for d in _CANDIDATES:
        path = d / fname
        if path.exists():
            with open(path) as f:
                return json.load(f)
    fallback = _canonical_challenges(dataset)
    if fallback:
        return fallback
    raise FileNotFoundError(f"{fname} not found in any of: {[str(d) for d in _CANDIDATES]}")


def load_solutions(dataset: str = "training") -> dict:
    """Load solutions. dataset: 'training' or 'evaluation'."""
    fname = f"arc-agi_{dataset}_solutions.json"
    for d in _CANDIDATES:
        path = d / fname
        if path.exists():
            with open(path) as f:
                return json.load(f)
    fallback = _canonical_solutions(dataset)
    if fallback:
        return fallback
    raise FileNotFoundError(f"{fname} not found in any of: {[str(d) for d in _CANDIDATES]}")


def load_task_pairs(dataset: str = "training") -> dict:
    """Load challenges merged with solutions (where available)."""
    challenges = load_challenges(dataset)
    try:
        solutions = load_solutions(dataset)
    except FileNotFoundError:
        solutions = {}

    merged = {}
    for task_id, task in challenges.items():
        merged[task_id] = {
            "train": task["train"],
            "test": task["test"],
        }
        if task_id in solutions:
            for i, sol in enumerate(solutions[task_id]):
                if i < len(merged[task_id]["test"]):
                    merged[task_id]["test"][i]["output"] = sol
    return merged
