"""One source-bound minimum-demo/four-query prototype support probe."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


TICKET = "ticket-b2c519e32abded56"
TASK = "3f533a120cf5"
TICKET_SEED = "e4e617c1623445de585ecde24ab2b8204a8c1b9c17b2dc211245d5fd61252eaf"
SEED = int(TICKET_SEED, 16) % (2**63)
ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent
HOME = f"generators/{TASK}"
SOURCE = f"{HOME}/generator.py"
MANIFEST = f"{HOME}/workspace/parametric/evidence/manifest.json"
PROTOTYPE = f"{HOME}/workspace/parametric/prototype.py"
EXPECTED = {
    SOURCE: "c63333b9cd8acc75cd147d76deff12590f9267cb7286d9d18f14cddf2bf8cd5c",
    MANIFEST: "c7b66db5b56bba43f2c06bb324e0b13a84f1026e42ae0d406b1dcfd938144892",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    for path, wanted in EXPECTED.items():
        assert sha(ROOT / path) == wanted, f"Pinned bytes changed: {path}"
    inventory = json.loads((ROOT / MANIFEST).read_bytes())
    assert inventory["task_id"] == TASK
    assert inventory["canonical_rule_hash"] == "df7e059f3faa"
    relevant = {
        PROTOTYPE,
        f"{HOME}/workspace/parametric/README.md",
        f"{HOME}/tests/test_parametric_paint_semantics.py",
    }
    entries = {entry["path"]: entry for entry in inventory["files"]}
    for path in relevant:
        EXPECTED[path] = entries[path]["sha256"]
    before = {path: sha(ROOT / path) for path in EXPECTED}
    assert before == EXPECTED, "Consumed prototype/evidence does not match pinned inventory"
    write("bindings-before.json", {"expected": EXPECTED, "observed": before})

    spec = importlib.util.spec_from_file_location("_ticket_3f533a120cf5_prototype", ROOT / PROTOTYPE)
    prototype = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = prototype
    spec.loader.exec_module(prototype)
    batch = OUT / "batch"
    report = prototype.materialize(batch, seed_start=SEED, episode_count=1, demo_count=1, query_count=4)
    assert report["status"] == "prototype"
    assert report["runtime_identity"]["backend"] == "racket"
    assert report["runtime_identity"]["protected"] is True
    assert report["source"]["generator_sha256"] == EXPECTED[SOURCE]
    assert report["source"]["canonical_normalized_rule_hash"] == "df7e059f3faa"
    assert len(report["episodes"]) == 1
    row = report["episodes"][0]
    episode = json.loads((batch / row["private_path"]).read_bytes())
    assert episode["parameters"] == {"key_target": "bbox_holes", "key_order": "reverse"}
    assert episode["seed"] == SEED
    assert len(episode["train"]) == 1 and len(episode["test"]) == 4
    inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == 5
    selected = episode["setting_id"]
    analysis = episode["analysis"]
    assert analysis["demo_compatible_settings"] == [selected]
    assert analysis["demos_refute_all_rivals"] is True
    assert analysis["query_identifiability"] == [
        {"query_index": index, "compatible_settings_from_demos": [selected], "identified": True}
        for index in range(4)
    ]
    program_path = batch / episode["rule_relative_path"]
    assert sha(program_path) == episode["racket_sha256"] == row["racket_sha256"]
    public_path = batch / row["public_path"]
    expected_public = {
        "train": [{"input": pair["input"], "output": pair["output"]} for pair in episode["train"]],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }
    assert public_path.read_bytes() == public_challenge_bytes(expected_public)
    assert row["public_id"] == public_challenge_id(expected_public)
    assert public_path.name == f"challenge-{row['public_id']}.json"
    assert json.loads(public_path.read_bytes()) == expected_public
    after = {path: sha(ROOT / path) for path in EXPECTED}
    assert after == before
    write("bindings-after.json", {"observed": after, "all_pinned_files_unchanged": True})
    observation = {
        "ticket_id": TICKET, "task_id": TASK, "boundary": "one demonstration and four queries",
        "ticket_seed": TICKET_SEED, "derived_seed": SEED, "seed_derivation": "int(ticket_seed,16) mod 2**63",
        "parameters": episode["parameters"], "demos": 1, "queries": 4,
        "distinct_inputs_across_both_splits": 5,
        "racket_backed_labels_materialized": 5,
        "racket_backend": "racket", "racket_protected": True,
        "demo_only_survivors": analysis["demo_compatible_settings"],
        "query_certificate_rows": 4, "public_projection_counts": {"train": 1, "test": 4},
        "public_queries_omit_answers": True, "public_visible_bytes_and_id_match": True,
        "prototype_status": report["status"], "variant_approved": False, "training_admitted": False,
        "all_pinned_files_unchanged": True,
        "scope": "One fresh setting and seed at the minimum-demo/four-query boundary. No all-settings qualification, acceptance, verifier replay, or full battery.",
    }
    write("observation.json", observation)
    print(json.dumps(observation, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
