"""Mutation probes and real controls for the task-owned retained-census rescorer.

No generator or input census is modified. Malformed reports are supplied through
in-memory paths; only this probe's result file is written.
"""
from __future__ import annotations
import argparse
import contextlib
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from reviewer_support import find_root


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


class MemoryInput:
    def __init__(self, value): self.value = value
    def read_bytes(self): return json.dumps(self.value).encode()
    def __str__(self): return "<in-memory mutation probe>"


class MemoryOutput:
    def __init__(self): self.content = None
    def exists(self): return False
    @property
    def parent(self): return self
    def mkdir(self, **kwargs): pass
    def write_text(self, value): self.content = value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool",type=Path,required=True)
    parser.add_argument("--old",type=Path,required=True)
    parser.add_argument("--final",type=Path,required=True)
    parser.add_argument("--expect",choices=("vulnerable","guarded"),required=True)
    parser.add_argument("--out",type=Path,required=True)
    args = parser.parse_args()
    if args.out.exists(): parser.error("--out must be new")
    root = find_root(__file__)
    generator = root / "generators/e937c5b85cdd/generator.py"
    generator_before = hashlib.sha256(generator.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location("rescorer_under_test",args.tool)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    # The retained before-tool snapshot lives under checks rather than workspace.
    module.find_root = lambda unused: root
    old = json.loads(args.old.read_bytes())
    tiny = deepcopy(old)
    tiny["lessons"] = tiny["lessons"][:1]
    tiny["summary"].update(requested=1,materialized=1,pairs=4,rotations=4)
    band = tiny["lessons"][0]["band"]
    tiny["per_band"] = {band:deepcopy(tiny["per_band"][band])}
    tiny["per_band"][band].update(requested=1,materialized=1,pairs=4,rotations=4)
    tiny["sampler"].update(per_band=1,bands=[band])
    cases = {}
    def case(name, edit):
        value = deepcopy(tiny); edit(value); cases[name] = value
    case("empty_failed",lambda x:x.update(lessons=[],status="error",errors=["worker failed"]))
    case("empty_complete",lambda x:x.update(lessons=[]))
    case("partial_count",lambda x:x["summary"].update(requested=2))
    case("incomplete_status",lambda x:x.update(status="incomplete"))
    case("source_errors",lambda x:x.update(errors=["retained scoring error"]))
    case("execution_failure",lambda x:x["execution"].update(exit_code=2))
    case("execution_timeout",lambda x:x["execution"].update(timed_out=True))
    case("materialization_error",lambda x:x["summary"].update(materialization_errors=1))
    case("scoring_error",lambda x:x["summary"].update(scoring_errors=1))
    case("lesson_error",lambda x:x["lessons"][0].update(errors=["bad lesson"]))
    case("rotation_error",lambda x:x["lessons"][0]["rotations"][0].update(errors=["bad rotation"]))
    case("malformed_top_level",lambda x:x.clear())
    case("manifest_digest",lambda x:x.update(runtime_manifest_sha256="0"*64))
    case("instance_digest",lambda x:x["lessons"][0].update(instance_sha256="0"*64))
    case("rule_binding",lambda x:x.update(declared_rule_hash="000000000000"))
    def bad_manifest(x):
        row = next(row for row in x["runtime_manifest"]["files"]
                   if row["library_path"] == "generators/e937c5b85cdd/generator.py")
        row["sha256"] = "0"*64
        x["runtime_manifest_sha256"] = hashlib.sha256((json.dumps(x["runtime_manifest"],indent=2)+"\n").encode()).hexdigest()
    case("manifest_source_binding",bad_manifest)
    for name, replacement in (("missing_reference",None),("empty_reference",[]),
                               ("ragged_reference",[[6,6],[6]]),("boolean_reference",[[True]])):
        def bad_output(x,replacement=replacement):
            x["lessons"][0]["instance"]["test"][0]["output"] = replacement
            x["lessons"][0]["instance_sha256"] = digest(x["lessons"][0]["instance"])
        case(name,bad_output)
    def run(value):
        out = MemoryOutput()
        with patch.object(argparse.ArgumentParser,"parse_args",return_value=SimpleNamespace(census=MemoryInput(value),out=out)), contextlib.redirect_stdout(io.StringIO()):
            try:
                code = module.main()
                error = None
            except Exception as exc:
                code,error = 2,f"{type(exc).__name__}: {exc}"
        report = json.loads(out.content) if out.content else {}
        return {"exit_code":code,"status":report.get("status"),"errors":report.get("errors",[]),
                "raised":error,"summary":report.get("summary",{})}
    results = {name:run(value) for name,value in cases.items()}
    controls = {"old_complete":run(old),"final_complete":run(json.loads(args.final.read_bytes()))}
    false_clean = [name for name,row in results.items() if row["exit_code"] == 0]
    assert controls["old_complete"]["exit_code"] == 1,controls
    assert controls["old_complete"]["summary"]["length_three_paints_farther:production_ambiguous"] == 25
    assert controls["old_complete"]["summary"]["length_three_paints_farther:ambiguous_rotations"] == 141
    assert controls["final_complete"]["exit_code"] == 0,controls
    if args.expect == "guarded":
        assert not false_clean,false_clean
        assert all(row["status"] == "error" for row in results.values()),results
    else:
        assert {"empty_failed","empty_complete","source_errors"} <= set(false_clean),false_clean
    stable = hashlib.sha256(generator.read_bytes()).hexdigest() == generator_before
    assert stable and generator_before == "25b0edefd8fe5333c0d4d9ac13be097dc2fc59123cf13b5e5c4505014f014b4e"
    report = {"schema":"rescorer-validation-v1","expect":args.expect,
              "tool_path":str(args.tool),"tool_sha256":hashlib.sha256(args.tool.read_bytes()).hexdigest(),
              "probe_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "input_census_sha256":{"old":hashlib.sha256(args.old.read_bytes()).hexdigest(),
                                     "final":hashlib.sha256(args.final.read_bytes()).hexdigest()},
              "generator_sha256":generator_before,"generator_unchanged":stable,
              "mutation_cases":len(results),"false_clean_cases":false_clean,
              "results":results,"complete_controls":controls,"status":"passed"}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ("expect","mutation_cases","false_clean_cases","generator_unchanged","status")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
