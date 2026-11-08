"""Bounded adversarial self-review for the H31 native parametric family.

This is evidence against named shortcuts, not owner qualification or a proof of
universal identifiability.  It intentionally uses only the task-local adapter
and writes a reproducible source-bound receipt for later agents.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

HERE = Path(__file__).resolve().parent
TASK_ID = "9d2f7c9e2ac4"
SEEDS = tuple(range(32))
DEMO_COUNTS = (2, 3, 6)
QUERIES = 4


def _load(filename: str) -> ModuleType:
    path = (HERE / filename).resolve()
    if path.parent != HERE or path.is_symlink() or not path.is_file():
        raise ValueError(f"missing regular adjacent source: {filename}")
    name = "_audit_h31_" + path.stem + "_" + hashlib.sha256(path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _fingerprint(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _replace(grid: list[list[int]], old: int, new: int) -> list[list[int]]:
    return [[new if value == old else value for value in row] for row in grid]


def _br_cue_colors(grid: list[list[int]], source: int) -> set[int]:
    split = len(grid) // 2
    return {
        grid[r][c]
        for r in range(split + 1, len(grid))
        for c in range(split + 1, len(grid[0]))
        if grid[r][c] not in (0, 9, source)
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict[str, object]:
    adapter = _load("adapter.py")
    family = _load("family.py")
    fixed_lowest_survivors = 0
    no_postprocess_survivors = 0
    selected_colors: set[int] = set()
    episodes = 0
    generated_pairs = 0
    stress_30 = 0

    for seed in SEEDS:
        for demos in DEMO_COUNTS:
            canonical = adapter.generate(seed, {"mode": "copy_only"}, demos, QUERIES)
            alternative = adapter.generate(seed, {"mode": "cue_payload"}, demos, QUERIES)
            left_pairs = [*canonical["train"], *canonical["test"]]
            right_pairs = [*alternative["train"], *alternative["test"]]
            assert len(canonical["train"]) == demos and len(canonical["test"]) == QUERIES
            assert [p["input"] for p in left_pairs] == [p["input"] for p in right_pairs]
            assert len({_fingerprint(p["input"]) for p in left_pairs}) == demos + QUERIES
            assert all(a["output"] != b["output"] for a, b in zip(left_pairs, right_pairs, strict=True))
            assert any(len(pair["input"]) == len(pair["input"][0]) == 30 for pair in canonical["test"])
            stress_30 += sum(len(pair["input"]) == len(pair["input"][0]) == 30 for pair in canonical["test"])

            low_ok = True
            none_ok = True
            for pair in alternative["train"]:
                info = family.analyze(pair["input"])
                selected_colors.add(int(info["selected_cue_color"]))
                assert int(info["remote_payload_count"]) >= 2
                stage_a = family.solve(pair["input"], "copy_only")
                cues = _br_cue_colors(pair["input"], int(info["source_color"]))
                assert len(cues) == 3
                low_ok &= _replace(stage_a, min(cues), int(info["source_color"])) == pair["output"]
                none_ok &= stage_a == pair["output"]
            fixed_lowest_survivors += int(low_ok)
            no_postprocess_survivors += int(none_ok)
            episodes += 1
            generated_pairs += 2 * (demos + QUERIES)

    assert fixed_lowest_survivors == 0
    assert no_postprocess_survivors == 0
    assert len(selected_colors) >= 4
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
        "settings": ["copy_only", "cue_payload"],
        "selected_cue_colors": sorted(selected_colors),
        "named_rivals": {
            "fixed_lowest_br_cue": {"demo_episodes_survived": fixed_lowest_survivors},
            "no_postprocess_tile": {"demo_episodes_survived": no_postprocess_survivors},
        },
        "source_sha256": {
            name: _sha256(HERE / name)
            for name in ("adapter.py", "family.py", "canonical.rkt", "cue_payload.rkt", "promotion.json")
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
