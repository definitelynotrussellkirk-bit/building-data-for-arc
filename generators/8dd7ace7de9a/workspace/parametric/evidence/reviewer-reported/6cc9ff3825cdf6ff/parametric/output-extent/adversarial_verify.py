from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
TASK = REPO / "generators" / "8dd7ace7de9a"
sys.path.insert(0, str(TASK / "workspace"))
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reference_probe import canonical_program, recover_details
from reviewer_support import public_challenge_bytes, public_challenge_id

spec = importlib.util.spec_from_file_location(
    "prototype_under_adversarial_review", TASK / "workspace/parametric/prototype.py"
)
assert spec is not None and spec.loader is not None
prototype = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)

programs = prototype.materialize_programs()
assert programs["full_grid"] == canonical_program()
program_hashes = {key: hashlib.sha256(value.encode()).hexdigest() for key, value in programs.items()}

reports = []
for setting_dir in (HERE / "full-grid", HERE / "tile-only"):
    private_path = next((setting_dir / "private").glob("*.json"))
    public_path = next((setting_dir / "public").glob("*.json"))
    episode = json.loads(private_path.read_text())
    visible = episode["public_challenge"]
    visible_bytes = public_challenge_bytes(visible)
    public_id = public_challenge_id(visible)
    assert public_path.name == f"{public_id}.json"
    assert public_path.read_bytes() == visible_bytes
    assert episode["public_id"] == public_id
    assert episode["program_sha256"] == program_hashes
    assert episode["n_train"] == 3 and episode["n_test"] == 4
    assert len(episode["pairs"]) == 7
    assert len({json.dumps(pair["input"], separators=(",", ":")) for pair in episode["pairs"]}) == 7
    assert episode["all_demos_distinguish"] is True
    assert episode["rival_fits_all_demos"] is False

    for pair in episode["pairs"]:
        for grid in (pair["input"], *pair["outputs_by_parameter"].values()):
            assert type(grid) is list and grid
            assert all(type(row) is list and row for row in grid)
            assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
        recovered = recover_details(pair["input"])
        assert recovered is not None
        full, pr, pc = recovered
        assert pair["outputs_by_parameter"]["full_grid"] == full
        assert pair["outputs_by_parameter"]["tile_only"] == [row[:pc] for row in full[:pr]]
        assert pair["selected_output"] == pair["outputs_by_parameter"][episode["parameter"]]

    # Hidden/private mutations must not affect the visible content ID.
    hidden_mutation = deepcopy(episode)
    hidden_mutation["seed"] = -999
    hidden_mutation["parameter"] = "tile_only" if episode["parameter"] == "full_grid" else "full_grid"
    hidden_mutation["programs"] = {"redacted": "changed"}
    hidden_mutation["test"][0]["selected_output"] = [[9]]
    assert public_challenge_id(hidden_mutation["public_challenge"]) == public_id

    reports.append({
        "parameter": episode["parameter"],
        "public_id": public_id,
        "pairs": len(episode["pairs"]),
        "distinct_inputs": 7,
        "all_demos_distinguish": True,
        "public_exact_bytes": True,
        "hidden_mutation_id_stable": True,
        "numeric_types_exact": True,
        "independent_output_shape_check": True,
    })

result = {
    "schema": "8dd7ace7de9a-output-extent-adversarial-v1",
    "surfaces": ["parameter/Racket-retained-output parity", "public/private export and numeric types"],
    "canonical_default_exact": True,
    "program_sha256": program_hashes,
    "episodes": reports,
    "findings": [],
    "bounded_limit": "Retained two seeds and two settings only; no claim over all seeds or future canonical source changes.",
}
(HERE / "adversarial-result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
