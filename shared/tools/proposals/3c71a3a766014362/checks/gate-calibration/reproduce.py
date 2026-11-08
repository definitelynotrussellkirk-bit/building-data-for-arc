#!/usr/bin/env python3
"""Source-bound evidence for generic rotation self-check mutation false positives."""
from pathlib import Path
from copy import deepcopy
import hashlib
import importlib.util
import json
import shutil
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
sys.path.insert(0, str(WORK / "repo/shared/runtime"))
from reviewer_support import canonical_pairs, find_root, load_selected_generator, normalize_grid
from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
ROOT = find_root(__file__)
TASK = "864eaaac6503"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage_detector(folder):
    """Retain full exact module and all nonstdlib dependencies used by these probes."""
    scripts = folder / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    (scripts / "__init__.py").write_text("")
    bindings = []
    for name in ("generator_defect_lint.py", "generator_module_loader.py"):
        source = ROOT / "shared/tools" / name
        target = scripts / name
        shutil.copyfile(source, target)
        assert digest(target) == digest(source)
        bindings.append({"source": str(source.relative_to(ROOT)),
                         "retained_copy": str(target.relative_to(HERE)), "sha256": digest(source)})
    return scripts / "generator_defect_lint.py", bindings


def load_detector(path, name="calibration_original_detector"):
    sys.path.insert(0, str(path.parents[1]))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    detector_path, bindings = stage_detector(HERE / "original")
    detector = load_detector(detector_path)
    generator, generator_path, generator_hash = load_selected_generator(TASK, root=ROOT)
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    train = [(p["input"], p["output"]) for p in pairs if p["split"] == "train"]
    witnesses = {
        "singleton": [[9, 9, 9], [9, 0, 9], [9, 9, 9]],
        "solid_2x2": [[0, 0, 9], [0, 0, 9], [9, 9, 9]],
        "short_line": [[9, 9, 9], [0, 0, 0], [9, 9, 9]],
    }
    authority = []
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            authority.append(row)
    programs = {row["program_solution"] for row in authority}
    assert programs == {"(rule! rotate-ccw)"}
    program = programs.pop()
    wrapper = "(define (rule! f) f)"
    installation = f"(define calibration-rule {program})"
    records = []
    with RacketBridge() as bridge:
        bridge.eval_text(wrapper)
        bridge.eval_text(installation)
        for index, entry in enumerate(pairs + [{"input": grid, "witness": kind} for kind, grid in witnesses.items()]):
            grid = deepcopy(entry["input"])
            bridge.define_grid("calibration-input", grid)
            actual = normalize_grid(bridge.eval_text("(calibration-rule calibration-input)"))
            errors = generator.self_check(deepcopy(grid))
            record = {**entry, "actual_racket_output": actual, "self_check_errors": errors,
                      "self_check_accepted": not errors,
                      "canonical_label_matches": actual == entry["output"] if "output" in entry else None}
            if "witness" in entry:
                record["standalone_minimal_probe_findings"] = detector.probe_selfcheck_minimal_impostors(generator, [grid], [None], train)
            records.append(record)
    assert len(pairs) == 5
    assert all(r["canonical_label_matches"] for r in records[:5])
    assert all(r["self_check_accepted"] for r in records)
    first = pairs[0]["input"]
    constructed = dict(detector._minimal_impostors(first))
    first_findings = detector.probe_selfcheck_minimal_impostors(generator, [first], [None], train)
    assert constructed["solid_2x2"] == first
    assert any("solid_2x2" in finding for finding in first_findings)
    canonical_inputs = [p["input"] for p in pairs]
    bridge_source = Path(sys.modules["arc_repl.racket_bridge"].__file__).resolve()
    report = {
        "schema": "rotation-selfcheck-gate-calibration-v1",
        "task": TASK,
        "status": "reproduced semantic false positives; no shared patch applied",
        "generator_source": str(generator_path.relative_to(ROOT)), "generator_sha256": generator_hash,
        "detector_dependency_closure": bindings,
        "dependency_closure_note": "The imported full detector and its full generator_module_loader dependency use stdlib in the two exercised probe paths; no dependency is stubbed. Other detector lazy imports are not called.",
        "rule_text": program,
        "rule_text_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "catalog_rule_hash": hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12],
        "rule_wrapper": wrapper, "installation": installation,
        "bridge_sha256": digest(bridge_source),
        "prelude_sha256": digest(bridge_source.parent / "racket_prelude/arc-prelude.rkt"),
        "runtime": racket_runtime_status(),
        "reproducer_sha256": digest(Path(__file__)),
        "canonical_pairs": len(pairs), "additional_witnesses": len(witnesses),
        "reference_outputs_match_all_canonical_labels": True,
        "records": records,
        "first_canonical_input": {
            "input": first, "modal_background": detector._majority(first),
            "exactly_equals_named_solid_2x2_mutation": constructed["solid_2x2"] == first,
            "canonical_minimal_kinds_before": sorted(detector._canonical_minimal_kinds(train)),
            "detector_findings": first_findings,
            "false_positive": True,
            "reason": "The detector calls the literal canonical input's accepted top-left minority 2x2 block an impostor; canonical Racket execution matches its recorded output."
        },
        "canonical_inputs_minimal_probe_findings": detector.probe_selfcheck_minimal_impostors(generator, canonical_inputs, [None] * 5, train),
        "canonical_inputs_power_probe_findings": detector.probe_selfcheck_power(generator, canonical_inputs, [None] * 5),
        "limits": [
            "Racket execution establishes reference transformation and label agreement; task-domain lawfulness also follows the generic rectangular rotation contract, not mere executable totality.",
            "This is an isolated exact-source function reproduction, not a new full defect lint or battery result.",
            "Both generic mutation warnings remain native shared-tool behavior until any proposal is separately accepted.",
            "No post-repair solve directory or private solve answers are accessed."
        ]
    }
    (HERE / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"canonical_pairs": 5, "racket_label_matches": 5, "lawful_witnesses": 3,
                      "first_canonical_block_false_positive": True,
                      "minimal_warnings": report["canonical_inputs_minimal_probe_findings"],
                      "power_warnings": report["canonical_inputs_power_probe_findings"]}, sort_keys=True))


if __name__ == "__main__":
    main()
