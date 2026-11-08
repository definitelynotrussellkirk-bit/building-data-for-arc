"""Bounded findings-only audit; run through the packet's public wrapper."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

TASK = "cdb0009458df"
OUT = Path(__file__).resolve().parent
catalog = Catalog()
source = catalog.root / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audited_generator", source)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def digest(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    path = OUT / name
    if path.exists():
        assert path.read_bytes() == raw, f"Refuse to replace differing evidence: {path}"
    else:
        path.write_bytes(raw)


def objects(grid, color):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        cells, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append(cells)
    return result


def bbox(cells):
    return (min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells))


def frames(grid):
    result = []
    for cells in objects(grid, 5):
        r1, c1, r2, c2 = bbox(cells)
        ring = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                if r in (r1, r2) or c in (c1, c2)}
        if r2 - r1 >= 2 and c2 - c1 >= 2 and cells == ring:
            result.append((r1, c1, r2, c2))
    return sorted(result)


def copy_template(grid, fixed_shape=None):
    template = min(objects(grid, 1), key=bbox)
    top, left, _, _ = bbox(template)
    shape = fixed_shape if fixed_shape is not None else [(r - top, c - left) for r, c in template]
    output = [row[:] for row in grid]
    for r1, c1, r2, c2 in frames(grid):
        markers = [(r, c, grid[r][c]) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)
                   if grid[r][c] not in (0, 5)]
        if not markers:
            continue
        mr, mc, color = markers[-1]
        output[mr][mc] = 0
        for dr, dc in shape:
            output[r1 + 1 + dr][c1 + 1 + dc] = color
    return output


FIXED_T = [(0, 0), (0, 1), (0, 2), (1, 1)]


def prepare():
    rows = []
    witness = None
    for seed in (0, 1):
        for difficulty in ("easy", "medium", "hard"):
            grid = generator.generate(seed, 0, difficulty=difficulty)
            if seed == 1 and difficulty == "easy":
                witness = grid
            template_box = bbox(objects(grid, 1)[0])
            frame_boxes = frames(grid)
            controls = []
            for axis in ("palette_kind", "texture"):
                for value in ("default", "warm", "cool", "varied"):
                    varied = generator.generate(seed, 0, difficulty=difficulty, **{axis: value})
                    controls.append({"overrides": {axis: value}, "input_sha256": digest(varied),
                                     "identical_to_unoverridden": varied == grid,
                                     "self_check": generator.self_check(varied, difficulty=difficulty)})
            rows.append({"seed": seed, "sample_index": 0, "difficulty": difficulty,
                         "overrides": {}, "input_sha256": digest(grid),
                         "self_check": generator.self_check(grid, difficulty=difficulty),
                         "template_bbox": template_box, "frame_bboxes": frame_boxes,
                         "template_before_all_frames": all(template_box[:2] < box[:2] for box in frame_boxes),
                         "controls": controls})
    pairs = canonical_pairs(TASK, root=catalog.root, labeled_only=True)
    canonical = [{"variant": p["variant"], "split": p["split"], "pair_index": p["pair_index"],
                  "input_sha256": digest(p["input"]),
                  "independent_python_fits": copy_template(p["input"]) == p["output"],
                  "hardcoded_T_rival_fits": copy_template(p["input"], FIXED_T) == p["output"]}
                 for p in pairs]
    assert all(row["independent_python_fits"] and row["hardcoded_T_rival_fits"] for row in canonical)
    assert all(control["identical_to_unoverridden"] and not control["self_check"]
               for row in rows for control in row["controls"])
    assert witness is not None
    witness_row = next(row for row in rows if row["seed"] == 1 and row["difficulty"] == "easy")
    assert not witness_row["self_check"] and not witness_row["template_before_all_frames"]
    description = catalog.describe(TASK)
    probe = {"schema": "arcpuzzles-bounded-audit-v1", "task_id": TASK,
             "generator_version": generator.VERSION, "generator_sha256": digest(source.read_bytes()),
             "catalog_rule_hash": description["rule_hash"], "generation_call_count": 54,
             "baseline_draw_count": 6, "paired_control_comparisons": 48,
             "identical_control_comparisons": sum(c["identical_to_unoverridden"] for row in rows for c in row["controls"]),
             "baseline_reading_order_violations": sum(not row["template_before_all_frames"] for row in rows),
             "canonical_checks": canonical, "draws": rows, "witness": witness_row,
             "declared_invariants": generator.INVARIANTS,
             "witness_input_shape": [len(witness), len(witness[0])],
             "scope": "No production source edits; declared controls and reading order checked on six baseline draws only."}
    save("input.json", witness)
    save("python_expected.json", copy_template(witness))
    save("rival.json", {"name": "fixed_canonical_T_shape", "kind": "diagnostic shortcut",
                        "description": "Ignore the color-1 motif and always stamp the canonical four-cell T shape.",
                        "output": copy_template(witness, FIXED_T)})
    save("probe.json", probe)
    print(json.dumps({k: probe[k] for k in ("task_id", "generation_call_count", "paired_control_comparisons",
                                           "identical_control_comparisons", "baseline_reading_order_violations", "witness_input_shape")}))


def verify():
    probe = json.loads((OUT / "probe.json").read_text())
    applied = json.loads((OUT / "racket.json").read_text())
    grid = json.loads((OUT / "input.json").read_text())
    expected = json.loads((OUT / "python_expected.json").read_text())
    rival = json.loads((OUT / "rival.json").read_text())
    assert applied["generator_sha256"] == probe["generator_sha256"] == digest(source.read_bytes())
    assert len(applied["results"]) == 1 and applied["results"][0]["input"] == grid
    actual = applied["results"][0]
    assert actual["error"] is None and actual["input_sha256"] == digest(grid)
    assert actual["output"] == expected, "Public Racket output differs from independent implementation"
    assert actual["output"] != rival["output"], "This witness failed to refute the hardcoded-T shortcut"
    diffs = [{"row": r, "column": c, "actual": v, "rival": rival["output"][r][c]}
             for r, row in enumerate(actual["output"]) for c, v in enumerate(row) if v != rival["output"][r][c]]
    finding = {"task_id": TASK, "finding_ids": ["A1", "A2"],
               "classifications": {"A1": "reproduced ignored advertised controls", "A2": "reproduced declared invariant and validator mismatch"},
               "generator_sha256": probe["generator_sha256"],
               "executed_rule_hash": applied["executed_rule_hash"], "rule_text_sha256": applied["rule_text_sha256"],
               "seed": 1, "sample_index": 0, "difficulty": "easy", "overrides": {},
               "self_check": generator.self_check(grid, difficulty="easy"),
               "generated_by_unmodified_target": True,
               "literal_documented_reading_order_invariant": False,
               "input": grid, "input_sha256": digest(grid), "actual_racket_output": actual["output"],
               "rival": rival, "rival_disagrees_at": diffs, "independent_python_matches_racket": True,
               "canonical_shortcut_fit": {"passed": len(probe["canonical_checks"]), "total": len(probe["canonical_checks"]),
                                          "scope": "all labeled canonical pairs; the generated witness refutes this shortcut"},
               "reference_command": {"cwd": "packet_root", "payload_cwd": "repo",
                   "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                            "--input", "../checks/audit/cdb0009458df/input.json", "--out", "../checks/audit/cdb0009458df/racket.json"],
                   "exit_code": 0, "effective_reference_cwd": applied["cwd"],
                   "evidence_paths": ["checks/audit/cdb0009458df/racket.json", "checks/audit/cdb0009458df/finding.json"]},
               "limitations": "No wrong Racket label was found. A1 and A2 concern the generator contract. The six baseline draws and one Racket witness are not an exhaustive semantic or lesson-identifiability audit."}
    save("finding.json", finding)
    print(json.dumps({"verification": "passed", "rival_changed_cell_count": len(diffs),
                      "generator_sha256": finding["generator_sha256"], "executed_rule_hash": finding["executed_rule_hash"]}))


if len(sys.argv) != 2 or sys.argv[1] not in ("prepare", "verify"):
    raise SystemExit("Usage: python3 reproduce.py prepare|verify (through run_with_racket.py)")
prepare() if sys.argv[1] == "prepare" else verify()
