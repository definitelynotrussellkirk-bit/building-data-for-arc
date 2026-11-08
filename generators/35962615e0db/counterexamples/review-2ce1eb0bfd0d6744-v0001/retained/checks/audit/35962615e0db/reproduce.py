"""Findings-only, source-bound audit using the selected public Racket executor.

Run from the packet root with the documented review.py runtime wrapper.
Only files beside this script are written; audited source remains unchanged.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "35962615e0db"
EXPECTED_SOURCE = "b4debe654591430d78f3d6f2686b7446627e721ac0d959a92da61d8b5c01d2da"
HERE = Path(__file__).resolve().parent
ROOT = find_root(Path.cwd())
WORK = ROOT.parent
PACKET = WORK.parent
ARGV = [
    "WORK/.venv/bin/python", "review.py", "run", "../.venv/bin/python",
    "../checks/audit/35962615e0db/reproduce.py",
]
ENV = {
    "TMPDIR": "/dev/shm/arcpuzzles-e5d955d3cc6a",
    "PYTHONDONTWRITEBYTECODE": "1",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(name: str, value) -> None:
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def proper_yellow_frames(grid):
    """Independent four-connected component/perimeter check, with real interiors."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4}
    frames = []
    while remaining:
        start = remaining.pop()
        stack, cells = [start], {start}
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        border = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                  if r in (r1, r2) or c in (c1, c2)}
        if r2 - r1 >= 2 and c2 - c1 >= 2 and cells == border:
            frames.append([r1, c1, r2, c2])
    return sorted(frames, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)


def observe(grid, gen):
    return {
        "height": len(grid), "width": len(grid[0]),
        "blue_markers": sum(value == 1 for row in grid for value in row),
        "colors": sorted({value for row in grid for value in row}),
        "proper_yellow_frames": proper_yellow_frames(grid),
        "self_check": gen.self_check(grid),
    }


def cyan_cells(grid):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8}


