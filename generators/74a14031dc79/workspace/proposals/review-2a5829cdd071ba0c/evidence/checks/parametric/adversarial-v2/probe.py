from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

TASK_ID = "74a14031dc79"
SOURCE = Path("generators") / TASK_ID / "workspace/parametric/prototype.py"
EVIDENCE = Path("../checks/parametric/occupancy-rule-v2")
OUT = Path("../checks/parametric/adversarial-v2/result.json")


def load_prototype():
    spec = importlib.util.spec_from_file_location("occupancy_rule_v2_probe", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    prototype = load_prototype()
    root = Path.cwd()
    source_sha256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()

    with prototype.RacketBridge() as bridge:
        episode = prototype.make_episode(
            1,
            demo_count=12,
            query_count=4,
            root=root,
            bridge=bridge,
        )
        pairs = episode["train"] + episode["test"]
        distinct_inputs = len({prototype.grid_sha256(pair["input"]) for pair in pairs})
        rule_source = prototype.materialize_rule(
            episode["parameters"]["occupancy_rule"], root=root
        )
        all_queries_racket_labeled = all(
            prototype.execute_rule(
                rule_source, pair["input"], bridge=bridge, root=root
            )
            == pair["output"]
            for pair in episode["test"]
        )

    try:
        prototype.make_episode(1, demo_count=13, query_count=4, root=root)
    except Exception as exc:
        oversize_rejection = {"type": type(exc).__name__, "message": str(exc)}
    else:
        raise AssertionError("17-pair episode was unexpectedly accepted")

    public_base = prototype.public_filename(episode)
    private_mutation = copy.deepcopy(episode)
    private_mutation["seed"] = 999
    private_mutation["parameters"] = {"occupancy_rule": "and"}
    private_mutation["rule"] = {"racket_source": "private mutation"}
    private_mutation["test"][0]["output"][0][0] = (
        private_mutation["test"][0]["output"][0][0] + 1
    ) % 10
    public_private_mutation = prototype.public_filename(private_mutation)

    visible_mutation = copy.deepcopy(episode)
    visible_mutation["test"][0]["input"][0][0] = (
        visible_mutation["test"][0]["input"][0][0] + 1
    ) % 10
    public_visible_mutation = prototype.public_filename(visible_mutation)

    with tempfile.TemporaryDirectory(prefix="occupancy-v2-tamper-") as tmp:
        tampered = Path(tmp) / "evidence"
        shutil.copytree(EVIDENCE, tampered)
        public_path = sorted((tampered / "public").glob("challenge-*.json"))[0]
        public_path.write_bytes(public_path.read_bytes() + b"\n")
        try:
            prototype.verify_evidence(tampered, root=root)
        except Exception as exc:
            tampered_public_rejection = {
                "type": type(exc).__name__,
                "message": str(exc),
            }
        else:
            raise AssertionError("tampered public bytes were unexpectedly accepted")

    with tempfile.TemporaryDirectory(prefix="occupancy-v2-order-") as tmp:
        unsorted = Path(tmp) / "evidence"
        shutil.copytree(EVIDENCE, unsorted)
        report_path = unsorted / "report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["episodes"] = list(reversed(report["episodes"]))
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        try:
            prototype.verify_evidence(unsorted, root=root)
        except Exception as exc:
            unsorted_report_rejection = {
                "type": type(exc).__name__,
                "message": str(exc),
            }
        else:
            raise AssertionError("unsorted public-ID report was unexpectedly accepted")

    result = {
        "schema": "arcpuzzles-parametric-adversarial-pass-v1",
        "status": "pass",
        "task_id": TASK_ID,
        "source": {"path": str(SOURCE), "sha256": source_sha256},
        "surfaces": [
            "sampler_count_boundaries",
            "public_private_export_and_verifier",
        ],
        "max_supported_case": {
            "demo_count": 12,
            "query_count": 4,
            "total_inputs": len(pairs),
            "distinct_inputs": distinct_inputs,
            "all_queries_racket_labeled": all_queries_racket_labeled,
        },
        "oversize_rejection": oversize_rejection,
        "public_identifier": {
            "base": public_base,
            "unchanged_after_private_metadata_and_query_answer_mutation": (
                public_private_mutation == public_base
            ),
            "changed_after_visible_query_input_mutation": (
                public_visible_mutation != public_base
            ),
        },
        "tampered_public_rejection": tampered_public_rejection,
        "unsorted_report_rejection": unsorted_report_rejection,
    }
    expected = (
        distinct_inputs == 16
        and all_queries_racket_labeled
        and oversize_rejection["type"] == "ValueError"
        and result["public_identifier"][
            "unchanged_after_private_metadata_and_query_answer_mutation"
        ]
        and result["public_identifier"]["changed_after_visible_query_input_mutation"]
        and tampered_public_rejection["type"] == "AssertionError"
        and unsorted_report_rejection["type"] == "AssertionError"
    )
    if not expected:
        result["status"] = "fail"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not expected:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
