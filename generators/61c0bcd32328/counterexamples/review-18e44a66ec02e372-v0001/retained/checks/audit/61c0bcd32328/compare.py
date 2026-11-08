"""Compare retained public Racket execution with the singleton-noise rival."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = Path.cwd()


def read(name):
    return json.loads((OUT / name).read_text())


prep = read("preparation.json")
execution = read("racket.json")
mirror = read("mirror.json")["outputs"]
rivals = read("rival.json")["outputs"]
records = execution["results"]
assert len(records) == 2
assert all(r["error"] is None and r["valid_output"] for r in records)
assert execution["generator_sha256"] == prep["generator_sha256"]
assert execution["executed_rule_hash"] == prep["normalized_rule_hash"]
assert execution["rule_hash_matches_catalog"]
assert [r["output"] for r in records] == mirror
assert records[0]["output"] == rivals[0]
assert records[1]["output"] != rivals[1]
diffs = []
for index, record in enumerate(records):
    diffs.append([
        {"row": r, "col": c, "racket": value, "rival": rivals[index][r][c]}
        for r, row in enumerate(record["output"])
        for c, value in enumerate(row)
        if value != rivals[index][r][c]
    ])
assert diffs == [[], [{"row": 0, "col": 7, "racket": 1, "rival": 4}]]
source = ROOT / "generators/61c0bcd32328/generator.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == prep["generator_sha256"]
result = {
    "finding": "singleton-corner noise shortcut survives the supplied corner shape catalogue",
    "generator_sha256_unchanged": prep["generator_sha256"],
    "executed_rule_hash": execution["executed_rule_hash"],
    "executed_rule_text_sha256": execution["rule_text_sha256"],
    "self_check": prep["self_check"],
    "reference_outputs_valid": [r["valid_output"] for r in records],
    "mirror_matches_reference": [True, True],
    "rival_matches_reference": [True, False],
    "reference_rival_differences": diffs,
    "input_sha256": [r["input_sha256"] for r in records],
    "reference_output_sha256": [r["output_sha256"] for r in records],
    "rival_output_sha256": [hashlib.sha256(json.dumps(g, separators=(",", ":")).encode()).hexdigest() for g in rivals],
    "bounds": {
        "generated_controls": 1,
        "mutated_lawful_inputs": 1,
        "public_reference_inputs_executed": 2,
        "canonical_unique_pairs_compared_with_rival": 4,
        "canonical_pair_occurrences": 8,
        "random_seed_sweep": False,
        "battery_run": False,
    },
    "evidence_sha256": {
        name: hashlib.sha256((OUT / name).read_bytes()).hexdigest()
        for name in ("prepare.py", "input.json", "preparation.json", "rival.json", "mirror.json", "racket.json")
    },
}
(OUT / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
