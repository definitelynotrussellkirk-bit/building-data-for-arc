from __future__ import annotations
import importlib.util
from pathlib import Path

TASK = "d8b498586958"
path = Path(__file__).resolve().parents[3] / "repo" / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_target", path)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
print("bool seed accepted:", gen.generate(True, 0, difficulty="medium") == gen.generate(1, 0, difficulty="medium"))
print("negative sample accepted shape:", (len(gen.generate(991, -1)), len(gen.generate(991, -1)[0])))
