"""Actual Racket-backed publication order of the retained legacy writer."""
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


ROOT = find_root(__file__)
HOME = ROOT / "generators/0ae119475d57"
SOURCE = HOME / "workspace/parametric/prototype.py"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_public_publication_is_buffered_sorted_and_keeps_private_association(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("legacy_order_0ae119475d57", SOURCE)
    prototype = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prototype)
    destination = tmp_path / "export"
    generated, physical = [], []
    generate = prototype._generate_episode_with_bridge
    write = Path.write_bytes

    def observed_generate(*args, **kwargs):
        public, private = generate(*args, **kwargs)
        generated.append(private["public_id"])
        return public, private

    def observed_write(path, payload):
        if path.parent == destination / "public":
            physical.append({"path": path.name, "public_id": hashlib.sha256(payload).hexdigest(),
                             "completed_episodes_before_write": len(generated)})
        return write(path, payload)

    monkeypatch.setattr(prototype, "_generate_episode_with_bridge", observed_generate)
    monkeypatch.setattr(Path, "write_bytes", observed_write)
    manifest = prototype.write_evidence(destination, seeds=[1, 0], demo_count=2, query_count=4, root=ROOT)
    public_ids = [row["public_id"] for row in manifest["episodes"]]
    physical_ids = [row["public_id"] for row in physical]
    payload_checks, association_checks = [], []
    for row in manifest["episodes"]:
        path = destination / row["public_file"]
        payload = path.read_bytes()
        public = json.loads(payload)
        private = json.loads((destination / row["private_file"]).read_bytes())
        payload_checks.append(payload == public_challenge_bytes(public)
            and path.name == f"challenge-{public_challenge_id(public)}.json"
            and public_challenge_id(public) == row["public_id"]
            and set(public) == {"train", "test"}
            and len(public["train"]) == 2 and len(public["test"]) == 4
            and all(set(p) == {"input", "output"} for p in public["train"])
            and all(set(p) == {"input"} for p in public["test"]))
        selected = private["parameter"]["overlap_precedence"]
        association_checks.append(private["public_id"] == row["public_id"]
            and private["seed"] == row["seed"]
            and private["parameter"] == row["parameter"] == prototype.parameter_for_seed(row["seed"])
            and private["program_sha256"] == manifest["programs"][selected]["sha256"]
            and private["query_answers"] == private["rival_checks"][selected]["query_predictions"]
            and [p["output"] for p in public["train"]] == private["rival_checks"][selected]["demonstration_predictions"])
    canonical = json.loads((destination / "private/canonical-default-check.json").read_bytes())
    checks = {
        "reverse_seed_order_exercises_unsorted_generation": generated != sorted(generated),
        "all_episodes_buffered_before_publication": all(row["completed_episodes_before_write"] == 2 for row in physical),
        "physical_public_writes_sorted": physical_ids == sorted(physical_ids),
        "manifest_index_sorted": public_ids == sorted(public_ids),
        "public_inventory_exact": len(physical) == len(set(public_ids)) == 2
            and set(public_ids) == set(physical_ids)
            and {path.name for path in (destination / "public").iterdir()} == {row["path"] for row in physical},
        "strict_canonical_public_bytes": all(payload_checks),
        "private_associations_preserved": all(association_checks),
        "canonical_default_replayed": manifest["canonical_default_unchanged"]
            and len(canonical) == 4 and all(row["matched"] for row in canonical),
        "protected_racket": manifest["racket_runtime"].get("backend") == "racket"
            and manifest["racket_runtime"].get("protected") is True,
    }
    proof = {"schema": "0ae119475d57-legacy-public-order-proof-v1",
        "status": "passed" if all(checks.values()) else "failed",
        "source_binding": {"prototype_sha256": digest(SOURCE), "test_sha256": digest(Path(__file__)),
            "generator_sha256": digest(HOME / "generator.py"),
            "canonical_program_sha256": manifest["canonical_source_sha256"],
            "prior_task_manifest_sha256": digest(HOME / "workspace/parametric/evidence/manifest.json")},
        "racket": manifest["racket_runtime"], "input_seed_order": [1, 0],
        "generated_public_ids": generated, "physical_public_writes": physical,
        "manifest_public_ids": public_ids, "checks": checks,
        "export_manifest_sha256": digest(destination / "manifest.json"),
        "limits": "Two legacy episodes, two demos/four queries each; physical writes observed while real Racket labels execute. No native qualification or acceptance."}
    (tmp_path / "proof.json").write_text(json.dumps(proof, sort_keys=True, indent=2) + "\n")
    assert all(checks.values()), {name: value for name, value in checks.items() if not value}
