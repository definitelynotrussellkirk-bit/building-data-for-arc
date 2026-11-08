from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3] / "repo"
sys.path.insert(0, str(ROOT / "shared" / "runtime"))
from reviewer_support import load_selected_generator  # noqa: E402

TASK_ID = "97e1d2aa0bc3"
module, source, digest = load_selected_generator(TASK_ID, root=ROOT)
base = Path(__file__).resolve().parent
grid = json.loads((base / "input.json").read_text())
result = {
    "task_id": TASK_ID,
    "generator_path": str(source.relative_to(ROOT)),
    "generator_sha256": digest,
    "self_check": module.self_check(grid),
    "strict_canonical_like": module.strict_canonical_like(grid),
}
(base / "validator.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
