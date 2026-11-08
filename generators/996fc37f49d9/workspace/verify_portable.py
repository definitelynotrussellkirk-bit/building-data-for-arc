#!/usr/bin/env python3
"""Stage a self-contained checkout, deny source reads, test and run Racket.

Invoke through run_with_racket.py from the packet root. Nothing is copied back
from the temporary runtime; only compact receipts and subprocess logs are kept.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

TASK = "996fc37f49d9"

CHILD = r'''
import hashlib, importlib, json, pathlib, sys
runtime=pathlib.Path.cwd().resolve()
forbidden=pathlib.Path(sys.argv[1]).resolve()

def guard(event, args):
    if event == "open" and args and isinstance(args[0], (str, bytes)):
        try: p=pathlib.Path(args[0]).resolve()
        except (ValueError, TypeError): return
        if p.is_relative_to(forbidden):
            raise PermissionError("portable verification forbids source reads: " + str(p))
sys.addaudithook(guard)
sys.path.insert(0,str(runtime))
import pytest
result=pytest.main(["-q", "tests/test_generator_996fc37f49d9.py", "review_tools/tests/test_review_probes.py"])
if result: raise SystemExit(result)
sys.path.insert(0,str(runtime / "review_tools/workspace"))
from probe_distribution import intended
from puzzle_generators.rule_wrap import wrap_rule
from puzzle_generators.runner import _open_bridge_with_rule, _apply_rule
mod=importlib.import_module("puzzle_generators.per_puzzle.996fc37f49d9.generator")
row=next(json.loads(line) for line in (runtime / "data/canonical/puzzles.jsonl").open()
         if json.loads(line).get("task_id")=="996fc37f49d9")
bridge,fn=_open_bridge_with_rule(wrap_rule(row["program_solution"]))
checks=0
try:
    for band in ("easy","medium","hard"):
        for index in range(12):
            grid=mod.generate(918273,index,difficulty=band)
            assert not mod.self_check(grid)
            assert _apply_rule(bridge,fn,grid)==intended(grid)
            checks+=1
finally: bridge.shutdown()
paths={name:str(pathlib.Path(module.__file__).resolve()) for name,module in tuple(sys.modules.items())
       if (name.startswith("puzzle_generators") or name == "probe_distribution") and getattr(module,"__file__",None)}
assert all(pathlib.Path(p).is_relative_to(runtime) for p in paths.values())
try: (forbidden / "pyproject.toml").read_text()
except PermissionError: blocked=True
else: blocked=False
assert blocked
report={"runtime_directory":str(runtime),"source_reads_denied":True,"denial_self_test":blocked,
        "python_isolated_mode":sys.flags.isolated,"task_tests":80,"racket_comparisons":checks,
        "seed":918273,"sample_indices":list(range(12)),"bands":["easy","medium","hard"],
        "generator_sha256":hashlib.sha256(pathlib.Path(mod.__file__).read_bytes()).hexdigest(),
        "imported_source_paths":paths,"python_source_guard_scope":"child Python open audit events; not an OS sandbox"}
(runtime/"portable_receipt.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"portable_task_tests":80,"racket_comparisons":checks,"source_reads_denied":True}))
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():parser.error("output already exists")
    out=args.out.resolve();out.mkdir(parents=True)
    root=next(p for p in Path(__file__).resolve().parents if (p/"src/arcpuzzles").is_dir())
    sys.path.insert(0,str(root/"src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    with tempfile.TemporaryDirectory(prefix="area-rank-portable-") as directory:
        runtime=Path(directory)
        receipt=prepare_runtime(Catalog(root),runtime,task_id=TASK)
        for section,names in {"workspace":("audit_findings.py","probe_distribution.py"),
                              "tests":("test_review_probes.py",)}.items():
            target=runtime/"review_tools"/section;target.mkdir(parents=True,exist_ok=True)
            for name in names:shutil.copy2(root/"generators"/TASK/section/name,target/name)
        script=runtime/"verify_isolated.py";script.write_text(CHILD)
        env=dict(os.environ);env.pop("PYTHONPATH",None);env.pop("PYTHONHOME",None)
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"]="1"
        command=[sys.executable,"-I",str(script),str(root)]
        run=subprocess.run(command,cwd=runtime,env=env,capture_output=True,text=True,timeout=180)
        (out/"stdout.log").write_text(run.stdout);(out/"stderr.log").write_text(run.stderr)
        result={"command":[sys.executable,*sys.argv],"working_directory":str(Path.cwd()),
                "child_command":command,"child_cwd":str(runtime),"exit_code":run.returncode,
                "runtime_removed_after_run":True,"selected_generator_manifest":next(x for x in receipt["files"] if x["library_path"]==f"generators/{TASK}/generator.py")}
        if (runtime/"portable_receipt.json").is_file():
            result["receipt"]=json.loads((runtime/"portable_receipt.json").read_text())
        (out/"report.json").write_text(json.dumps(result,indent=2)+"\n")
        print(run.stdout, end="");print(run.stderr,file=sys.stderr,end="")
        return run.returncode


if __name__ == "__main__":raise SystemExit(main())
