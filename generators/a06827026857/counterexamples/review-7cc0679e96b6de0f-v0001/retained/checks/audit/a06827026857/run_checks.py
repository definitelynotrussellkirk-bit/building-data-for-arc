"""Record exact commands for the bounded Python-only adversarial audit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

p=argparse.ArgumentParser()
p.add_argument("--work-root",type=Path,required=True)
root=p.parse_args().work_root.resolve()
repo=root/"repo"
out=root/"checks/audit/a06827026857"
env=os.environ.copy()
env["PYTHONPATH"]=str(repo/"src")+os.pathsep+str(repo/"shared/runtime")
env["PYTHONDONTWRITEBYTECODE"]="1"
commands=[
 ["../../.venv-review/bin/python","../checks/audit/a06827026857/audit_probe.py",
  "--repo",".","--out","../checks/audit/a06827026857"],
 ["../../.venv-review/bin/python","-m","pytest","-q","--import-mode=importlib",
  "-p","no:cacheprovider","generators/a06827026857/tests/test_generator_contract.py",
  "--junitxml=../checks/audit/a06827026857/task-tests.xml"],
]
receipts=[]
for i,argv in enumerate(commands):
    completed=subprocess.run(argv,cwd=repo,env=env,capture_output=True,text=True,timeout=120)
    log=out/("probe.log" if i==0 else "task-tests.log")
    log.write_text(completed.stdout+completed.stderr)
    receipts.append({"cwd":"repo","argv":argv,"exit_code":completed.returncode,
        "environment":{"PYTHONPATH":"src:shared/runtime","PYTHONDONTWRITEBYTECODE":"1"},
        "evidence_paths":["checks/audit/a06827026857/"+log.name,
            "checks/audit/a06827026857/"+("report.json" if i==0 else "task-tests.xml")]})
    print(json.dumps({"command_index":i,"exit_code":completed.returncode,"log":str(log.relative_to(root))}))
    print(completed.stdout,end="")
test_counts=None
junit=out/"task-tests.xml"
if junit.exists():
    doc=ET.parse(junit).getroot()
    suites=[doc] if doc.tag=="testsuite" else doc.findall("testsuite")
    test_counts={name:sum(int(s.get(name,0)) for s in suites) for name in ("tests","errors","failures","skipped")}
source=repo/"generators/a06827026857/generator.py"
receipt={"schema":"arcpuzzles-python-only-audit-execution-v1",
    "verification_commands":receipts,"test_counts":test_counts,
    "generator_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
    "racket_subprocesses":0,
    "note":"Direct Python-only selected task tests; this is not a public audit preset or a full battery."}
(out/"execution.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
raise SystemExit(0 if all(r["exit_code"]==0 for r in receipts) else 1)
