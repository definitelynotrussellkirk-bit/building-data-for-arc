"""Bounded independent Python screen of the supported minimum lessons."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "repo"
PARAMETRIC = REPO / "generators/323fded12174/workspace/parametric"


def load(name):
    spec = importlib.util.spec_from_file_location("_minimum_"+name, PARAMETRIC / (name+".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit, family = load("audit_native"), load("prototype")
paths = [PARAMETRIC / (name+".py") for name in ("prototype", "audit_native")]
binding = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
report = {"status": "running", "source_files_sha256": binding, "episodes": [], "findings": [],
          "limits": "Six minimum-count lessons, seeds0/17/101 under both settings, twenty fixed rivals, Python only. This is not native qualification or universal identifiability."}
for seed in (0, 17, 101):
    for settings in audit.SETTINGS:
        episode = family.generate(seed, settings, demos=3, queries=4)
        assert all(pair["output"] == audit.reference(pair["input"], settings)
                   for pair in episode["train"]+episode["test"])
        fitted = {name: all(audit.rival_reference(pair["input"], settings, name) == pair["output"]
                           for pair in episode["train"]) for name in audit.RIVALS}
        disagreements = {name: [i for i, pair in enumerate(episode["test"])
                                if audit.rival_reference(pair["input"], settings, name) != pair["output"]]
                         for name, survives in fitted.items() if survives}
        for name, indices in disagreements.items():
            if indices:
                report["findings"].append({"seed": seed, "settings": settings,
                                           "rival": name, "queries": indices, "episode": episode})
        report["episodes"].append({"seed": seed, "settings": settings, "demos": 3, "queries": 4,
                                   "fit_frozen_before_query": True, "demo_fits": fitted,
                                   "survivor_query_disagreements": disagreements})
assert binding == {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
report["status"] = "passed" if not report["findings"] else "failed"
(HERE / "minimum-screen.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
print(json.dumps({"status": report["status"], "episodes": len(report["episodes"]), "findings": len(report["findings"])}))
raise SystemExit(0 if report["status"] == "passed" else 1)
