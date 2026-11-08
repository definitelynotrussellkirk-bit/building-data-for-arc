from __future__ import annotations
import hashlib, importlib.util, json, pathlib

TASK_ID = "f6e6de72c068"
ROOT = pathlib.Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

requested = {
    "grid_h": 3,
    "grid_w": 5,
    "motifs": 1,
    "decoys": 0,
    "n_distinct_colors": 1,
    "palette_kind": "warm",
    "density": "sparse",
}
baseline = module.generate(123, 0, difficulty="easy")
overridden = module.generate(123, 0, difficulty="easy", **requested)
result = {
    "task_id": TASK_ID,
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "seed": 123,
    "sample_index": 0,
    "difficulty": "easy",
    "requested_overrides": requested,
    "observed_dimensions": [len(overridden), len(overridden[0])],
    "observed_firing_triples": module._count_firing_triples(overridden),
    "self_check": module.self_check(overridden),
    "identical_to_no_override_call": overridden == baseline,
    "grid": overridden,
    "finding": "Advertised exact controls are ignored; even out-of-band dimensions and motif/decoy requests return the unchanged default sample.",
}
print(json.dumps(result, indent=2, sort_keys=True))
