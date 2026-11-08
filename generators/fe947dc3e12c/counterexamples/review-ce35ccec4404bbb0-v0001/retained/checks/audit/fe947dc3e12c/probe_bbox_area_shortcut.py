#!/usr/bin/env python3
"""Audit fe947dc3e12c for a bounding-box-area ranking shortcut."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Callable

WORK = Path(__file__).resolve().parents[3]
GENERATOR = WORK / "repo/generators/fe947dc3e12c/generator.py"
CANONICAL = WORK / "repo/shared/data/canonical/puzzles.jsonl"
OUT_DIR = Path(__file__).resolve().parent
SEED = 947031
RANK_COLORS = (1, 4, 2)


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_fe", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            seen.add((r, c))
            stack = [(r, c)]
            cells: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            objects.append(cells)
    return objects


def bbox_area(cells: list[tuple[int, int]]) -> int:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def recolor_by(
    grid: list[list[int]], key: Callable[[list[tuple[int, int]]], int]
) -> list[list[int]]:
    out = [row[:] for row in grid]
    # Python's stable sort supplies the rival's explicit scan-order tie-break.
    ranked = sorted(components(grid), key=key, reverse=True)
    for rank, cells in enumerate(ranked):
        if rank >= len(RANK_COLORS):
            break
        for r, c in cells:
            out[r][c] = RANK_COLORS[rank]
    return out


def authority_mirror(grid: list[list[int]]) -> list[list[int]]:
    return recolor_by(grid, len)


def bbox_area_rival(grid: list[list[int]]) -> list[list[int]]:
    return recolor_by(grid, bbox_area)


def canonical_pairs() -> list[dict]:
    for line in CANONICAL.read_text().splitlines():
        task = json.loads(line)
        if task.get("task_id") == "fe947dc3e12c":
            test = task.get("test")
            tests = test if isinstance(test, list) else [test]
            return [*task.get("train", []), *[pair for pair in tests if pair]]
    raise RuntimeError("canonical task not found")


def shape_meta(grid: list[list[int]]) -> dict[str, object]:
    objects = components(grid)
    return {
        "sizes_in_scan_order": [len(cells) for cells in objects],
        "bbox_areas_in_scan_order": [bbox_area(cells) for cells in objects],
        "source_colors": sorted({v for row in grid for v in row if v != 0}),
    }


def main() -> None:
    module = load_generator()
    pairs = canonical_pairs()
    canonical_matches = sum(
        bbox_area_rival(pair["input"]) == pair["output"] for pair in pairs
    )

    bands: dict[str, dict[str, int]] = {}
    samples: dict[str, dict[int, dict[str, object]]] = {}
    for band in ("easy", "medium", "hard"):
        rows: dict[int, dict[str, object]] = {}
        canonical_palette = 0
        varied_palette = 0
        matches = 0
        for sample_index in range(300):
            grid = module.generate(SEED, sample_index, difficulty=band)
            errors = module.self_check(grid)
            if errors:
                raise AssertionError((band, sample_index, errors))
            actual = authority_mirror(grid)
            rival = bbox_area_rival(grid)
            meta = shape_meta(grid)
            palette = "canonical" if meta["source_colors"] == [5] else "varied"
            canonical_palette += palette == "canonical"
            varied_palette += palette == "varied"
            matches += rival == actual
            rows[sample_index] = {
                "input": grid,
                "actual": actual,
                "rival": rival,
                "match": rival == actual,
                "palette": palette,
                **meta,
            }
        samples[band] = rows
        bands[band] = {
            "generated": len(rows),
            "self_check_passed": len(rows),
            "rival_matches": matches,
            "canonical_palette": canonical_palette,
            "varied_palette": varied_palette,
        }

    # Prefer a clean disagreement with distinct bounding-box areas, so the rival
    # requires no tie to disagree.  The three immediately preceding samples are
    # a concrete three-demo lesson on which the rival fits.
    selected: dict[str, object] | None = None
    for band in ("easy", "medium", "hard"):
        rows = samples[band]
        for query_index in range(3, 300):
            query = rows[query_index]
            if query["match"]:
                continue
            areas = query["bbox_areas_in_scan_order"]
            if len(set(areas)) != len(areas):
                continue
            demo_indices = list(range(query_index - 3, query_index))
            if all(rows[index]["match"] for index in demo_indices):
                selected = {
                    "band": band,
                    "seed": SEED,
                    "demo_indices": demo_indices,
                    "query_index": query_index,
                    "demo_meta": [
                        {
                            "sample_index": index,
                            "palette": rows[index]["palette"],
                            "sizes_in_scan_order": rows[index]["sizes_in_scan_order"],
                            "bbox_areas_in_scan_order": rows[index]["bbox_areas_in_scan_order"],
                        }
                        for index in demo_indices
                    ],
                    "query_meta": {
                        "palette": query["palette"],
                        "sizes_in_scan_order": query["sizes_in_scan_order"],
                        "bbox_areas_in_scan_order": query["bbox_areas_in_scan_order"],
                    },
                    "inputs": [rows[index]["input"] for index in [*demo_indices, query_index]],
                    "authority_mirror_outputs": [
                        rows[index]["actual"] for index in [*demo_indices, query_index]
                    ],
                    "rival_outputs": [
                        rows[index]["rival"] for index in [*demo_indices, query_index]
                    ],
                }
                break
        if selected is not None:
            break
    if selected is None:
        raise AssertionError("no clean three-demo ambiguity found")

    # Probe two API contract failures without treating them as semantic counts.
    ignored_override_cases: list[dict[str, object]] = []
    for kwargs in ({"bogus": 123}, {"size_1": 9}):
        try:
            grid = module.generate(7, 0, difficulty="easy", **kwargs)
        except Exception as exc:  # pragma: no cover - evidence branch
            ignored_override_cases.append(
                {"kwargs": kwargs, "accepted": False, "error": f"{type(exc).__name__}: {exc}"}
            )
        else:
            ignored_override_cases.append(
                {
                    "kwargs": kwargs,
                    "accepted": True,
                    "observed_sizes": module.observe_overrides(grid),
                    "shape": [len(grid), len(grid[0])],
                }
            )

    report = {
        "task_id": "fe947dc3e12c",
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "seed": SEED,
        "sample_indices": [0, 299],
        "canonical_pairs": len(pairs),
        "canonical_rival_matches": canonical_matches,
        "bands": bands,
        "ordinary_total": sum(v["generated"] for v in bands.values()),
        "ordinary_rival_matches": sum(v["rival_matches"] for v in bands.values()),
        "selected_lesson": {
            key: value for key, value in selected.items()
            if key not in ("inputs", "authority_mirror_outputs", "rival_outputs")
        },
        "ignored_override_cases": ignored_override_cases,
    }
    (OUT_DIR / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    (OUT_DIR / "lesson_inputs.json").write_text(
        json.dumps(selected["inputs"], indent=2) + "\n"
    )
    (OUT_DIR / "authority_mirror_outputs.json").write_text(
        json.dumps(selected["authority_mirror_outputs"], indent=2) + "\n"
    )
    (OUT_DIR / "rival_lesson_outputs.json").write_text(
        json.dumps(
            {
                "rival": "rank_objects_by_bounding_box_area_descending",
                "outputs": selected["rival_outputs"],
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