def main() -> int:
    gen, source, source_hash = load_selected_generator(TASK_ID, root=ROOT)
    assert source_hash == EXPECTED_SOURCE, ("Source changed; audit must be re-triaged", source_hash)
    notes = source.parent / "notes.md"
    notes_hash = sha(notes)
    index = source.parent / "evidence/review_index.json"
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        canonical_records = [json.loads(line) for line in handle if line.strip()]
    selected = [row for row in canonical_records if row.get("task_id") == TASK_ID]
    assert len(selected) == 1
    program_hash = hashlib.sha256(selected[0]["program_solution"].encode()).hexdigest()
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    cases, inputs = [], []

    def add(name, grid, **metadata):
        case_index = len(inputs)
        inputs.append(grid)
        cases.append({"case_index": case_index, "name": name, **metadata, **observe(grid, gen)})
        return case_index

    for pair in pairs:
        add(f"canonical_{pair['split']}_{pair['pair_index']}", pair["input"],
            variant=pair["variant"], split=pair["split"], pair_index=pair["pair_index"],
            origin="canonical", documented_frame_domain=True)

    default = gen.generate(0, 0, difficulty="easy")
    default_index = add("default_easy_seed0_index0", default, origin="generated",
                        seed=0, sample_index=0, difficulty="easy", overrides={},
                        documented_frame_domain=True)
    assert (len(default), len(default[0])) == (14, 15)
    override_rows = []
    for overrides in (
        {"grid_h": 11, "grid_w": 24}, {"grid_h": 24, "grid_w": 11},
        {"grid_h": 0, "grid_w": 31}, {"palette_kind": "invalid"},
        {"texture": "invalid"}, {"unknown_axis": "invented"},
    ):
        grid = gen.generate(0, 0, difficulty="easy", **overrides)
        assert grid == default
        override_rows.append({"seed": 0, "sample_index": 0, "difficulty": "easy",
                              "overrides": overrides, "same_as_default": True,
                              "reference_case_index": default_index, **observe(grid, gen)})

    census = []
    for band in ("easy", "medium", "hard"):
        failures = []
        structural_failures = []
        for sample_index in range(64):
            grid = gen.generate(0, sample_index, difficulty=band)
            observation = observe(grid, gen)
            assert observation["self_check"] == []
            frames = observation["proper_yellow_frames"]
            if not 2 <= len(frames) <= 5:
                structural_failures.append(sample_index)
            if not (11 <= len(grid) <= 24 and 11 <= len(grid[0]) <= 24):
                failures.append({"sample_index": sample_index, "height": len(grid), "width": len(grid[0])})
        census.append({"difficulty": band, "seed": 0, "sample_index_range_inclusive": [0, 63],
                       "draw_count": 64, "outside_declared_dimension_range": len(failures),
                       "dimension_failures": failures, "frame_count_failures": structural_failures,
                       "reference_label_census": False})
    assert [row["outside_declared_dimension_range"] for row in census] == [5, 10, 30]
    add("default_easy_seed0_index1", gen.generate(0, 1, difficulty="easy"), origin="generated",
        seed=0, sample_index=1, difficulty="easy", overrides={}, documented_frame_domain=True)
    add("default_hard_seed0_index2", gen.generate(0, 2, difficulty="hard"), origin="generated",
        seed=0, sample_index=2, difficulty="hard", overrides={}, documented_frame_domain=True)

    original = gen.generate(0, 11, difficulty="easy")
    original_index = add("broken_frame_original", original, origin="generated",
                         seed=0, sample_index=11, difficulty="easy", overrides={},
                         documented_frame_domain=True)
    frames = proper_yellow_frames(original)
    assert len(frames) == 2
    assert sum(value == 1 for row in original for value in row) == 1
    r1, c1, _, _ = frames[0]
    broken = copy.deepcopy(original)
    assert broken[r1][c1] == 4
    broken[r1][c1] = 0
    broken_index = add("broken_outer_frame", broken, origin="one_cell_mutation",
                       source_case_index=original_index, source_seed=0, source_sample_index=11,
                       source_difficulty="easy", mutation={"row": r1, "column": c1, "before": 4, "after": 0},
                       documented_frame_domain=False, generated_by_default=False)
    assert gen.self_check(broken) == []
    assert len(proper_yellow_frames(broken)) == 1
    tiny_index = add("no_hollow_frame_or_fillable_band", [[1, 4]], origin="hand_built",
                     documented_frame_domain=False, generated_by_default=False)
    assert gen.self_check(inputs[tiny_index]) == []
    malformed = [
        {"name": "ragged", "input": [[1, 4], [0]]},
        {"name": "invalid_arc_color", "input": [[1, 4], [0, 99]]},
    ]
    for row in malformed:
        row["self_check"] = gen.self_check(row["input"])
        row["reference_executed"] = False
        assert row["self_check"] == []

    write_json("input.json", {"inputs": inputs})
    before_inputs = copy.deepcopy(inputs)
    receipt = Catalog(root=ROOT).apply(TASK_ID, inputs, timeout=120)
    write_json("racket.json", receipt)
    assert inputs == before_inputs
    results = receipt["results"]
    assert len(results) == len(inputs) == 11
    assert all(row["error"] is None and row["valid_output"] for row in results)
    assert receipt["generator_sha256"] == source_hash
    assert receipt["executed_rule_hash"] == "38f679dfa901"
    assert receipt["rule_hash_matches_catalog"] is True
    canonical_matches = [results[i]["output"] == pair["output"] for i, pair in enumerate(pairs)]
    assert all(canonical_matches)
    for case, grid, result in zip(cases, inputs, results, strict=True):
        case["reference_output_dimensions"] = [len(result["output"]), len(result["output"][0])]
        case["reference_changed_cell_count"] = sum(a != b for ar, br in zip(grid, result["output"], strict=True)
                                                   for a, b in zip(ar, br, strict=True))
        case["reference_cyan_cell_count"] = len(cyan_cells(result["output"]))
    original_fill = cyan_cells(results[original_index]["output"])
    broken_fill = cyan_cells(results[broken_index]["output"])
    assert original_fill and broken_fill and original_fill.isdisjoint(broken_fill)
    assert results[tiny_index]["output"] == inputs[tiny_index]
    assert sha(source) == source_hash and sha(notes) == notes_hash

    evidence_paths = [f"checks/audit/{TASK_ID}/{name}" for name in
                      ("reproduce.py", "input.json", "racket.json", "audit.json", "audit.md", "reproduce.log")]
    report = {
        "schema": "arcpuzzles-focused-audit-v1", "task_id": TASK_ID,
        "classification": "reproduced override-contract and validator defects; no wrong-reference-label claim",
        "generator_sha256": source_hash, "generator_version": gen.VERSION,
        "notes_sha256": notes_hash, "review_index_present": index.is_file(),
        "canonical_program_sha256": program_hash,
        "executed_rule_hash": receipt["executed_rule_hash"],
        "executed_rule_text_sha256": receipt["rule_text_sha256"],
        "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
        "source_and_notes_unchanged": True, "script_sha256": sha(Path(__file__)),
        "command": {"argv": ARGV, "cwd": "packet_root", "absolute_cwd": str(PACKET),
                    "payload_cwd": "repo", "absolute_payload_cwd": str(ROOT),
                    "env": ENV, "exit_code": 0, "evidence_paths": evidence_paths},
        "public_reference_call": {"api": "Catalog(root=ROOT).apply", "task_id": TASK_ID,
                                  "input_count": len(inputs), "timeout": 120},
        "reference_counts": {"executed": len(inputs), "valid_outputs": len(inputs),
                             "execution_errors": 0, "canonical_labels_matched": sum(canonical_matches),
                             "canonical_labels_checked": len(pairs)},
        "override_cases": override_rows, "default_dimension_census": census,
        "reference_cases": cases, "validator_only_cases": malformed,
        "broken_frame_comparison": {"original_case": original_index, "mutant_case": broken_index,
                                    "original_cyan_count": len(original_fill), "mutant_cyan_count": len(broken_fill),
                                    "cyan_regions_disjoint": True},
        "artifact_sha256": {name: sha(HERE / name) for name in ("input.json", "racket.json")},
        "limits": [
            "The 192-draw dimension census checks generated inputs, not 192 Racket labels.",
            "The broken frame, tiny grid, ragged grid, and color-99 grid are deliberate off-domain probes, not default generator outputs.",
            "Malformed ARC grids were checked only with self_check and were not submitted to the reference executor.",
            "No corpus-wide lesson census, query-rotation claim, task admission decision, or target source change was made.",
        ],
    }
    write_json("audit.json", report)
    audit = f"""## {TASK_ID}

**Finding A359-1: reproduced exact-override contract failure.** On generator `{source_hash}` (version `{gen.VERSION}`), `generate(0, 0, difficulty="easy", grid_h=11, grid_w=24)` returns the identical **14 × 15** grid as the unoverridden draw. Reversing those valid requests to 24 × 11 still produces that same grid. Invalid 0 × 31 requests, invalid palette/texture values, and an unknown axis are also silently accepted. The implementation declares these axes but samples dimensions directly from the placement RNG without consuming their overrides. Its lack of an observer is not the basis of this finding: the returned row/column counts directly contradict the exact requested values.

The source-bound input census uses seed 0 and indices 0–63 separately in each band: **5/64 easy, 10/64 medium, and 30/64 hard** draws lie outside the advertised 11..24 height/width range. These are metadata/parameter-contract violations, not ARC size violations or alleged incorrect labels. A 10 × 13 easy example and 27 × 26 hard example were independently labeled by the selected Racket rule. Suggested task-local follow-up: either implement and validate meaningful exact axes or remove/correct stale declarations, preserving the fixed semantic color roles. See `checks/audit/{TASK_ID}/audit.json` (`override_cases`, `default_dimension_census`) and the exact arrays in `input.json`.

**Finding A359-2: reproduced task-validator false acceptance.** The real default draw `generate(0, 11, difficulty="easy")` has two complete hollow yellow frames and one blue marker. Replacing its outer frame's corner at zero-based **({r1}, {c1})** from 4 to 0 leaves only one complete hollow frame, yet `self_check` still returns `[]`. The selected Racket execution then fills **{len(broken_fill)} innermost cells**, whereas the original fills **{len(original_fill)} inter-frame cells**; these cyan regions are disjoint. This is an invalid-input acceptance defect, not a claim that Racket should ignore the mutation. The off-domain mutation is explicitly distinguished from default sampling support.

The minimal valid-ARC grid `[[1,4]]` also passes `self_check`, despite having no hollow frame or fillable band; selected Racket returns it unchanged. Separately, `[[1,4],[0]]` (ragged) and `[[1,4],[0,99]]` (invalid color) pass the validator. Those two malformed grids were **not** submitted to Racket. The validator only checks nonemptiness, coarse maximum dimensions, and presence of colors 1 and 4. Suggested task-local follow-up: validate rectangular literal ARC grids, complete nested frame geometry/count/gaps, marker count, and a nonempty selected fill region, while keeping deliberately degenerate textures explicitly separate.

### Reference execution and scope

The public `Catalog.apply` call executed **11 inputs: 5 canonical pairs, 4 unmodified generated examples, and 2 deliberate validator probes**. All 11 outputs were valid with zero execution errors; all **5/5** canonical outputs matched the retained labels. The generated broken-frame original is included among the four unmodified examples. All inspected default inputs passed `self_check`; the 192-draw census found no default frame-count violation. No incorrect default reference label is alleged.

- Generator SHA-256: `{source_hash}`.
- Canonical program-text SHA-256: `{program_hash}`.
- Executed rule hash: `{receipt['executed_rule_hash']}`; catalog match: `true`.
- Executor rule-text SHA-256: `{receipt['rule_text_sha256']}`.
- Current `evidence/review_index.json`: absent; associated notes are empty.
- Generator and notes stayed unchanged. This audit is findings-only.

Exact replay from the outer packet directory:

```bash
TMPDIR=/dev/shm/arcpuzzles-e5d955d3cc6a PYTHONDONTWRITEBYTECODE=1 \\
WORK/.venv/bin/python review.py run ../.venv/bin/python \\
../checks/audit/{TASK_ID}/reproduce.py
```

Payload working directory is `WORK/repo`. The script uses `reviewer_support` to load the selected bytes/canonical data, calls public `Catalog.apply(..., timeout=120)`, and writes only its audit directory. The complete selected-reference receipt is `checks/audit/{TASK_ID}/racket.json`; `audit.json` retains exact source/rule identities, input indices, mutations, overrides, census denominators, command/working-directory/exit metadata, hashes, and limits. `reproduce.log` retains actual console output and the process exit code. No lesson census or whole-library suite was run.
"""
    (HERE / "audit.md").write_text(audit, encoding="utf-8")
    print(json.dumps({"task_id": TASK_ID, "generator_sha256": source_hash,
                      "findings": ["A359-1", "A359-2"], "reference_counts": report["reference_counts"],
                      "dimension_census_failures": [row["outside_declared_dimension_range"] for row in census],
                      "broken_frame_comparison": report["broken_frame_comparison"],
                      "source_unchanged": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
