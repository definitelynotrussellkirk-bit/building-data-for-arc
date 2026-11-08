"""Replay the frozen pre-repair tie-color lesson with exact stored Racket rules."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "repo"
RUNTIME = ROOT / "shared/runtime"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    frozen = json.loads((HERE / "python-screen.json").read_bytes())
    for name, expected in frozen["source_files_sha256"].items():
        assert hashlib.sha256((HERE / "source" / name).read_bytes()).hexdigest() == expected
    report = {key: frozen[key] for key in ("seed", "settings", "train", "test", "programs", "source_files_sha256", "source_snapshot", "scene_facts")}
    report.update({"schema": "c1fd38e5812b-tie-color-before-v1", "fit_frozen_before_query": True,
                   "training_admitted": False, "visibility": "controller_private"})
    outputs = {name: {"train": [], "test": []} for name in frozen["programs"]}
    with _local_imports(RUNTIME, HERE):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            report["racket"] = identity
            for name, program in frozen["programs"].items():
                for pair in frozen["train"]:
                    outputs[name]["train"].append(_grid(apply(program, pair["input"])))
            report["demo_survivors"] = [name for name in frozen["programs"]
                if outputs[name]["train"] == [p["output"] for p in frozen["train"]]]
            assert set(report["demo_survivors"]) == {"reference", "tie_min_color"}
            for name, program in frozen["programs"].items():
                for pair in frozen["test"]:
                    outputs[name]["test"].append(_grid(apply(program, pair["input"])))
        finally:
            bridge.close()
    assert outputs["reference"]["test"] == [p["output"] for p in frozen["test"]]
    differences = [i for i, (actual, other) in enumerate(zip(outputs["reference"]["test"], outputs["tie_min_color"]["test"])) if actual != other]
    assert differences == frozen["query_disagreements"]
    report.update({"status": "reproduced_supported_episode_ambiguity", "outputs": outputs,
                   "query_disagreement_indices": differences, "racket_evaluations": 14,
                   "scope": "Exact supported three-demo seed0 lesson before repair; conditional minimum-color tie-break fits all demos and disagrees on query0. Production canonical source is unchanged."})
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"status": report["status"], "query_disagreement_indices": differences, "racket_evaluations": 14}))


if __name__ == "__main__":
    main()
