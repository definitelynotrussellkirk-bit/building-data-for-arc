from pathlib import Path
import json, os, re, subprocess, sys
WORK = Path.cwd().parent
OUT = WORK / "checks/repository-triage"
original = WORK / "checks/repository-tests.log"
nodes = re.findall(r"^FAILED (tests/[^\n]+)$", original.read_text(), re.M)
assert len(nodes) == len(set(nodes)) == 26
(OUT / "failed-nodes.json").write_text(json.dumps(nodes,indent=2)+"\n")
(OUT / "original.log").write_bytes(original.read_bytes())
argv = [str(WORK/".venv-review/bin/python"), "run_with_racket.py", str(WORK/".venv-review/bin/python"), "-m", "pytest", "-q", "-ra", *nodes, "--junitxml=../checks/repository-triage/rerun.xml"]
env = dict(os.environ, PYTHONNOUSERSITE="1")
metadata = {"cwd":".","payload_cwd":"repo","argv":argv,"environment":{"PYTHONNOUSERSITE":"1"},"exit_code":None,"evidence_paths":["checks/repository-triage/failed-nodes.json","checks/repository-triage/original.log","checks/repository-triage/rerun.log","checks/repository-triage/rerun.xml"],"interpreter":str(WORK/".venv-review/bin/python"),"selected_node_count":26}
(OUT/"commands.json").write_text(json.dumps({"commands":[metadata]},indent=2)+"\n")
print("Rerunning exactly 26 failed nodes under " + argv[0],flush=True)
with (OUT/"rerun.log").open("w") as log:
    completed = subprocess.run(argv,cwd=WORK,env=env,stdout=log,stderr=subprocess.STDOUT)
metadata["exit_code"] = completed.returncode
(OUT/"commands.json").write_text(json.dumps({"commands":[metadata]},indent=2)+"\n")
print((OUT/"rerun.log").read_text()[-24000:])
print("Exit code:",completed.returncode)
