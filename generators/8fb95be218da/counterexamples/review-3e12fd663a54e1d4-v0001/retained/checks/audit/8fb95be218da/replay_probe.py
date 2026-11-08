from pathlib import Path
import json
from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
mod, source, digest = load_selected_generator("8fb95be218da", root=ROOT)
grid = mod.generate(19, 3, difficulty="hard", n_panels=7)
expected = json.loads((HERE.parent / "input.json").read_text())
full_dividers = [c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)]
assert digest == "920cf11cef34eebad261d4e69446a863ad6dcdcd1737f72ce9849161501ec5f4"
assert grid == expected
assert mod.self_check(grid, difficulty="hard") == []
assert len(grid[0]) == 29
assert len(full_dividers) + 1 == 6
print(json.dumps({"generator_sha256": digest, "requested_n_panels": 7, "observed_n_panels": 6, "width": len(grid[0])}, sort_keys=True))
