"""Bounded source-bound Racket parity and lesson-contract verification."""
import copy
import hashlib
import json
from pathlib import Path
import time

from arcpuzzles import Catalog
from arcpuzzles.runtime import GenerationFailure, apply_rule
from arcpuzzles.worker import lesson_check
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK = "5ca74a85bc85"
ROOT = find_root(__file__)
OUT = ROOT.parent / "checks" / TASK / "racket-and-adversarial.json"
START = time.monotonic()
module, source, digest = load_selected_generator(TASK, root=ROOT)
catalog = Catalog(ROOT)
audited = [module.generate(0, index) for index in (3, 4, 5, 6)]
cases = [(f"audit_{index}", grid) for index, grid in zip((3, 4, 5, 6), audited)]
for band in ("easy", "medium", "hard"):
    for profile in ("multicolor_left", "multicolor_right", "boundary_mirror", "multiple_objects_left"):
        cases.append((f"{band}_{profile}", module.generate(83, 103, difficulty=band, scene_profile=profile)))
applied = apply_rule(catalog, TASK, [g for _, g in cases], check_generator_domain=True, timeout=90)
rows = []
for (name, grid), result in zip(cases, applied["results"], strict=True):
    assert result["error"] is None and result["valid_output"]
    assert result["generator_domain"] == {"status": "valid", "errors": []}
    assert result["output"] == module.rule_mirror(grid)
    before = copy.deepcopy(grid)
    predicted = module.LESSON_COMPETITORS["filled_source_bbox"](grid)
    assert predicted == module.LESSON_COMPETITORS["filled_source_bbox"](grid)
    assert grid == before
    rows.append({"case": name, "input_sha256": result["input_sha256"],
                 "output_sha256": result["output_sha256"], "racket_parity": True,
                 "rival_fits": predicted == result["output"]})
assert [row["rival_fits"] for row in rows[:4]] == [True, True, True, False]
pairs = [{"input": result["input"], "output": result["output"]} for result in applied["results"][:4]]
rotations = []
for held_out in range(4):
    episode = {"train": [pair for i, pair in enumerate(pairs) if i != held_out],
               "test": [pairs[held_out]]}
    before = copy.deepcopy(episode)
    verdict = lesson_check(module, episode, {"demonstration_policy": {"automatic": False, "declared_minimum": None}})
    assert episode == before
    assert verdict["status"] == ("diagnostic_unsupported" if held_out == 3 else "passed_declared_rivals")
    rotations.append({"held_out": held_out, "status": verdict["status"], "rivals": verdict["rivals"]})
explicit = catalog.generate(TASK, seed=0, sample_index=3, n_train=3, allow_unapproved=True, timeout=90)[0]
assert [pair["input"] for split in ("train", "test") for pair in explicit[split]] == audited
assert explicit["lesson_check"]["status"] == "diagnostic_unsupported"
try:
    catalog.generate(TASK, seed=0, sample_index=3, allow_unapproved=True, timeout=90)
except GenerationFailure as exc:
    assert "filled_source_bbox" in exc.run["stderr"] and "Automatic lesson unsupported" in exc.run["stderr"]
    automatic = {"rejected": True, "worker_exit_code": exc.run["exit_code"], "reason": "filled_source_bbox fits every demo but disagrees with query"}
else:
    raise AssertionError("automatic lesson ambiguity was accepted")
row = next(json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if json.loads(line).get("task_id") == TASK)
rule = row["program_solution"]
report = {"schema": "arc-bbox-lesson-repair-check-v1", "task_id": TASK,
          "generator_sha256": digest, "canonical_rule_sha256": hashlib.sha256(rule.encode()).hexdigest(),
          "executed_rule_hash": applied["executed_rule_hash"], "rule_text_sha256": applied["rule_text_sha256"],
          "racket_cases": rows, "audited_inputs": audited,
          "audit_fit_vector": [row["rival_fits"] for row in rows[:4]],
          "query_rotations": rotations, "explicit_diagnostic": explicit["lesson_check"],
          "automatic_generation": automatic, "elapsed_seconds": round(time.monotonic()-START, 3),
          "adversarial_surfaces": ["multicolor/sparse/boundary rival purity and selected Racket parity across all difficulty bands", "all four held-out rotations and explicit/automatic public generation policy"],
          "limits": ["Only the declared global filled-bbox rival is checked, not all possible shortcuts.", "Automatic ambiguous draws are rejected, not resampled or scheduled for guaranteed success.", "No reference rule or per-grid generation behavior changed."]}
assert not OUT.exists(), OUT
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"racket_cases": len(rows), "rotations": len(rotations), "audit_fit_vector": report["audit_fit_vector"], "automatic_rejected": True, "elapsed_seconds": report["elapsed_seconds"]}))
