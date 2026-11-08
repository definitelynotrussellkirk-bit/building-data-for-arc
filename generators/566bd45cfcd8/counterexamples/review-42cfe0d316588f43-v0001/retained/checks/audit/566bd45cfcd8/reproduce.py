from __future__ import annotations
import hashlib, importlib.util, json, pathlib

TASK_ID = "566bd45cfcd8"
ROOT = pathlib.Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

nonsense = [[2, 3, 5]]
requested_height = 15
sample_index = 1
overridden = module.generate(17, sample_index, difficulty="easy", grid_h=requested_height)
result = {
    "task_id": TASK_ID,
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "validator_counterexample": {
        "grid": nonsense,
        "self_check": module.self_check(nonsense),
        "has_rectangular_color5_frame": False,
        "has_key_above_frame": False,
        "finding": "self_check accepts a 1x3 [2,3,5] row that contains no frame, no key, and no marked crossing.",
    },
    "override_counterexample": {
        "seed": 17,
        "sample_index": sample_index,
        "difficulty": "easy",
        "requested_grid_h": requested_height,
        "observed_dimensions": [len(overridden), len(overridden[0])],
        "finding": "The placement fallback silently replaces the requested 15-row grid with its fixed 18x22 fallback.",
    },
}
print(json.dumps(result, indent=2, sort_keys=True))
