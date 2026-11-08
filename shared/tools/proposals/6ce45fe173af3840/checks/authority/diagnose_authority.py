"""Read-only, source-bound diagnosis of task 44e865b6a43e authority formatting.

Run from the outer packet root:
  python3 review.py run ../.venv/bin/python -B ../checks/authority/diagnose_authority.py

Writes only new evidence beside this script. Never applies a patch.
"""
from __future__ import annotations

import copy
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from arcpuzzles.authority_sync import _replace_target, _tokens, propose_selected_sync
from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_return import _allowed, _diff, _patch_paths


TASK = "44e865b6a43e"
OUT = Path(__file__).resolve().parent
WORK = OUT.parent.parent
REPO = WORK / "repo"
PACKET = WORK.parent
BASE = "shared/data/base/solutions/training/2601afb7__44e865b6a43e.json"
CANONICAL = "shared/data/canonical/puzzles.jsonl"


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def write_new(name, content):
    with (OUT / name).open("x", encoding="utf-8") as stream:
        stream.write(content)


def stats(source):
    return {
        "bytes_utf8": len(source.encode("utf-8")),
        "characters": len(source),
        "line_count": len(source.splitlines()),
        "whitespace_counts": dict(sorted(Counter(c for c in source if c.isspace()).items())),
        "non_whitespace_characters": sum(not c.isspace() for c in source),
        "exact_sha256": sha(source.encode("utf-8")),
        "whitespace_normalized_sha256": sha(" ".join(source.split()).encode("utf-8")),
        "restricted_reader_token_count": len(_tokens(source)),
    }


def source_ref(relative, start, end):
    path = PACKET / relative
    lines = path.read_text().splitlines()
    return {
        "path": relative,
        "sha256": sha(path.read_bytes()),
        "start_line": start,
        "end_line": end,
        "excerpt": "\n".join(lines[start - 1:end]),
    }


