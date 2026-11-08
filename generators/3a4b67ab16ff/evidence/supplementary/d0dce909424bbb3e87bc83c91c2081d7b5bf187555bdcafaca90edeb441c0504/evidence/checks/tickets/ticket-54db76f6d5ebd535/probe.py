from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path.cwd().resolve()
CHECK = ROOT.parent / "checks" / "tickets" / "ticket-54db76f6d5ebd535"
TASK_ID = "3a4b67ab16ff"
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
ASSET_MANIFEST = (
    ROOT
    / "generators"
    / TASK_ID
    / "counterexamples"
    / "review-860d9cbbd103d929-v0001"
    / "audit_assets.json"
)
AUDIT_INDEX = ROOT / "generators" / TASK_ID / "evidence" / "review_index.json"
CANONICAL_RECORD = (
    ROOT
    / "shared"
    / "data"
    / "base"
    / "solutions"
    / "training"
    / "1c02dbbe__3a4b67ab16ff.json"
)
EXPECTED = {
    "source_sha256": "c643621f6d5d606ea6b988bf7d67ec5486ef288c11dc7b0f3fe43a33a611cd31",
    "assets_manifest_sha256": "3a1df38b1be903ee703537ef5ee97a121a89ad492ce40e8adf6508513304bf8c",
    "audit_index_sha256": "ad4a96d604cc69b5b2941e995a61b44a07e6e3f50fdbcad0b5f3a072ec438284",
    "audited_generator_sha256": "abd406bd9626d25aba8dc67db0971b3722302a2959e2b6453dcbba2cfb431b7f",
    "witness_sha256": "a64f761f5ce3b942828f903724ffdda48684501a9e6e9fb4fbe84eab37504a31",
    "rule_hash": "32c694357bd0",
    "probe_seed": "0220a56d6fa5253f0634d224366e5ed159fde2ae83cf87e2d6feb79332841a69",
}

sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared" / "runtime")]
from arcpuzzles.parametric_worker import _real_evaluator  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_sha256(program: str) -> str:
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()


def load_module():
    spec = importlib.util.spec_from_file_location("audit_replay_3a4b67ab16ff", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not create current generator import spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    identities = {
        "source_sha256": sha256(SOURCE),
        "assets_manifest_sha256": sha256(ASSET_MANIFEST),
        "audit_index_sha256": sha256(AUDIT_INDEX),
    }
    for key, actual in identities.items():
        if actual != EXPECTED[key]:
            raise AssertionError(f"{key} drifted: {actual}")

    manifest = json.loads(ASSET_MANIFEST.read_text())
    if manifest["audited_generator_sha256"] != EXPECTED["audited_generator_sha256"]:
        raise AssertionError("audited source identity in retained manifest drifted")
    witness_entry = next(
        row
        for row in manifest["files"]
        if row["path"].endswith("3a4b67ab16ff_counterexample.json")
    )
    witness_path = ROOT / witness_entry["path"].removeprefix("generators/")
    # The retained paths are rooted at generators/, while ROOT already contains it.
    if not witness_path.is_file():
        witness_path = ROOT / witness_entry["path"]
    if sha256(witness_path) != EXPECTED["witness_sha256"]:
        raise AssertionError("retained witness bytes drifted")
    witness = json.loads(witness_path.read_text())

    module = load_module()
    if module.RULE_HASH != EXPECTED["rule_hash"]:
        raise AssertionError(f"current rule hash drifted: {module.RULE_HASH}")

    grid = witness["input"]
    retained_actual = witness["actual_racket_output"]
    retained_rival = witness["rival_output"]
    validator_result = module.self_check(grid)
    current_python = module.rule_mirror(grid)
    current_rival = module._endpoint_only_bbox_rule(grid)
    witness_predicate = module._distributed_extrema_refutes_endpoint_only_bbox(grid)

    canonical_record = json.loads(CANONICAL_RECORD.read_text())
    program = canonical_record["racket_target"]["raw_code"]
    program_sha = normalized_sha256(program)
    if not program_sha.startswith(EXPECTED["rule_hash"]):
        raise AssertionError(f"canonical program hash drifted: {program_sha}")

    apply, runtime_identity, bridge = _real_evaluator(ROOT / "shared" / "runtime")
    try:
        current_racket = apply(program, grid)
    finally:
        bridge.close()

    checks = {
        "retained_validator_result_was_empty": witness["validator_result"] == [],
        "current_validator_result_is_empty": validator_result == [],
        "current_python_matches_retained_racket": current_python == retained_actual,
        "current_racket_matches_retained_racket": current_racket == retained_actual,
        "current_python_matches_current_racket": current_python == current_racket,
        "current_rival_matches_retained_rival": current_rival == retained_rival,
        "canonical_differs_from_endpoint_shortcut": current_racket != current_rival,
        "current_witness_predicate_recognizes_case": witness_predicate is True,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise AssertionError("audit replay failed checks: " + ", ".join(failed))

    probe_seed = int(EXPECTED["probe_seed"][:16], 16)
    repaired_sample = module.generate(
        probe_seed,
        0,
        difficulty="medium",
        scene_profile="distributed_extrema",
    )
    repaired_analysis = module._analysis(repaired_sample)
    repaired_canonical = module.rule_mirror(repaired_sample)
    repaired_rival = module._endpoint_only_bbox_rule(repaired_sample)
    repair_checks = {
        "profile_is_distributed_extrema": repaired_analysis.get("scene_profile")
        == "distributed_extrema",
        "sample_is_lawful": repaired_analysis.get("errors") == [],
        "sample_refutes_endpoint_shortcut": repaired_canonical != repaired_rival,
        "registered_witness_recognizes_sample": module._distributed_extrema_refutes_endpoint_only_bbox(
            repaired_sample
        ),
    }
    repair_failed = [name for name, passed in repair_checks.items() if not passed]
    if repair_failed:
        raise AssertionError("current coverage repair failed checks: " + ", ".join(repair_failed))

    result = {
        "schema": "arc-review-audit-replay-v1",
        "ticket_id": "ticket-54db76f6d5ebd535",
        "task_id": TASK_ID,
        "status": "completed",
        "pinned_identity": {
            **identities,
            "audited_generator_sha256": manifest["audited_generator_sha256"],
            "retained_witness_sha256": sha256(witness_path),
            "rule_hash": module.RULE_HASH,
            "canonical_program_normalized_sha256": program_sha,
            "audit_return_id": manifest["return_id"],
        },
        "bounded_claim": {
            "description": witness["rival_rule"],
            "domain_status": witness["domain_status"],
            "reproduced": True,
            "checks": checks,
            "input": grid,
            "canonical_output": current_racket,
            "endpoint_shortcut_output": current_rival,
        },
        "current_generator_assessment": {
            "coverage_gap_addressed": True,
            "evidence": (
                "The current generator registers distributed_extrema, its witness predicate "
                "recognizes both the retained case and a freshly generated pinned-seed sample, "
                "and that sample refutes endpoint_only_bbox."
            ),
            "repair_checks": repair_checks,
            "fresh_sample": repaired_sample,
        },
        "audit_clearance": {
            "cleared": False,
            "reason": (
                "This bounded replay reproduces the old semantic witness and confirms the "
                "current coverage repair; maintainer assessment is still required."
            ),
        },
        "runtime": runtime_identity,
    }
    (CHECK / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "bounded_claim_reproduced": True,
                "coverage_gap_addressed": True,
                "audit_cleared": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
