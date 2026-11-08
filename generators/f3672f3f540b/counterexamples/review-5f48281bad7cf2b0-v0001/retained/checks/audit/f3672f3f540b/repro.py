from __future__ import annotations
import hashlib, json
from reviewer_support import find_root, load_selected_generator

TASK = "f3672f3f540b"
root = find_root(__file__)
gen, path, source_sha = load_selected_generator(TASK, root=root)

def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()

def attempt(**kwargs):
    try:
        grid = gen.generate(991, 17, difficulty="hard", **kwargs)
        return {"status": "accepted", "sha256": digest(grid), "shape": [len(grid), len(grid[0])], "self_check": gen.self_check(grid)}
    except Exception as exc:
        return {"status": "rejected", "error": f"{type(exc).__name__}: {exc}"}

base = attempt()
probes = {
    "grid_h_8": attempt(grid_h=8),
    "grid_h_16": attempt(grid_h=16),
    "grid_w_9": attempt(grid_w=9),
    "grid_w_18": attempt(grid_w=18),
    "n_border_1": attempt(n_border=1),
    "n_border_5": attempt(n_border=5),
    "n_interior_1": attempt(n_interior=1),
    "n_interior_4": attempt(n_interior=4),
    "blob_size_1": attempt(blob_size=1),
    "blob_size_6": attempt(blob_size=6),
    "texture_warm": attempt(texture="warm"),
    "texture_cool": attempt(texture="cool"),
    "texture_varied": attempt(texture="varied"),
}
try:
    bool_grid = gen.generate(991, True, difficulty="hard")
    bool_sample = {"status": "accepted", "sha256": digest(bool_grid)}
except Exception as exc:
    bool_sample = {"status": "rejected", "error": f"{type(exc).__name__}: {exc}"}

ignored = [name for name, result in probes.items() if result.get("sha256") == base.get("sha256")]
out = {
    "schema": "arc-audit-repro-v1",
    "task_id": TASK,
    "generator_path": str(path),
    "generator_sha256": source_sha,
    "base": base,
    "probes": probes,
    "accepted_but_byte_identical_to_base": ignored,
    "sample_index_bool": bool_sample,
    "semantic_contract_declared": any(hasattr(gen, name) for name in ("strict_canonical_like", "SEMANTIC_WITNESSES", "lesson_identifiable")),
}
print(json.dumps(out, indent=2, sort_keys=True))
