import json, os, sys
from pathlib import Path
from arcpuzzles import check_jobs
import pytest, numpy, PIL
out = Path.cwd().parent / "checks/repository-triage"
path = Path("/proc") / str(os.getpid()) / "stat"
report = {"pid":os.getpid(),"proc_pid_stat_path":str(path),"proc_exists":Path("/proc").exists(),"proc_pid_stat_exists":path.exists(),"self_stat_exists":Path("/proc/self/stat").exists(),"birth_probe":check_jobs._birth(os.getpid()),"interpreter":sys.executable,"python_no_user_site":os.environ.get("PYTHONNOUSERSITE"),"dependencies":{"pytest":pytest.__version__,"numpy":numpy.__version__,"Pillow":PIL.__version__}}
try:
    report["proc_pid_stat"] = path.read_text()
except OSError as exc:
    report["proc_read_error"] = repr(exc)
try:
    report["proc_self_stat_pid"] = Path("/proc/self/stat").read_text().split()[0]
except OSError as exc:
    report["proc_self_stat_read_error"] = repr(exc)
(out / "proc-probe.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