def main():
    protected_names = [
        BASE, CANONICAL, "catalog/authority_files.json",
        "src/arcpuzzles/authority_sync.py", "src/arcpuzzles/review_full_return.py",
    ]
    before = {name: sha((REPO / name).read_bytes()) for name in protected_names}
    contract_blob = (WORK / "ASSIGNMENT.json").read_bytes()
    contract = json.loads(contract_blob)
    proposal_blob = (OUT / "selected-authority-proposal.json").read_bytes()
    proposal = json.loads(proposal_blob)
    assert proposal == propose_selected_sync(Catalog(REPO), TASK)
    assert proposal["status"] == "proposal" and proposal["applied"] is False
    assert len(proposal["files"]) == 1
    item = proposal["files"][0]
    assert item["path"] == BASE
    assert item["changed_json_pointers"] == ["/racket_target/target_code"]

    original = (REPO / BASE).read_bytes()
    row = json.loads(original)
    selected = row["racket_target"]["target_code"]
    canonical_rows = [
        (index, json.loads(line))
        for index, line in enumerate((REPO / CANONICAL).read_text().splitlines(), 1)
        if line.strip() and json.loads(line).get("task_id") == TASK
    ]
    assert len({r["program_solution"] for _, r in canonical_rows}) == 1
    canonical = canonical_rows[0][1]["program_solution"]
    assert selected != canonical
    assert " ".join(selected.split()) == " ".join(canonical.split())
    assert _tokens(selected) == _tokens(canonical)

    proposed_bytes = _replace_target(original.decode("utf-8"), selected, canonical).encode("utf-8")
    expected = copy.deepcopy(row)
    expected["racket_target"]["target_code"] = canonical
    assert json.loads(proposed_bytes) == expected
    assert expected["racket_target"]["raw_code"] == row["racket_target"]["raw_code"]
    assert sha(original) == item["old_sha256"]
    assert sha(proposed_bytes) == item["new_sha256"]
    assert sha(original) == contract["baseline_sha256"]["repo/" + BASE]
    assert before[CANONICAL] == contract["baseline_sha256"]["repo/" + CANONICAL]

    repository_patch = proposal["patch"]
    return_patch = _diff("repo/" + BASE, original, proposed_bytes)
    write_new("selected-authority.patch", repository_patch)
    write_new("return-scope.patch", return_patch)
    write_new("source-formatting.diff", "".join(difflib.unified_diff(
        selected.splitlines(keepends=True), canonical.splitlines(keepends=True),
        fromfile="selected_target_code", tofile="canonical_program_solution")))

    assert _patch_paths(return_patch, contract) == ["repo/" + BASE]
    allow_checks = {
        "repo/" + BASE: True,
        "repo/" + CANONICAL: True,
        "repo/shared/data/base/solutions/training/unlisted.json": False,
        "repo/catalog/authority_files.json": False,
        "repo/shared/tools/check_task_authority_sync.py": False,
        "repo/src/arcpuzzles/authority_sync.py": False,
    }
    for name, expected_allowed in allow_checks.items():
        assert _allowed(name, contract) is expected_allowed

    patch_checks = []
    for cwd, patch_name in ((REPO, "selected-authority.patch"), (WORK, "return-scope.patch")):
        argv = ["git", "apply", "--check", "--no-index", str(OUT / patch_name)]
        run = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
        patch_checks.append({"cwd": str(cwd), "argv": argv, "exit_code": run.returncode,
                             "stdout": run.stdout, "stderr": run.stderr})
        assert run.returncode == 0, run.stderr

    after = {name: sha((REPO / name).read_bytes()) for name in protected_names}
    assert after == before
    assert (WORK / "ASSIGNMENT.json").read_bytes() == contract_blob
    existing_baseline = json.loads((WORK / "checks/before/checks" / (TASK + "_before_authority_sync.json")).read_text())
    audit = existing_baseline["audits"][0]
    report = {
        "schema": "reviewer-authority-formatting-diagnostic-v1",
        "task_id": TASK,
        "status": "PASS_non_applying_proposal_and_scope_checks",
        "applied": False,
        "proposal_path": "checks/authority/selected-authority-proposal.json",
        "proposal_sha256": sha(proposal_blob),
        "diagnostic_script_sha256": sha(Path(__file__).read_bytes()),
        "assignment_sha256": sha(contract_blob),
        "protected_source_sha256_before": before,
        "protected_source_sha256_after": after,
        "protected_sources_unchanged": True,
        "selected_source": stats(selected),
        "canonical_source": stats(canonical),
        "canonical_lines": [index for index, _ in canonical_rows],
        "canonical_rule_hash": proposal["canonical_rule_hash"],
        "exact_difference": {
            "kind": "Whitespace-only presentation change; same normalized text and restricted reader tokens.",
            "utf8_byte_delta": len(canonical.encode()) - len(selected.encode()),
            "selected_is_one_line": len(selected.splitlines()) == 1,
            "non_whitespace_text_equal": "".join(selected.split()) == "".join(canonical.split()),
            "restricted_reader_tokens_equal": True,
            "only_json_pointer_changed": "/racket_target/target_code",
            "archival_raw_code_unchanged": True,
            "canonical_file_unchanged": True,
        },
        "proposed_files": proposal["files"],
        "scope": {
            "selected_base_in_assignment_baseline": True,
            "allowlist_results": allow_checks,
            "return_patch_paths": _patch_paths(return_patch, contract),
            "scope_conclusion": "Selected baseline base-authority alignment is expressly permitted by the active return builder. Canonical edits are restricted to the selected rule task; no canonical edit is proposed. Other shared tooling/catalog paths remain forbidden.",
            "source_evidence": [
                source_ref("START-HERE.md", 68, 73),
                source_ref("WORK/package_return.py", 7, 9),
                source_ref("WORK/repo/src/arcpuzzles/review_full_return.py", 27, 49),
                source_ref("WORK/repo/src/arcpuzzles/review_full_return.py", 364, 406),
                source_ref("WORK/repo/src/arcpuzzles/authority_sync.py", 88, 159),
            ],
        },
        "patch_dry_run_checks": patch_checks,
        "existing_execution_parity": {
            "source": "checks/before/checks/44e865b6a43e_before_authority_sync.json",
            "sha256": sha((WORK / "checks/before/checks" / (TASK + "_before_authority_sync.json")).read_bytes()),
            "result": audit["execution_parity"],
            "qualification": "Retained baseline evidence; not a new execution test by this diagnostic.",
        },
        "remaining_verification": "No live authority_sync or rule_smoke rerun after applying because no application was made. Parent may apply the reviewed field-only patch, then run both stages in fresh evidence directories.",
    }
    write_new("diagnostic.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"], "applied": False,
        "selected_source": report["selected_source"],
        "canonical_source": report["canonical_source"],
        "source_files_unchanged": True,
        "proposed_files": report["proposed_files"],
        "patch_check_exit_codes": [r["exit_code"] for r in patch_checks],
        "allowlist_results": allow_checks,
    }, indent=2))


if __name__ == "__main__":
    main()
