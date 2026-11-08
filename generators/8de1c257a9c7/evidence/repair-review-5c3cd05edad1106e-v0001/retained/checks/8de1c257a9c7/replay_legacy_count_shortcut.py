"""Replay the count-only rule against the freshly captured old prototype."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
CHECKS = ROOT.parent / "checks/8de1c257a9c7"
PATH = ROOT / "generators/8de1c257a9c7/workspace/parametric/audit_native.py"


def main():
    spec = importlib.util.spec_from_file_location("legacy_count_replay_audit", PATH)
    audit = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = audit
    spec.loader.exec_module(audit)
    baseline_path = CHECKS / "legacy-baseline.json"
    baseline = json.loads(baseline_path.read_text())
    rows = []
    with audit.CachedEvaluator() as evaluator:
        for episode in baseline["episodes"]:
            setting = episode["meta"]["stamp_transform"]
            settings = {"stamp_transform": setting}
            name = "historical_count_" + setting
            program = audit.rival_program(name, settings)
            train_rows = []
            # Establish demo fit before inspecting or running this episode's query.
            for pair in episode["train"]:
                output = evaluator(program, pair["input"])
                assert output == audit.rival_output(name, pair["input"], settings)
                assert output == pair["output"]
                train_rows.append({"input_sha256": audit.digest(pair["input"]), "output": output})
            query_rows = []
            for pair in episode["test"]:
                output = evaluator(program, pair["input"])
                assert output == audit.rival_output(name, pair["input"], settings)
                assert output == pair["output"]
                query_rows.append({"input_sha256": audit.digest(pair["input"]), "output": output})
            rows.append({"settings": settings, "rival_name": name, "rival_program": program,
                         "rival_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                         "fits_all_demonstrations": True, "fits_old_query": True,
                         "demonstration_fit_frozen_before_query": True,
                         "train": train_rows, "test": query_rows})
        report = {
            "schema": "stamp-legacy-count-shortcut-replay-v1", "status": "reproduced",
            "scope": "The count-only rule reproduces the captured finite-bank prototype. Its sampled query is not mislabeled and does not disagree; the finding is bypassed geometry extraction, not an observed old query failure.",
            "baseline_sha256": hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
            "legacy_prototype_sha256": baseline["prototype_sha256"],
            "audit_source_sha256": hashlib.sha256(PATH.read_bytes()).hexdigest(),
            "racket": evaluator.identity, "racket_evaluations": evaluator.evaluations,
            "records": evaluator.records, "episodes": rows,
        }
    path = CHECKS / "legacy-count-shortcut.json"
    with path.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "episodes": len(rows),
                      "racket_evaluations": report["racket_evaluations"]}))


if __name__ == "__main__":
    main()
