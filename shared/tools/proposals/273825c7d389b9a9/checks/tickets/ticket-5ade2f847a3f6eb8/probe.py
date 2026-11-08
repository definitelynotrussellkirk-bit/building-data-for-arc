#!/usr/bin/env python3
"""Bounded replay of the retained ec1260207f71 audit witness."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TASK_ID = "ec1260207f71"
RETURN_ID = "review-722db3e7875e275c:v0001"
EXPECTED = {
    "source": "e3871fe1e3186a4ae8d9a90557b1fe237497475b5a026de0d9d039bd095ab48e",
    "assets_manifest": "e61add661cc8066d5717de5d369eb9bef6b7c828c381fe616e2a353ba5f80fcd",
    "audit_index": "ecc2b237aa0901452699a8aa5c28907ed650c023ec96526bafdb9a597cbb7713",
    "audit_record": "f37537e7a50cf7ebe9889ddc096c94e26c06458b236306e529226d7e395ded56",
    "rule_hash": "8b7e24f62fab",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def datum(grid: list[list[int]]) -> str:
    return "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def evaluate(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    body = strip_rule_wrapper(program)
    if not body.startswith("(lambda (g)"):
        raise AssertionError("canonical program is not the expected lambda")
    return normalize_grid(bridge.eval_text(f"({body} '{datum(normalize_grid(grid))})"))


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    repo = find_root(__file__)
    work = repo.parent
    source_rel = Path("repo/generators/ec1260207f71/generator.py")
    assets_rel = Path(
        "repo/generators/ec1260207f71/counterexamples/"
        "review-722db3e7875e275c-v0001/audit_assets.json"
    )
    index_rel = Path("repo/generators/ec1260207f71/evidence/review_index.json")
    retained_rel = Path(
        "repo/generators/ec1260207f71/counterexamples/"
        "review-722db3e7875e275c-v0001/retained/checks/audit/ec1260207f71"
    )

    hashes = {
        "source": sha256_bytes((work / source_rel).read_bytes()),
        "assets_manifest": sha256_bytes((work / assets_rel).read_bytes()),
        "audit_index": sha256_bytes((work / index_rel).read_bytes()),
    }
    assert hashes == {key: EXPECTED[key] for key in hashes}, hashes

    audit_index = json.loads((work / index_rel).read_text(encoding="utf-8"))
    rows = [row for row in audit_index["audits"] if row.get("return_id") == RETURN_ID]
    assert len(rows) == 1
    audit_record_hash = sha256_bytes(canonical_bytes(rows[0]))
    assert audit_record_hash == EXPECTED["audit_record"], audit_record_hash

    assets = json.loads((work / assets_rel).read_text(encoding="utf-8"))
    assert assets["return_id"] == RETURN_ID
    assert assets["audited_generator_sha256"] == EXPECTED["source"]
    retained_hashes = {}
    for row in assets["files"]:
        path = repo / row["path"]
        actual = sha256_bytes(path.read_bytes())
        assert actual == row["sha256"], (row["path"], actual, row["sha256"])
        retained_hashes[row["path"]] = actual

    module, source_path, selected_hash = load_selected_generator(TASK_ID, root=repo)
    assert selected_hash == EXPECTED["source"]
    assert module.RULE_HASH == EXPECTED["rule_hash"]
    assert source_path == (work / source_rel).resolve()

    seed = 2
    first_index = 33
    difficulty = "easy"
    grids = [module.generate(seed, first_index + offset, difficulty=difficulty) for offset in range(5)]
    retained_dir = work / retained_rel
    retained_inputs = json.loads((retained_dir / "input.json").read_text(encoding="utf-8"))
    assert grids == retained_inputs
    validator_errors = [module.self_check(grid) for grid in grids]
    assert validator_errors == [[] for _ in grids]
    observed = [module.observe_overrides(grid) for grid in grids]
    dot_bands = [row["dot_band"] for row in observed]
    assert dot_bands == ["upper", "upper", "upper", "upper", "lower"]

    programs = []
    with canonical_path(repo).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.append(row.get("program_solution"))
    assert programs and len(set(programs)) == 1
    program = programs[0]

    retained_racket = json.loads((retained_dir / "racket.json").read_text(encoding="utf-8"))
    retained_outputs = [row["output"] for row in retained_racket["results"]]
    assert retained_racket["executed_rule_hash"] == EXPECTED["rule_hash"]
    with RacketBridge() as bridge:
        fresh_outputs = [evaluate(bridge, program, grid) for grid in grids]
        runtime = bridge.runtime_identity
    assert fresh_outputs == retained_outputs

    def upper_only(grid: list[list[int]]) -> list[list[int]]:
        if module.observe_overrides(grid)["dot_band"] == "upper":
            return module.rule_mirror(grid)
        return [row[:] for row in grid]

    rival_outputs = [upper_only(grid) for grid in grids]
    fits_demonstrations = rival_outputs[:4] == fresh_outputs[:4]
    fails_query = rival_outputs[4] != fresh_outputs[4]
    assert fits_demonstrations and fails_query

    retained_counterexample = json.loads(
        (retained_dir / "counterexample.json").read_text(encoding="utf-8")
    )
    assert retained_counterexample["rival"]["fits_all_four_demonstrations"] is True
    assert retained_counterexample["rival"]["fails_query"] is True
    assert [row["input"] for row in retained_counterexample["demonstrations"]] == grids[:4]
    assert retained_counterexample["query"]["input"] == grids[4]

    report = {
        "schema": "arcpuzzles-ticket-audit-replay-v1",
        "ticket_id": "ticket-5ade2f847a3f6eb8",
        "type": "audit_replay",
        "task_id": TASK_ID,
        "return_id": RETURN_ID,
        "status": "reproduced",
        "source_bound": True,
        "identity": {
            **hashes,
            "audit_record": audit_record_hash,
            "retained_files_verified": len(retained_hashes),
            "rule_hash": module.RULE_HASH,
        },
        "lesson": {
            "seed": seed,
            "difficulty": difficulty,
            "sample_indexes": list(range(first_index, first_index + 5)),
            "dot_bands": dot_bands,
            "all_inputs_pass_self_check": all(not errors for errors in validator_errors),
            "fresh_racket_matches_retained": fresh_outputs == retained_outputs,
            "rival": "upper_only",
            "fits_all_four_demonstrations": fits_demonstrations,
            "fails_query": fails_query,
        },
        "audit_disposition": "bounded claim reproduced; existing audit remains needs_triage",
        "runtime": runtime,
    }
    path = out_dir / "result.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "source_bound": report["source_bound"],
        "retained_files_verified": report["identity"]["retained_files_verified"],
        "dot_bands": dot_bands,
        "fits_demonstrations": fits_demonstrations,
        "fails_query": fails_query,
        "result": str(path),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
