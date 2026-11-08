from __future__ import annotations
import hashlib, json
from reviewer_support import find_root, load_selected_generator

TASK = "a5b0638997f5"
root = find_root(__file__)
gen, path, source_sha = load_selected_generator(TASK, root=root)

def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()

def attempt(**kwargs):
    try:
        grid = gen.generate(991, 17, difficulty="easy", **kwargs)
        return {"status": "accepted", "sha256": digest(grid), "shape": [len(grid), len(grid[0])], "self_check": gen.self_check(grid)}
    except Exception as exc:
        return {"status": "rejected", "error": f"{type(exc).__name__}: {exc}"}

base = attempt()
probes = {
    "texture_default": attempt(texture="default"),
    "texture_warm": attempt(texture="warm"),
    "texture_cool": attempt(texture="cool"),
    "texture_varied": attempt(texture="varied"),
    "palette_kind_warm": attempt(palette_kind="warm"),
    "palette_size_negative": attempt(palette_size=-1),
    "ch_w_advertised_2": attempt(ch_w=2),
}
try:
    bool_grid = gen.generate(991, True, difficulty="easy")
    bool_sample = {"status": "accepted", "sha256": digest(bool_grid)}
except Exception as exc:
    bool_sample = {"status": "rejected", "error": f"{type(exc).__name__}: {exc}"}

out = {
    "schema": "arc-audit-repro-v1",
    "task_id": TASK,
    "generator_path": str(path),
    "generator_sha256": source_sha,
    "base": base,
    "probes": probes,
    "dead_helpful_textures": [name for name, result in probes.items() if name.startswith("texture_") and result.get("sha256") == base.get("sha256")],
    "palette_kind_ignored": probes["palette_kind_warm"].get("sha256") == base.get("sha256"),
    "negative_palette_size_accepted_and_ignored": probes["palette_size_negative"].get("sha256") == base.get("sha256"),
    "sample_index_bool": bool_sample,
    "semantic_contract_declared": any(hasattr(gen, name) for name in ("strict_canonical_like", "SEMANTIC_WITNESSES", "lesson_identifiable")),
}
print(json.dumps(out, indent=2, sort_keys=True))
