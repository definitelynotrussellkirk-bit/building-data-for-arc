#!/usr/bin/env python3
"""Small Python-only audit probes; this does not invoke the Racket reference.

The task-specific Python translation is first compared with every supplied
canonical label. All other predicted labels remain explicitly Python-derived.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2] / "repo"
TASK = "974fee515740"
SOURCE = REPO / "generators" / TASK / "generator.py"
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("audited_generator_974", SOURCE)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def normalized(cells):
    if not cells:
        return set()
    low_r = min(r for r, c in cells)
    low_c = min(c for r, c in cells)
    return {(r - low_r, c - low_c) for r, c in cells}


def first_component(grid, color):
    height, width = len(grid), len(grid[0])
    start = next((r, c) for r in range(height) for c in range(width)
                 if grid[r][c] == color)
    found, pending = {start}, [start]
    while pending:
        r, c = pending.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p = r + dr, c + dc
            if (0 <= p[0] < height and 0 <= p[1] < width
                    and grid[p[0]][p[1]] == color and p not in found):
                found.add(p)
                pending.append(p)
    return normalized(found)


def render(cells):
    if not cells:
        return [[0]]
    cells = normalized(cells)
    return [[8 if (r, c) in cells else 0
             for c in range(1 + max(c for r, c in cells))]
            for r in range(1 + max(r for r, c in cells))]


def python_reference(grid, *, reverse_subtraction=False):
    """Direct translation of the selected canonical Racket rule, not Racket."""
    codes = [value for value in grid[0] if value != 0]
    op = codes[0] if codes and codes[0] in (3, 4, 6, 7) else 6
    rot = codes[1] if len(codes) > 1 and codes[1] in (1, 2, 3, 4) else 1
    red, blue = first_component(grid, 2), first_component(grid, 1)
    for unused in range(rot - 1):
        blue = normalized({(c, -r) for r, c in blue})
    if op == 3:
        result = red | blue
    elif op == 4:
        result = red & blue
    elif op == 6:
        result = red ^ blue
    else:
        result = blue - red if reverse_subtraction else red - blue
    return render(result)


def save(name, value):
    path = OUT / name
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main():
    canonical_path = REPO / "shared/data/canonical/puzzles.jsonl"
    canonical_digest = hashlib.sha256()
    pattern = re.compile(rb'"task_id"\s*:\s*"974fee515740"')
    selected = []
    with canonical_path.open("rb") as handle:
        for line_number, raw in enumerate(handle, 1):
            canonical_digest.update(raw)
            if pattern.search(raw):
                value = json.loads(raw)
                if value.get("task_id") == TASK:
                    selected.append((line_number, raw, value))
    assert len(selected) == 1
    line_number, record_raw, record = selected[0]
    canonical_checks = [
        {"split": split, "index": index,
         "matches_supplied_label": python_reference(pair["input"]) == pair["output"]}
        for split in ("train", "test")
        for index, pair in enumerate(record[split])
    ]
    assert all(row["matches_supplied_label"] for row in canonical_checks)
    result = {
        "task_id": TASK,
        "verification_kind": "Python-only; no Racket execution",
        "racket_verification": "pending",
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical_file_sha256": canonical_digest.hexdigest(),
        "canonical_record_line": line_number,
        "canonical_record_sha256": hashlib.sha256(record_raw).hexdigest(),
        "rule_hash": hashlib.sha256(" ".join(record["program_solution"].split()).encode()).hexdigest()[:12],
        "canonical_translation_checks": canonical_checks,
    }
    no_overlap = generator.generate(seed=17, sample_index=0, texture="no_overlap")
    result["no_overlap_texture"] = {
        "self_check": generator.self_check(no_overlap),
        "first_red_mask": sorted(first_component(no_overlap, 2)),
        "first_blue_mask": sorted(first_component(no_overlap, 1)),
        "python_predicted_output": python_reference(no_overlap),
        "claim_in_generator": "red and blue cannot overlap under any rotation",
    }
    save("no-overlap-input.json", no_overlap)

    seed = 17
    samples = {}
    color_counts = {}
    code_counts = {}
    for band in ("easy", "medium", "hard"):
        samples[band] = [generator.generate(seed=seed, sample_index=i, difficulty=band)
                         for i in range(32)]
        color_counts[band] = {}
        code_counts[band] = {}
        for grid in samples[band]:
            colors = len({value for row in grid for value in row})
            color_counts[band][str(colors)] = color_counts[band].get(str(colors), 0) + 1
            rot = str(grid[0][1])
            code_counts[band][rot] = code_counts[band].get(rot, 0) + 1
    result["bounded_sample"] = {"seed": seed, "samples_per_band": 32,
                               "all_color_count_histogram": color_counts,
                               "rotation_code_histogram": code_counts}

    baseline = samples["medium"][0]
    override_checks = []
    for option in ({"palette_kind": "warm"}, {"palette_kind": "cool"},
                   {"palette_kind": "varied"}, {"texture": "warm"},
                   {"texture": "cool"}, {"texture": "varied"},
                   {"palette_size": 4}, {"n_distinct_colors": 4},
                   {"n_shapes": 3}, {"palette_kind": "not_a_palette"}):
        row = {"overrides": option}
        try:
            grid = generator.generate(seed=seed, sample_index=0, difficulty="medium", **option)
            row.update({"accepted": True, "identical_to_no_override": grid == baseline,
                        "all_colors": sorted({value for line in grid for value in line}),
                        "self_check": generator.self_check(grid)})
        except Exception as exc:
            row.update({"accepted": False, "error": f"{type(exc).__name__}: {exc}"})
        override_checks.append(row)
    result["override_checks"] = override_checks

    # Find a small consecutive generator sequence, not a production-sampler
    # episode: the natural directional-subtraction rival fits demonstrations
    # but differs on a code-7 query. No claim about production lesson frequency.
    lesson = None
    grids = samples["medium"]
    for start in range(len(grids) - 3):
        demos, query = grids[start:start + 3], grids[start + 3]
        if (all(python_reference(g) == python_reference(g, reverse_subtraction=True) for g in demos)
                and python_reference(query) != python_reference(query, reverse_subtraction=True)):
            lesson = {
                "task_id": TASK,
                "kind": "candidate lesson from consecutive direct generator calls; not production-sampler evidence",
                "label_provenance": "Python translation matching all supplied canonical labels; Racket pending",
                "seed": seed, "difficulty": "medium",
                "sample_indices": list(range(start, start + 4)),
                "rival": "For operation code 7 use blue-minus-red instead of red-minus-blue; all other logic unchanged",
                "train": [{"input": g, "output": python_reference(g)} for g in demos],
                "test": [{"input": query, "python_reference_prediction": python_reference(query),
                          "python_rival_prediction": python_reference(query, reverse_subtraction=True)}],
            }
            break
    result["candidate_teaching_witness_found"] = lesson is not None
    apply_inputs = [no_overlap]
    if lesson is not None:
        save("candidate-lesson-python.json", lesson)
        apply_inputs += [p["input"] for p in lesson["train"]]
        apply_inputs += [lesson["test"][0]["input"]]
        result["candidate_teaching_sample_indices"] = lesson["sample_indices"]
    save("reference-apply-inputs.json", apply_inputs)
    save("python-probe-results.json", result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
