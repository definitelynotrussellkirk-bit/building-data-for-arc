from pathlib import Path
import json
from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
mod, source, digest = load_selected_generator("b46564e50781", root=ROOT)
grid = json.loads((HERE.parent / "input.json").read_text())
ray_counts = [mod._ray_paint_count(grid, r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 5)]
assert digest == "ffaac6b7cf236dc0d566c43c54d2bf2730dedaddec4f352b70aa38e5513bc676"
assert mod.self_check(grid) == []
assert ray_counts == [0, 7]
print(json.dumps({"generator_sha256": digest, "self_check": [], "ray_counts": ray_counts}, sort_keys=True))
