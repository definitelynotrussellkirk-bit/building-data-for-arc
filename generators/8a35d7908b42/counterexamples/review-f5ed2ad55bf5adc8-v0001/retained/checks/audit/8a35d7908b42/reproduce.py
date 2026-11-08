from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
TASK = "8a35d7908b42"
sys.path.insert(0, str(ROOT / "repo" / "src"))
source = ROOT / "repo" / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_8a35", source)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
def sha_grid(g): return hashlib.sha256(json.dumps(g,separators=(",",":")).encode()).hexdigest()
base = mod.generate(7, 3, difficulty="easy")
over = mod.generate(7, 3, difficulty="easy", n_blobs=1)
unknown = mod.generate(7, 3, difficulty="easy", bogus_axis=123)
zero = [[0]*8 for _ in range(7)]
colors = sorted({v for row in over for v in row if v})
report = {
 "schema":"arcpuzzles-audit-reproducer-v1", "task_id":TASK,
 "generator_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
 "call":{"seed":7,"sample_index":3,"difficulty":"easy","overrides":{"n_blobs":1}},
 "advertised_axis":mod.AXES["n_blobs"], "realized_dimensions":[len(over),len(over[0])],
 "realized_nonzero_colors":colors, "realized_blob_count":len(colors),
 "requested_blob_count":1, "override_ignored":over==base,
 "unknown_key_accepted":unknown==base, "self_check_generated":mod.self_check(over),
 "self_check_all_zero":mod.self_check(zero), "all_zero_grid":zero,
 "input":over, "input_sha256":sha_grid(over)
}
assert report["override_ignored"] and report["unknown_key_accepted"]
assert report["realized_blob_count"] != 1 and report["self_check_all_zero"] == []
out=Path(__file__).resolve().parent
(out/"override-validator-audit.json").write_text(json.dumps(report,indent=2)+"\n")
(out/"input.json").write_text(json.dumps(over)+"\n")
print(json.dumps({k:report[k] for k in ["generator_sha256","realized_blob_count","override_ignored","unknown_key_accepted","self_check_all_zero"]},indent=2))
