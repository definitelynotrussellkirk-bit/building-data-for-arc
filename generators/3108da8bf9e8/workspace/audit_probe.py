"""Reproducible adversarial probes for review audit targets.

Run from repo root with:
    PYTHONPATH=shared/runtime python3 generators/3108da8bf9e8/workspace/audit_probe.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row(task_id: str) -> dict:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def normalize_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return grid


def pairs(row: dict) -> list[dict]:
    test = row.get("test", [])
    if isinstance(test, dict):
        test = [test]
    return [*row.get("train", []), *test]


def components(grid):
    grid = normalize_grid(grid)
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rs = [x for x, _ in cells]
            cs = [x for _, x in cells]
            result.append({
                "color": color,
                "size": len(cells),
                "bbox": [min(rs), min(cs), max(rs), max(cs)],
                "bbox_h": max(rs) - min(rs) + 1,
                "bbox_w": max(cs) - min(cs) + 1,
            })
    return result


def probe_2b7() -> dict:
    task_id = "2b7bcfbf942b"
    gen = load(task_id)
    row = canonical_row(task_id)
    canonical_profiles = []
    for index, pair in enumerate(pairs(row)):
        comps = components(pair["input"])
        canonical_profiles.append({
            "pair": index,
            "n_objects": len(comps),
            "bbox_sizes": sorted([[obj["bbox_h"], obj["bbox_w"]] for obj in comps]),
        })

    generated_profiles = Counter()
    for seed in range(120):
        grid = gen.generate(seed, seed, difficulty=("easy", "medium", "hard")[seed % 3])
        comps = components(grid)
        key = (len(comps), tuple(sorted((obj["bbox_h"], obj["bbox_w"]) for obj in comps)))
        generated_profiles[key] += 1

    inert = {}
    base = gen.generate(17, 4, difficulty="medium")
    for name, left, right in (
        ("anchor_corner", False, True),
        ("asymmetry_force", False, True),
        ("palette_kind", "warm", "cool"),
        ("position_bias", "fixed", "anything"),
    ):
        inert[name] = (
            gen.generate(17, 4, difficulty="medium", **{name: left})
            == gen.generate(17, 4, difficulty="medium", **{name: right})
            == base
        )

    return {
        "canonical_profiles": canonical_profiles,
        "generated_profiles": [
            {"profile": [n, list(bboxes)], "count": count}
            for (n, bboxes), count in sorted(generated_profiles.items())
        ],
        "minimal_impostor_self_check": gen.self_check([[1, 2]]),
        "inert_axis_same_grid": inert,
    }


def probe_20b5() -> dict:
    task_id = "20b5e7246250"
    gen = load(task_id)
    row = canonical_row(task_id)
    canonical_errors = []
    mirror_errors = []
    for index, pair in enumerate(pairs(row)):
        inp = normalize_grid(pair["input"])
        out = normalize_grid(pair["output"])
        errs = gen.self_check(inp)
        if errs:
            canonical_errors.append([index, errs])
        if not errs and gen.rule_mirror(inp) != out:
            mirror_errors.append(index)

    shortcut_hits = Counter()
    profiles = Counter()
    for seed in range(600):
        grid = gen.generate(seed, seed * 31 + 7, difficulty=("easy", "medium", "hard")[seed % 3])
        analysis = gen._analyze(grid)
        if analysis["errors"]:
            raise AssertionError((seed, analysis["errors"]))
        frames = analysis["frames"]
        sources = analysis["sources"]
        keys = analysis["keys"]
        official_colors = tuple(source["color"] for source in sources)
        source_reading = tuple(
            source["color"] for source in sorted(sources, key=lambda obj: obj["bbox"])
        )
        source_color = tuple(sorted(source["color"] for source in sources))
        frame_widths = tuple(frame["bbox"][3] - frame["bbox"][1] + 1 for frame in frames)
        source_widths = tuple(source["bbox"][3] - source["bbox"][1] + 1 for source in sources)

        shortcut_hits["source_reading_order"] += source_reading == official_colors
        shortcut_hits["source_color_order"] += source_color == official_colors
        shortcut_hits["ignore_key_use_generated_order"] += tuple(
            source["color"] for source in sources
        ) == official_colors
        shortcut_hits["key_colors_are_monotone"] += keys[0]["color"] < keys[1]["color"]
        profiles[(analysis["facts"]["layout_family"], analysis["facts"]["source_order"])] += 1

        # Assert the intended relation itself is not silently broken.
        assert tuple(key["color"] for key in keys) == official_colors
        assert all(sw <= fw - 2 for sw, fw in zip(source_widths, frame_widths))

    return {
        "canonical_self_check_failures": canonical_errors,
        "canonical_mirror_failures": mirror_errors,
        "generated": 600,
        "shortcut_match_counts": dict(shortcut_hits),
        "layout_source_order_profiles": {
            f"{layout}/{order}": count for (layout, order), count in sorted(profiles.items())
        },
        "semantic_contract_declared": {
            name: hasattr(gen, name)
            for name in ("strict_canonical_like", "SEMANTIC_WITNESSES", "lesson_identifiable")
        },
    }


def main() -> None:
    report = {"20b5e7246250": probe_20b5(), "2b7bcfbf942b": probe_2b7()}
    out = Path(__file__).with_name("audit_probe_report.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
