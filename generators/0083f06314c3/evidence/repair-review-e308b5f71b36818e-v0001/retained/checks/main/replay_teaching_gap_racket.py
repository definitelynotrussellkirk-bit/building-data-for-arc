"""Replay the retained pre-repair case using exact qualified protected Racket.

Run through the packet's review.py run wrapper. This executes exactly eight
case/program pairs: three demonstrations and one query, each under the fixed
canonical program and the current parameter-aware few_groups rival. The old
sampler binding remains separate from the qualified execution-source binding.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
TASK_ID = "0083f06314c3"
TASK_HOME = ROOT / f"generators/{TASK_ID}/workspace/parametric"
LIMIT = 8


def load_audit():
    path = TASK_HOME / "audit.py"
    if not path.is_file() or path.is_symlink() or path.resolve() != path:
        raise ValueError("Audit must be a regular file in the exact current task home")
    name = "_qualified_teaching_gap_audit_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def replay(qualification_path, case_path, output):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Replay report must be new")
    audit = load_audit()
    report = {"schema": "arcpuzzles-protected-teaching-gap-replay-v1",
              "task_id": TASK_ID, "status": "running", "private": True,
              "racket_evaluations": 0, "evaluation_limit": LIMIT,
              "executions": [], "training_admitted": False,
              "limits": ["One retained pre-repair case; no universal uniqueness claim.",
                         "The sampler remains historical; current qualified programs supply the replayed labels.",
                         "This replay neither qualifies nor accepts a generator and does not admit training data."]}
    bridge = None
    try:
        qualification, native, episodes, execution_path = audit.qualification_inputs(qualification_path)
        binding, contract = qualification["source_binding"], qualification["contract"]
        case_path = Path(case_path).resolve()
        case_hash = audit.file_hash(case_path)
        case = json.loads(case_path.read_bytes())
        audit.require(case.get("schema") == "arcpuzzles-parametric-python-teaching-gap-v1"
                      and case.get("task_id") == TASK_ID
                      and case.get("status") == "pre_repair_counterexample"
                      and case.get("settings") == {"orientation": "fixed"}
                      and len(case.get("train", [])) == 3,
                      "Expected the retained three-demo fixed-setting pre-repair case")
        old_files = {row["path"]: row["sha256"] for row in case["source_files"]}
        program_path = f"generators/{TASK_ID}/workspace/parametric/canonical.rkt"
        audit.require(old_files[program_path] == binding["canonical_program_sha256"],
                      "Retained case and qualification must bind the same exact canonical program")
        report.update(source_binding=copy.deepcopy(binding),
                      pre_repair_source_files=copy.deepcopy(case["source_files"]),
                      replay_source_sha256=audit.file_hash(Path(__file__)),
                      case={"path": str(case_path), "sha256": case_hash,
                            "seed": case["seed"], "query_index": case["query_index"],
                            "original_label_source": case["label_source"]},
                      qualification={"path": str(Path(qualification_path).resolve()),
                                     "sha256": audit.file_hash(qualification_path),
                                     "execution_path": str(execution_path),
                                     "execution_sha256": audit.file_hash(execution_path)})
        runtime = ROOT / "shared/runtime"
        with audit._local_imports(runtime, TASK_HOME):
            prototype = audit.load_prototype()
            setting = {"orientation": "fixed"}
            program = prototype.program(copy.deepcopy(setting))
            rival = prototype.rival_programs(copy.deepcopy(setting))["few_groups"]
            audit.require(qualification["programs"].get(audit.raw(setting).decode().strip())
                          == audit.program_hash(program) == old_files[program_path],
                          "Replay program differs from the exact qualified canonical authority")
            audit.check_source(binding, contract)
            apply, identity, bridge = audit._real_evaluator(runtime)
            report["racket"] = {"backend": identity["backend"], "protected": identity["protected"]}
            report["racket_runtime_identity"] = copy.deepcopy(identity)
            report["programs"] = {
                "reference": {"program": program, "sha256": audit.program_hash(program)},
                "few_groups": {"program": rival, "sha256": audit.program_hash(rival)}}
            rows = [("train", index, pair) for index, pair in enumerate(case["train"])]
            rows.append(("query", case["query_index"], case["query"]))
            for split, index, pair in rows:
                grid, expected = audit._grid(pair["input"]), audit._grid(pair["output"])
                actual = {}
                for name, code in (("reference", program), ("few_groups", rival)):
                    audit.require(report["racket_evaluations"] < LIMIT, "Replay budget exceeded")
                    report["racket_evaluations"] += 1
                    row = {"split": split, "index": index, "program": name,
                           "program_sha256": audit.program_hash(code),
                           "input_sha256": audit.digest(grid)}
                    report["executions"].append(row)
                    actual[name] = audit._grid(apply(code, copy.deepcopy(grid)))
                    row.update(output_sha256=audit.digest(actual[name]),
                               matches_recorded_label=actual[name] == expected)
                audit.require(actual["reference"] == expected,
                              f"Protected canonical label differs for {split} {index}")
                if split == "train":
                    audit.require(actual["few_groups"] == expected,
                                  f"Few-groups rival does not fit recorded demonstration {index}")
                else:
                    audit.require(actual["few_groups"] == audit._grid(case["counterfactual_output"])
                                  and actual["few_groups"] != expected,
                                  "Protected rival must reproduce the exact recorded wrong query answer")
            audit.require(report["racket_evaluations"] == LIMIT, "Expected exactly eight evaluations")
            audit.require(audit.file_hash(case_path) == case_hash, "Case bytes changed during replay")
            audit.check_source(binding, contract)
            report.update(status="passed", canonical_labels_verified=4,
                          rival_demonstrations_fitted=3, rival_query_differs=True,
                          recorded_wrong_query_output_verified=True,
                          label_source="Fresh execution of both exact programs through protected Racket")
    except Exception as error:
        report.update(status="failed", error={"type": type(error).__name__, "message": str(error)})
    finally:
        if bridge is not None:
            bridge.close()
        audit.write_json(output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--case", type=Path, default=HERE / "teaching-gap-before.json")
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    report = replay(options.qualification, options.case, options.out)
    print(json.dumps({"status": report["status"], "report": str(options.out.resolve()),
                      "racket_evaluations": report["racket_evaluations"],
                      "canonical_labels_verified": report.get("canonical_labels_verified"),
                      "rival_demonstrations_fitted": report.get("rival_demonstrations_fitted"),
                      "rival_query_differs": report.get("rival_query_differs"),
                      "error": report.get("error")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
