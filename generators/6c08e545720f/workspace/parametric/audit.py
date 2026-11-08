"""Bounded adversarial self-review for the connect-then-mark-crossings family."""
from __future__ import annotations

from collections.abc import Iterable
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

HERE = Path(__file__).resolve().parent
TASK_ID = "6c08e545720f"


def _load(filename: str) -> ModuleType:
    path = (HERE / filename).resolve()
    if path.parent != HERE or path.is_symlink() or not path.is_file():
        raise ValueError(f"missing regular adjacent source: {filename}")
    name = "_audit_6c08e545720f_" + path.stem + "_" + hashlib.sha256(path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(
    *, seeds: Iterable[int] = range(64), demo_counts: tuple[int, ...] = (2, 3, 6)
) -> dict[str, object]:
    adapter = _load("adapter.py")
    family = _load("family.py")
    seed_list = tuple(seeds)
    survivors = {
        "connect_only": 0,
        "fixed_zero": 0,
        "pair_midpoints": 0,
        "input_crossings": 0,
    }
    crossing_locations: set[tuple[int, int]] = set()
    cue_colors: set[int] = set()
    pair_counts: set[int] = set()
    episodes = 0
    generated_pairs = 0
    stress_30 = 0

    rival_functions = {
        "connect_only": family.rival_connect_only,
        "fixed_zero": family.rival_fixed_zero,
        "pair_midpoints": family.rival_pair_midpoints,
        "input_crossings": family.rival_input_crossings,
    }
    for seed in seed_list:
        for demos in demo_counts:
            canonical = adapter.generate(seed, {"mode": "connect_only"}, demos, 4)
            sequential = adapter.generate(
                seed, {"mode": "connect_then_mark_crossings"}, demos, 4
            )
            left = [*canonical["train"], *canonical["test"]]
            right = [*sequential["train"], *sequential["test"]]
            assert [pair["input"] for pair in left] == [pair["input"] for pair in right]
            assert len(
                {json.dumps(pair["input"], separators=(",", ":")) for pair in left}
            ) == demos + 4
            assert all(
                a["output"] != b["output"] for a, b in zip(left, right, strict=True)
            )
            thirty = sum(
                len(pair["input"]) == len(pair["input"][0]) == 30
                for pair in canonical["test"]
            )
            assert thirty == 1
            stress_30 += thirty

            for pair in sequential["train"]:
                info = family.analyze(pair["input"])
                cue_colors.add(int(info["cue_color"]))
                pair_counts.add(len(info["paired_colors"]))
                crossing_locations.update(tuple(cell) for cell in info["crossings"])
                assert info["input_crossings"] == []
                assert info["crossings"]
            for name, rival in rival_functions.items():
                survivors[name] += int(
                    all(rival(pair["input"]) == pair["output"] for pair in sequential["train"])
                )
            episodes += 1
            generated_pairs += 2 * (demos + 4)

    assert all(count == 0 for count in survivors.values())
    assert len(cue_colors) >= min(4, max(1, len(seed_list)))
    assert len(crossing_locations) >= min(8, max(1, len(seed_list) * 2))
    return {
        "schema": "arcpuzzles-parametric-self-review-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "scope": {
            "seeds": list(seed_list),
            "demo_counts": list(demo_counts),
            "queries": 4,
            "episodes_per_setting_pair": episodes,
            "generated_labeled_pairs": generated_pairs,
            "thirty_by_thirty_queries": stress_30,
        },
        "settings": ["connect_only", "connect_then_mark_crossings"],
        "cue_colors": sorted(cue_colors),
        "paired_color_counts": sorted(pair_counts),
        "distinct_crossing_locations": len(crossing_locations),
        "named_rivals": {
            name: {"demo_episodes_survived": count} for name, count in survivors.items()
        },
        "source_sha256": {
            name: _sha256(HERE / name)
            for name in (
                "adapter.py",
                "family.py",
                "canonical.rkt",
                "connect_then_mark_crossings.rkt",
                "promotion.json",
            )
        },
        "limits": [
            "Finite deterministic seeds and named rivals only; this is not universal uniqueness evidence.",
            "Python mirror labels are checked here; protected-Racket labels are established separately by authoring preflight.",
            "This receipt does not grant owner acceptance or training admission.",
        ],
    }


def main() -> int:
    report = audit()
    out = HERE / "evidence" / "current" / "self-review.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = out.with_suffix(".tmp")
    temp.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(out)
    print(
        json.dumps(
            {
                "status": report["status"],
                "path": str(out),
                "episodes": report["scope"]["episodes_per_setting_pair"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
