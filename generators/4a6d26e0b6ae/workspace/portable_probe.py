"""Exercise the *copied* generator in a clean child from a declared runtime.

Run from packet_root with:
 python3 run_with_racket.py python3 generators/4a6d26e0b6ae/workspace/portable_probe.py --out ../checks/portable
No source-directory aliases, editable installs, PYTHONPATH, or Racket labels.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
TASK = "4a6d26e0b6ae"
CHILD = r'''
import hashlib, importlib.util, json, pathlib, sys
root = pathlib.Path.cwd().resolve()
source = root / "puzzle_generators/per_puzzle/4a6d26e0b6ae/generator.py"
spec = importlib.util.spec_from_file_location("relocated_generator", source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
import puzzle_generators.base as base
import puzzle_generators.helpers.grid as grid_helper
for path in (m.__file__, base.__file__, grid_helper.__file__):
    assert pathlib.Path(path).resolve().is_relative_to(root), path
rows=[]
for band in (None, "easy", "medium", "hard"):
    for seed in range(32):
        g = m.generate(seed, seed % 7, difficulty=band)
        errors=m.self_check(g, difficulty=band)
        assert not errors, (band,seed,errors)
        assert g == m.generate(seed, seed % 7, difficulty=band)
        rows.append({"seed":seed,"sample_index":seed % 7,"difficulty":band,
                     "input_sha256":hashlib.sha256(json.dumps(g).encode()).hexdigest()})
for texture in ("default", "horizontal", "vertical", "edge"):
    g=m.generate(7, 2, grid_h=14, grid_w=14, gap_count=8, texture=texture)
    assert not m.self_check(g, meta={"grid_h":14,"grid_w":14,"gap_count":8,"texture":texture})
print(json.dumps({"runtime_cwd":str(root),"generator_path":m.__file__,
 "base_path":base.__file__,"grid_helper_path":grid_helper.__file__,
 "generator_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
 "default_draws":len(rows),"dense_override_cases":4,"deterministic_repeats":len(rows),
 "rows":rows,"passed":True},indent=2))
'''

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args(); out=args.out.resolve(); out.mkdir(parents=True,exist_ok=True)
    # Repository API is used only in the staging parent, never the tested child.
    sys.path.insert(0,str(ROOT/"src"))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-portable-e15551ff-") as directory:
        runtime=Path(directory)
        manifest=prepare_runtime(Catalog(ROOT),runtime,task_ids=[TASK])
        (out/"runtime-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
        env={k:v for k,v in os.environ.items() if k not in {"PYTHONPATH","PYTHONHOME"}}
        result=subprocess.run([sys.executable,"-E","-c",CHILD],cwd=runtime,env=env,
                              text=True,capture_output=True,timeout=60)
        (out/"child-stdout.log").write_text(result.stdout)
        (out/"child-stderr.log").write_text(result.stderr)
        record={"command_cwd":str(Path.cwd()),"runtime_directory":str(runtime),
                "child_argv":[sys.executable,"-E","-c","<CHILD in portable_probe.py>"],
                "exit_code":result.returncode,"environment_removed":["PYTHONPATH","PYTHONHOME"],
                "source_sha256":hashlib.sha256((ROOT/"generators"/TASK/"generator.py").read_bytes()).hexdigest()}
        if result.returncode==0:
            payload=json.loads(result.stdout)
            if payload["generator_sha256"]!=record["source_sha256"]:
                raise RuntimeError("staged generator does not match selected source")
            record.update(payload)
        (out/"summary.json").write_text(json.dumps(record,indent=2)+"\n")
        print(json.dumps({k:v for k,v in record.items() if k!="rows"},indent=2))
        return result.returncode

if __name__=="__main__":
    raise SystemExit(main())
