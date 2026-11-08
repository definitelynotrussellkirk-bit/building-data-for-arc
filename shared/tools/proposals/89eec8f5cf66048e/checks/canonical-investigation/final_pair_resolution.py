#!/usr/bin/env python3
"""Select final-support witnesses, then distill fresh public Racket receipts."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import load_selected_generator


TASK = "fc814cec3976"
FINAL_SHA = "416d21b39294a0c88facbf8a094b492fe5a2fc67ed24330852d0faa776b10189"
INTERMEDIATE_REVIEW_SHA = "8d140768e6e511b55a4187a8f71e39d63701ac3b23f5314cdb0270a5e6dfaa9b"
ROOT = Path.cwd().resolve()
WORK = ROOT.parent
OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_sha(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def centers(output):
    return [[r, c] for r, row in enumerate(output) for c, value in enumerate(row) if value == 4]


def write_new(path, value, *, compact=False):
    if path.exists():
        raise FileExistsError(f"Refusing to replace retained evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, sort_keys=True, separators=(",", ":")) if compact else json.dumps(value, indent=2, sort_keys=True)
    path.write_text(text + "\n")


def wrapper_argv(*payload):
    return ["WORK/.venv/bin/python", "review.py", "run", "../.venv/bin/python", *payload]


def prepare(gen, digest):
    choices = {}
    for code in range(840):
        template = gen._template_for_code(code)
        if (template["profile_index"], template["transform_index"]) != (1, 2):
            continue
        kind = "altered" if code % 5 in (1, 3) else "ordinary"
        if kind in choices:
            continue
        grid = gen.generate(0, 0, scene_code=code)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {"scene_code": code}
        choices[kind] = {"scene_code": code, "input": grid, "selection_centers": centers(gen._analysis(grid)["output"])}
        if len(choices) == 2:
            break
    assert set(choices) == {"ordinary", "altered"}
    ordinary, altered = [choices[kind] for kind in ("ordinary", "altered")]
    assert gen._red_key(ordinary["input"]) == gen._red_key(altered["input"])
    assert ordinary["selection_centers"] != altered["selection_centers"]
    write_new(OUT / "final-pair-input.json", {"inputs": [ordinary["input"], altered["input"]]}, compact=True)
    write_new(OUT / "final-pair-selection.json", {
        "task_id": TASK, "generator_sha256": digest,
        "search_bound_exclusive": 840, "last_considered_code": code,
        "profile": "public_2", "profile_index": 1, "transform_index": 2,
        "pair_order": ["ordinary", "altered"],
        "choices": {kind: {key: value for key, value in choice.items() if key != "input"} for kind, choice in choices.items()},
        "scope": "The Python mirror selected inputs with differing centers only. Final labels must come from a separate canonical Racket apply receipt."
    })
    print(json.dumps({"generator_sha256": digest, "replay_codes": {kind: choice["scene_code"] for kind, choice in choices.items()}}), flush=True)


def distill(gen, source, digest):
    selection = json.loads((OUT / "final-pair-selection.json").read_text())
    raw_path = OUT / "final-pair-racket.json"
    raw = json.loads(raw_path.read_text())
    assert selection["generator_sha256"] == raw["generator_sha256"] == digest
    assert raw["reference"] == "canonical" and raw["rule_hash_matches_catalog"]
    assert raw["task_id"] == TASK and raw["executed_rule_hash"] == gen.RULE_HASH
    assert len(raw["results"]) == 2
    original, altered = raw["results"]
    codes = {kind: selection["choices"][kind]["scene_code"] for kind in ("ordinary", "altered")}
    assert codes == {"ordinary": 7, "altered": 31}
    for kind, result in (("ordinary", original), ("altered", altered)):
        assert result["error"] is None and result["valid_output"]
        assert result["generator_domain"] == {"status": "valid", "errors": []}
        assert result["input"] == gen.generate(0, 0, scene_code=codes[kind])
        assert grid_sha(result["input"]) == result["input_sha256"]
        assert grid_sha(result["output"]) == result["output_sha256"]
        assert gen.self_check(result["input"]) == []
        assert gen.observe_overrides(result["input"]) == {"scene_code": codes[kind]}
    assert gen._red_key(original["input"]) == gen._red_key(altered["input"])
    assert centers(original["output"]) != centers(altered["output"])
    protected = gen._TEMPLATES[(1, 2)]["protected"]
    changes = [[r, c, original["input"][r][c], altered["input"][r][c]] for r in range(19) for c in range(19) if original["input"][r][c] != altered["input"][r][c]]
    relevant = [change for change in changes if tuple(change[:2]) in protected]
    assert relevant == [[3, 10, 0, 5]]
    assert gen._STRUCTURAL_EDITS[(1, 2)] == ((3, 10, 5),)
    rival = deepcopy(altered["input"])
    for r in range(19):
        for c in range(19):
            if original["output"][r][c] != original["input"][r][c]:
                rival[r][c] = original["output"][r][c]
    assert rival == gen.red_layout_lookup(altered["input"])
    disagreements = [[r, c, altered["output"][r][c], rival[r][c]] for r in range(19) for c in range(19) if altered["output"][r][c] != rival[r][c]]
    assert len(disagreements) == 12

    prior_binding = json.loads((OUT / "structural-racket-verification.json").read_text())
    assert sha(OUT / "structural-racket-raw-receipt.json") == prior_binding["raw_receipt_sha256"]
    intermediate = WORK / "checks/code-review.json"
    assert sha(intermediate) == INTERMEDIATE_REVIEW_SHA
    previous = json.loads((OUT / "malformed-validator-review.json").read_text())
    cropped = previous["input"]
    replay = gen.generate(0, 0, scene_code=5)
    assert cropped == [row[:16] for row in replay[:16]]
    assert gen._red_key(cropped) == gen._red_key(replay)
    errors = gen.self_check(cropped)
    strict = gen.strict_canonical_like(cropped)
    observed = gen.observe_overrides(cropped)
    analysis = gen._analysis(cropped)
    assert errors and any("19x19" in error for error in errors)
    assert strict == errors and observed == {}
    assert analysis == {"errors": errors, "scene_code": None, "facts": {}, "output": None}
    test_log = OUT / "final-shape-regression.log"
    assert "1 passed" in test_log.read_text()
    source_text = source.read_text()
    assert 'errors.append("calibrated dense-noise scenes must be exactly 19x19")\n        return {"errors": errors, "scene_code": None, "facts": {}, "output": None}' in source_text
    assert sha(source) == digest

    apply_command = {
        "cwd": str(WORK.parent),
        "argv": wrapper_argv("-m", "arcpuzzles", "apply", TASK, "--input", "../checks/canonical-investigation/final-pair-input.json", "--check-generator-domain", "--out", "../checks/canonical-investigation/final-pair-racket.json"),
        "payload_cwd": str(ROOT), "exit_code": 0,
        "input_path": "checks/canonical-investigation/final-pair-input.json", "input_sha256": sha(OUT / "final-pair-input.json"),
        "receipt_path": "checks/canonical-investigation/final-pair-racket.json", "receipt_sha256": sha(raw_path),
        "log_path": "checks/canonical-investigation/final-pair-apply.log", "log_sha256": sha(OUT / "final-pair-apply.log"),
    }
    counter_path = ROOT / "generators" / TASK / "counterexamples/structural-contrast.json"
    counter = {
        "schema": "fc814cec3976-structural-contrast-v2", "task_id": TASK,
        "finding": "Two final generated inputs have identical red coordinates and different canonical Racket recolor masks. A single fixed recolor mask per red-coordinate key fails.",
        "coordinate_convention": "zero-based [row, column]",
        "source_binding": {key: raw[key] for key in ("generator_sha256", "executed_rule_hash", "rule_text_sha256", "rule_file", "reference", "rule_hash_matches_catalog")},
        "historical_distinction": {
            "baseline_generator_sha256": prior_binding["analytical_baseline_sha256"],
            "prior_48_input_receipt_sha256": prior_binding["raw_receipt_sha256"],
            "scope": "Earlier original-template/hand-mutated Racket pairs motivated this edit. The inputs and labels below are fresh final-source generated-support evidence from a separate Racket execution; they are not copied from the baseline receipt."
        },
        "replay": {"seed": 0, "sample_index": 0, "ordinary_scene_code": codes["ordinary"], "altered_scene_code": codes["altered"], "profile": "public_2", "transform_index": 2},
        "ordinary": {**{key: original[key] for key in ("input", "output", "input_sha256", "output_sha256", "generator_domain")}, "centers": centers(original["output"])},
        "altered": {**{key: altered[key] for key in ("input", "output", "input_sha256", "output_sha256", "generator_domain")}, "centers": centers(altered["output"])},
        "same_red_key": True,
        "candidate_relevant_changes": relevant,
        "safe_texture_difference_count": len(changes) - len(relevant),
        "lookup_counterexample": {
            "construction": "Copy the altered input, then overwrite exactly those cells changed in the ordinary Racket input/output pair with their ordinary output colors. This equals final red_layout_lookup on the altered input.",
            "output_sha256": grid_sha(rival),
            "mismatch_count": len(disagreements),
            "differing_cells_row_col_authoritative_lookup": disagreements,
        },
        "public_apply": apply_command,
        "remaining_limit": "The contrast refutes red coordinates alone as a fixed-mask key. The generator still has 53 candidate contexts and recoverable scene-code bits; broader context or code lookup remains possible."
    }
    malformed_path = ROOT / "generators" / TASK / "counterexamples/malformed-known-red-key.json"
    malformed = {
        "schema": "fc814cec3976-malformed-known-red-key-v1", "task_id": TASK,
        "input": cropped, "shape": [16, 16], "input_sha256": grid_sha(cropped),
        "replay": "Crop gen.generate(0, 0, scene_code=5) to [row[:16] for row in grid[:16]]. Its red key remains unchanged.",
        "before_generator_sha256": previous["generator_sha256"], "final_generator_sha256": digest, "declared_rule_hash": gen.RULE_HASH,
        "before": [{key: result[key] for key in ("hook", "status", "exception_type", "error")} for result in previous["results"]],
        "after": {"self_check": errors, "strict_canonical_like": strict, "observe_overrides": observed, "analysis_output": analysis["output"]},
        "resolution": "Wrong-shape analysis returns rejection reasons before indexing any template scene-code bit position.",
        "scope": "Validator rejection regression outside generated support; no Racket label or valid generated-scene admission is claimed."
    }
    targets = [counter_path, malformed_path, OUT / "final-pair-command.json", WORK / "checks/code-review-resolution.json"]
    assert not any(path.exists() for path in targets), targets
    write_new(counter_path, counter, compact=True)
    write_new(malformed_path, malformed, compact=True)
    write_new(OUT / "final-pair-command.json", apply_command)
    resolution = {
        "schema": "fc814cec3976-code-review-resolution-v1", "task_id": TASK,
        "status": "resolved", "finding_id": "known_red_key_wrong_shape",
        "intermediate_review": {"path": "checks/code-review.json", "sha256": INTERMEDIATE_REVIEW_SHA, "generator_sha256": previous["generator_sha256"], "unchanged": True},
        "final_generator": {"path": "repo/generators/fc814cec3976/generator.py", "version": gen.VERSION, "sha256": digest},
        "reviewed_change": "_analysis immediately returns errors, scene_code=None, facts={}, output=None after rejecting a non-19x19 shape; template-bit positions are not accessed on this path.",
        "probe": {"input_sha256": grid_sha(cropped), "same_known_red_key": True, "self_check": errors, "strict_canonical_like": strict, "observe_overrides": observed},
        "commands": [
            {"cwd": str(WORK.parent), "argv": wrapper_argv("-m", "pytest", "-q", "generators/fc814cec3976/tests/test_structural_support.py::test_known_red_layout_on_wrong_shape_is_rejected_without_indexing_error"), "exit_code": 0, "result": "1 passed", "log_path": "checks/canonical-investigation/final-shape-regression.log", "log_sha256": sha(test_log)},
            {"cwd": str(WORK.parent), "argv": wrapper_argv("../checks/canonical-investigation/final_pair_resolution.py", "prepare"), "exit_code": 0, "log_path": "checks/canonical-investigation/final-pair-prepare.log", "log_sha256": sha(OUT / "final-pair-prepare.log")},
            apply_command,
            {"cwd": str(WORK.parent), "argv": wrapper_argv("../checks/canonical-investigation/final_pair_resolution.py", "distill"), "payload_cwd": str(ROOT), "result": "Artifact emission follows successful exact-source, preserved-evidence, direct malformed-grid, generated-domain, and Racket-pair assertions.", "log_path": "checks/canonical-investigation/final-pair-distill.log"},
        ],
        "counterexamples": [{"path": str(path.relative_to(WORK)), "sha256": sha(path)} for path in (counter_path, malformed_path)],
        "racket_contrast": {"input_count": 2, "scene_codes": codes, "generator_sha256": digest, "executed_rule_hash": raw["executed_rule_hash"], "same_red_key": True, "lookup_mismatch_count": len(disagreements), "receipt_sha256": sha(raw_path)},
        "preserved_prior_raw_receipt": {"sha256": prior_binding["raw_receipt_sha256"], "unchanged": True},
        "non_payload_tool_failure": "A draft-script rewrite using Delete File plus Add File for the same path in one apply_patch was rejected before changes. The unused draft remains; this new script supplied the executed payload.",
        "remaining_limits": "Finite candidate-context bank, recoverable scene-code bits, and the explicitly named-rival scope remain as documented in the intermediate review.",
        "completed_utc": datetime.now(timezone.utc).isoformat(),
    }
    write_new(WORK / "checks/code-review-resolution.json", resolution)
    print(json.dumps({"status": "resolved", "generator_sha256": digest, "scene_codes": codes, "racket_lookup_mismatches": len(disagreements), "counterexamples": [str(path.relative_to(WORK)) for path in (counter_path, malformed_path)], "intermediate_review_unchanged": True, "prior_48_input_receipt_unchanged": True}), flush=True)


def main():
    gen, source, digest = load_selected_generator(TASK, root=ROOT)
    assert digest == FINAL_SHA, digest
    assert len(sys.argv) == 2 and sys.argv[1] in ("prepare", "distill")
    if sys.argv[1] == "prepare":
        prepare(gen, digest)
    else:
        distill(gen, source, digest)


if __name__ == "__main__":
    main()
