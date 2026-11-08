#!/usr/bin/env python3
"""Verify source, selected authority, executable text, and all retained Racket rows.

This runs no Racket evaluations. The failed raw-prefix verifier is preserved as
verify_racket.before_normalization_fix.py with its failure in the diagnostic.
"""
import hashlib
import json
from pathlib import Path
import sys
import types

BASE = Path(__file__).resolve().parent
WORK = BASE.parents[1]
REPO = WORK / "repo"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def grid_sha(grid):
    return text_sha(json.dumps(grid, separators=(",", ":")))


def load_authority_helpers():
    # Use the repository's recorded runtime mapping, not guessed module aliases.
    rows = json.loads((REPO / "catalog/runtime_files.json").read_text())
    mapping = {row["target"]: row["path"] for row in rows}
    names = ("canonical_profile_gate", "comment_solutions", "coder_synth_verify")
    paths = [REPO / mapping[f"scripts/{name}.py"] for name in names]
    assert len({path.parent for path in paths}) == 1
    package = types.ModuleType("scripts")
    package.__path__ = [str(paths[0].parent)]
    assert "scripts" not in sys.modules
    sys.modules["scripts"] = package
    sys.path.insert(0, str(REPO / "shared/runtime"))
    from scripts.canonical_profile_gate import canonical_rule_source, normalized_rule_hash
    from puzzle_generators.rule_wrap import wrap_rule
    from reviewer_support import load_selected_generator
    return canonical_rule_source, normalized_rule_hash, wrap_rule, load_selected_generator


def main():
    diagnostic_path = BASE / "authority_verification_diagnostic.json"
    diagnostic = json.loads(diagnostic_path.read_text())
    assert diagnostic["status"] == "verifier_predicate_error_no_authority_drift"
    for relative, pin in diagnostic["original_source_pins"].items():
        assert sha(REPO / relative) == pin["sha256"], relative
    assert sha(BASE / "AUDIT_DRAFT.md") == diagnostic["preconfirmation_draft"]["sha256"]
    canonical_rule_source, normalized_rule_hash, wrap_rule, load_selected_generator = load_authority_helpers()
    pending = []
    for gid in ("ebd08d719ed6", "05b5a82ace36"):
        home = BASE / gid
        path = home / "racket.json"
        if not path.is_file():
            pending.append(gid)
            continue
        record = json.loads(path.read_text())
        report = json.loads((home / "report.json").read_text())
        inputs = json.loads((home / "inputs.json").read_text())["inputs"]
        expected = json.loads((home / "python_reference_outputs.json").read_text())["outputs"]
        rivals = json.loads((home / "rival_outputs.json").read_text())["outputs"]
        module, source_path, source_sha = load_selected_generator(gid, root=REPO)
        assert source_path == REPO / report["generator_source"]
        assert source_sha == record["generator_sha256"] == report["generator_sha256"]
        assert record["task_id"] == gid and record["reference"] == "canonical"
        rule_task_id = getattr(module, "RULE_TASK_ID", gid).strip()
        assert record["rule_task_id"] == rule_task_id == gid
        assert record["rule_file"] == "data/canonical/puzzles.jsonl"
        source = canonical_rule_source(rule_task_id)
        original_row = diagnostic["canonical_rows"][gid][0]
        raw_sha = text_sha(source)
        assert raw_sha == report["canonical_rule_text_sha256"] == original_row["program_raw_sha256"]
        normalized_sha = text_sha(" ".join(source.split()))
        assert normalized_sha == original_row["program_normalized_sha256"]
        rule_hash = normalized_rule_hash(source)
        assert rule_hash == normalized_sha[:12]
        assert record["rule_hash_matches_catalog"] is True
        assert record["executed_rule_hash"] == record["catalog_rule_hash"] == rule_hash
        wrapped_sha = text_sha(wrap_rule(source))
        assert record["rule_text_sha256"] == wrapped_sha
        rows = record["results"]
        assert len(rows) == len(inputs) == len(expected) == len(rivals)
        assert [row["index"] for row in rows] == list(range(len(inputs)))
        assert len({grid_sha(grid) for grid in inputs}) == len(inputs)
        for i, row in enumerate(rows):
            assert row["input"] == inputs[i]
            assert row["input_sha256"] == grid_sha(inputs[i])
            assert row["valid_output"] is True and row["error"] is None
            assert row["output"] == expected[i], (gid, i, "Racket and Python reference differ")
            assert row["output_sha256"] == grid_sha(row["output"])
            assert row["generator_domain"] == {"status": "valid", "errors": []}
            assert module.self_check(inputs[i]) == []
        agree = [row["output"] == rivals[i] for i, row in enumerate(rows)]
        demos = report["episode"]["demonstrations"]
        assert all(agree[:demos]) and not all(agree[demos:])
        assert agree == report["episode"]["rival_equals_python_reference_by_source_index"]
        diff_cells = []
        for row, rival in zip(rows, rivals, strict=True):
            output = row["output"]
            assert len(output) == len(rival) and all(len(a) == len(b) for a, b in zip(output, rival, strict=True))
            diff_cells.append(sum(a != b for ra, rb in zip(output, rival, strict=True) for a, b in zip(ra, rb, strict=True)))
        verification = {
            "schema": "arcpuzzles-audit-racket-comparison-v2", "task_id": gid,
            "status": "confirmed", "generator_sha256": source_sha,
            "authority": {
                "rule_task_id": rule_task_id, "canonical_source_raw_sha256": raw_sha,
                "canonical_source_normalized_sha256": normalized_sha,
                "executed_rule_hash": rule_hash, "executable_wrapper_sha256": wrapped_sha,
                "original_zip_row_sha256": original_row["row_sha256"],
                "diagnostic_sha256": sha(diagnostic_path),
                "raw_source_normalized_id_and_full_executable_hash_all_verified": True,
            },
            "racket_receipt_sha256": sha(path), "input_list_sha256": sha(home / "inputs.json"),
            "preconfirmation_report_sha256": sha(home / "report.json"),
            "inputs_checked": len(rows), "demonstrations": demos, "queries": len(rows) - demos,
            "all_inputs_distinct_and_generator_domain_valid": True,
            "all_grid_digests_verified": True,
            "all_racket_outputs_match_python_reference": True,
            "rival_equals_racket_by_source_index": agree,
            "rival_different_cells_by_source_index": diff_cells,
            "query_source_indices_with_disagreement": [i for i in range(demos, len(rows)) if not agree[i]],
            "scope": "Exact retained episodes only; not default CLI assembly, corpus prevalence, or approval.",
        }
        (home / "verification.json").write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n")
        print(json.dumps(verification, sort_keys=True))
    if pending:
        print(json.dumps({"status": "pending", "missing_racket_receipts": pending}))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
