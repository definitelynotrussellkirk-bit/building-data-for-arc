from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))
SOURCE = ROOT / "generators/a2d9d069c7d5/generator.py"
spec = importlib.util.spec_from_file_location("audit_a2d9d069c7d5", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
rows = []
for name in module.DEGENERATE_TEXTURES:
    grid = module.generate(0, 0, texture=name)
    rows.append({
        "texture": name,
        "shape": [len(grid), len(grid[0])],
        "self_check_errors": module.self_check(grid),
    })
result = {
    "schema": "arcpuzzles-audit-reproduction-v1",
    "task_id": "a2d9d069c7d5",
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "declared_degenerate_textures": list(module.DEGENERATE_TEXTURES),
    "lawful_degenerate_declaration_present": hasattr(module, "LAWFUL_DEGENERATE_TEXTURES"),
    "results": rows,
    "finding_reproduced": all(not row["self_check_errors"] for row in rows),
}
Path(__file__).with_name("reproduction.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
