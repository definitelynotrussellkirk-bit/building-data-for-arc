#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
OUT = ROOT / "checks" / "audit"


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def same_colour_components(grid, colours=None):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            colour = grid[r][c]
            if colour == 0 or (colours is not None and colour not in colours) or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == colour:
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append((colour, cells))
    return result


def norm(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def canonical_row(task_id):
    with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return row
    raise KeyError(task_id)


def audit_75():
    task = "75c10ce4046c"
    module, source_path = load_generator(task)
    generated = {}
    all_source_sizes = Counter()
    all_candidate_sizes = Counter()
    all_source_shapes = Counter()
    for band in ("easy", "medium", "hard"):
        band_sources = Counter()
        band_candidates = Counter()
        for sample_index in range(300):
            grid = module.generate(0x75C10CE4, sample_index, difficulty=band)
            sources = same_colour_components(grid, {2})
            candidates = same_colour_components(grid, {3, 4, 5, 6})
            assert len(sources) == 1
            source_size = len(sources[0][1])
            band_sources[source_size] += 1
            all_source_sizes[source_size] += 1
            all_source_shapes[norm(sources[0][1])] += 1
            for _, cells in candidates:
                band_candidates[len(cells)] += 1
                all_candidate_sizes[len(cells)] += 1
        generated[band] = {
            "draws": 300,
            "source_cell_counts": dict(sorted(band_sources.items())),
            "candidate_component_cell_counts": dict(sorted(band_candidates.items())),
        }

    override_observations = []
    for sample_index in range(40):
        grid = module.generate(0xA11CE, sample_index, difficulty="medium", matching_candidates=3)
        source = norm(same_colour_components(grid, {2})[0][1])
        candidates = same_colour_components(grid, {3, 4, 5, 6})
        matches = sum(norm(cells) == source for _, cells in candidates)
        override_observations.append(matches)

    canonical = canonical_row(task)
    test_examples = canonical["test"] if isinstance(canonical["test"], list) else [canonical["test"]]
    canonical_examples = list(canonical["train"]) + list(test_examples)
    canonical_counts = []
    for idx, example in enumerate(canonical_examples):
        grid = example["input"]
        sources = same_colour_components(grid, {2})
        candidates = same_colour_components(grid, {3, 4, 5, 6})
        canonical_counts.append({
            "example_index": idx,
            "split": "train" if idx < len(canonical["train"]) else "test",
            "source_cell_counts": [len(cells) for _, cells in sources],
            "candidate_cell_counts": [len(cells) for _, cells in candidates],
        })

    report = {
        "schema": "assigned-audit-probe-v1",
        "task_id": task,
        "generator_path": str(source_path.relative_to(ROOT)),
        "generator_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "finding": "generator support is restricted to five fixed tetromino signatures; the canonical test uses five-cell objects",
        "generated": generated,
        "aggregate_generated_source_cell_counts": dict(sorted(all_source_sizes.items())),
        "aggregate_generated_candidate_cell_counts": dict(sorted(all_candidate_sizes.items())),
        "unique_generated_source_signatures": len(all_source_shapes),
        "canonical_component_counts": canonical_counts,
        "matching_candidates_override_requested": 3,
        "matching_candidates_override_observed_counts": dict(sorted(Counter(override_observations).items())),
        "matching_candidates_override_honoured_all_draws": all(v == 3 for v in override_observations),
        "limitations": [
            "Finite sampling cannot prove a property of arbitrary source edits; the fixed _SHAPES table makes the four-cell restriction source-verifiable.",
            "The constructed five-cell witness is authority-valid but is outside the selected generator's current support."
        ],
    }
    out_path = OUT / task / "probe.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def beam_output(grid, *, blockers_enabled):
    h, w = len(grid), len(grid[0])
    corners = ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
    markers = [(r, c, grid[r][c]) for r, c in corners if grid[r][c] in {1, 2, 3, 4}]
    if not markers:
        raise ValueError("no marker")
    mr, mc, marker_colour = markers[0]
    dr, dc = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}[marker_colour]
    blockers = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    out = copy.deepcopy(grid)
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value in (0, 5) or (r, c) == (mr, mc):
                continue
            rr, cc = r + dr, c + dc
            while 0 <= rr < h and 0 <= cc < w:
                if blockers_enabled and (rr, cc) in blockers:
                    break
                out[rr][cc] = value
                rr += dr
                cc += dc
    return out


def audit_b91():
    task = "b91a3b0baac4"
    module, source_path = load_generator(task)
    stats = {}
    all_equal = 0
    all_draws = 0
    for band in ("easy", "medium", "hard"):
        same = 0
        with_blockers = 0
        draws = 600
        for sample_index in range(draws):
            grid = module.generate(0xB91A3B0B, sample_index, difficulty=band)
            if any(5 in row for row in grid):
                with_blockers += 1
            canonical = beam_output(grid, blockers_enabled=True)
            ignore = beam_output(grid, blockers_enabled=False)
            if canonical == ignore:
                same += 1
        stats[band] = {
            "draws": draws,
            "draws_with_at_least_one_blocker": with_blockers,
            "ignore_blockers_same_output": same,
            "ignore_blockers_same_fraction": same / draws,
        }
        all_equal += same
        all_draws += draws

    witness = None
    # Find a six-example lesson where the blocker-ignoring rival fits all five
    # demonstrations but disagrees on the query.
    for seed in range(1, 500):
        if witness is not None:
            break
        for start in range(0, 80):
            examples = []
            for sample_index in range(start, start + 6):
                grid = module.generate(seed, sample_index, difficulty="medium")
                truth = beam_output(grid, blockers_enabled=True)
                rival = beam_output(grid, blockers_enabled=False)
                examples.append({
                    "sample_index": sample_index,
                    "input": grid,
                    "authority_mirror_output": truth,
                    "ignore_blockers_output": rival,
                    "rival_fits": truth == rival,
                })
            if all(item["rival_fits"] for item in examples[:5]) and not examples[5]["rival_fits"]:
                witness = {
                    "seed": seed,
                    "difficulty": "medium",
                    "start_sample_index": start,
                    "demonstrations": examples[:5],
                    "query": examples[5],
                }
                break
    if witness is None:
        raise RuntimeError("no blocker-survival lesson found in bounded search")

    report = {
        "schema": "assigned-audit-probe-v1",
        "task_id": task,
        "generator_path": str(source_path.relative_to(ROOT)),
        "generator_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "finding": "random blocker placement often leaves the ignore-blockers rival observationally equivalent, including complete five-demo lessons",
        "sample_stats": stats,
        "aggregate_ignore_blockers_same_fraction": all_equal / all_draws,
        "lesson_witness": witness,
        "limitations": [
            "The five-demo lesson assembly is a simple consecutive-window probe, not proof about every downstream sampler.",
            "The Python authority mirror directly follows the canonical program; the retained query is separately checked with Racket."
        ],
    }
    out_path = OUT / task / "probe.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    query_input = witness["query"]["input"]
    (OUT / task / "racket_query_input.json").write_text(json.dumps(query_input) + "\n")
    return report


if __name__ == "__main__":
    reports = [audit_75(), audit_b91()]
    print(json.dumps({
        "reports": [
            {
                "task_id": report["task_id"],
                "generator_sha256": report["generator_sha256"],
                "finding": report["finding"],
            }
            for report in reports
        ]
    }, indent=2))
