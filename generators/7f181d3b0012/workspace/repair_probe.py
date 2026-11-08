"""Bounded source-bound override/symmetry reproduction, no assertion of approval."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("repair_generator", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
parser = argparse.ArgumentParser()
parser.add_argument("--out", required=True)
args = parser.parse_args()
report = {"task_id": gen.TASK_ID, "source_sha256": hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(), "unknown_override": None, "asymmetry_failure": None, "palette_failure": None, "cases": 0}
try:
    g = gen.generate(23, 9, __override_contract_unknown_axis__=123)
    report["unknown_override"] = {"accepted": True, "same_as_default": g == gen.generate(23, 9)}
except (ValueError, TypeError) as exc:
    report["unknown_override"] = {"accepted": False, "error": str(exc)}
for seed in range(80):
    for h, w, n, symmetric in ((2, 3, 2, False), (3, 2, 2, False), (4, 2, 4, True), (3, 2, 4, True), (2, 6, 6, True)):
        kw = dict(grid_h=h, grid_w=w, palette_size=n, ud_asymmetric=not symmetric, texture="frame")
        report["cases"] += 1
        try:
            g = gen.generate(seed, seed, **kw)
        except (ValueError, TypeError) as exc:
            if report["palette_failure"] is None:
                report["palette_failure"] = {"seed": seed, "overrides": kw, "error": str(exc)}
            continue
        observed = gen.observe_overrides(g)
        if observed["palette_size"] != n and report["palette_failure"] is None:
            report["palette_failure"] = {"seed": seed, "overrides": kw, "grid": g, "observed": observed}
        if observed["ud_asymmetric"] != (not symmetric) and report["asymmetry_failure"] is None:
            report["asymmetry_failure"] = {"seed": seed, "overrides": kw, "grid": g, "observed": observed}
Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
