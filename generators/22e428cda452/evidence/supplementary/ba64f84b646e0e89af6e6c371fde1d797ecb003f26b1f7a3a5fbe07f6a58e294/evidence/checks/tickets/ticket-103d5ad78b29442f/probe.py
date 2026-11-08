"""One source-bound privacy probe for the assigned retained parameter evidence."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path.cwd()
TICKET_ID = "ticket-103d5ad78b29442f"
EXPECTED_MANIFEST = "49b81db8826d6ef96d781205489921dc57e12304dcb983d816f5f079a9ac0b07"
EXPECTED_SOURCE = "b4655068a725dddba8295203ddfc360f896393209ba21c47b62d9010609ffd5a"
SEED = "b8939dd7b0d2bf08d274247c1756f7d363f815e51a14bbd8ec1b102e1bcac8fd"

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()

audit = json.loads((ROOT / "AUDIT_ASSIGNMENT.json").read_bytes())
ticket = next(t for t in audit["tickets"] if t["ticket_id"] == TICKET_ID)
assert ticket["type"] == "parameter_queries"
assert ticket["consumer"] == "task_support_or_prototype_followup"
assert ticket["seed"] == SEED
assert ticket["rule_hash"] == "2e6c42d70b0f"
assert ticket["source"]["sha256"] == EXPECTED_SOURCE
assert ticket["evidence_manifest"]["sha256"] == EXPECTED_MANIFEST
bindings = {}
def bound_read(relative, expected):
    p = ROOT / relative
    assert p.is_file() and not p.is_symlink(), relative
    raw = p.read_bytes()
    digest = sha(raw)
    assert digest == expected, (relative, digest, expected)
    bindings[relative] = digest
    return raw

bound_read(ticket["source"]["path"], EXPECTED_SOURCE)
manifest = json.loads(bound_read(ticket["evidence_manifest"]["path"], EXPECTED_MANIFEST))
assert manifest["generator_sha256"] == EXPECTED_SOURCE
assert manifest["canonical_rule_hash"] == "2e6c42d70b0f"
assert manifest["production_parametric_api"] is False
assert manifest["variant_approved"] is False
listed = {"repo/" + row["path"]: row for row in manifest["files"]}
def retained_read(relative):
    row = listed[relative]
    raw = bound_read(relative, row["sha256"])
    assert len(raw) == row["bytes"], relative
    return raw

home = "repo/generators/22e428cda452/workspace/parametric/"
prototype = home + "prototype.py"
retained_read(prototype)
spec = importlib.util.spec_from_file_location("ticket_103d5ad78b29442f_prototype", ROOT / prototype)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
owner_prefix = home + "evidence/owner-current/"
owner = json.loads(retained_read(owner_prefix + "manifest.json"))
assert owner["complete_episodes"] == 2
assert {r["projection_inset"] for r in owner["records"]} == {1, 2}
rows = []
for record in owner["records"]:
    private_path = owner_prefix + record["private_path"]
    public_path = owner_prefix + record["public_path"]
    private = json.loads(retained_read(private_path))
    public = json.loads(retained_read(public_path))
    original_public = module.public_challenge(private)
    assert public == original_public
    name = module.public_filename(private)
    assert name == module.public_filename(public) == Path(public_path).name
    assert sha(canonical(public)) == record["public_sha256"]
    assert set(public) == {"schema", "train", "test"}
    assert set(public["test"]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])

    # One deterministic private mutation holds every public cell fixed.
    changed = deepcopy(private)
    mutation_number = int(SEED[:16], 16)
    changed["meta"] = {"seed": mutation_number,
                       "projection_inset": 3 - private["meta"]["projection_inset"],
                       "private_mutation_nonce": SEED}
    changed["program"] = "private program replaced for identifier-invariance probe"
    changed["test"]["output"] = [[(cell + 1 + mutation_number % 8) % 10 for cell in row]
                                    for row in changed["test"]["output"]]
    assert changed["test"]["output"] != private["test"]["output"]
    assert module.public_filename(changed) == name
    assert module.public_challenge(changed) == public

    # Positive control: changing a visible query cell must change the identifier.
    visible = deepcopy(private)
    visible["test"]["input"][0][0] = (visible["test"]["input"][0][0] + 1) % 10
    changed_name = module.public_filename(visible)
    assert changed_name != name
    rows.append({"projection_inset": record["projection_inset"],
                 "private_path": private_path, "public_path": public_path,
                 "demonstration_count": len(public["train"]), "query_count": 1,
                 "public_filename": name, "public_content_sha256": sha(canonical(public)),
                 "private_mutation_filename_unchanged": True,
                 "private_mutation_public_content_unchanged": True,
                 "visible_query_input_mutation_filename_changed": True,
                 "visible_control_filename": changed_name,
                 "public_query_answers_masked": True})

print(json.dumps({"schema": "arcpuzzles-supplementary-parameter-privacy-probe-v1",
                  "ticket_id": TICKET_ID, "task_id": "22e428cda452", "seed": SEED,
                  "status": "pass", "probe_count": 1,
                  "boundary": "corrected owner-current public export and filename exclude private metadata, program and held-out answers",
                  "source_bindings_sha256": bindings, "episodes": rows,
                  "limitations": ["Only the two retained owner-current episodes were examined.",
                                  "Each retained episode has three demonstrations and one query; four-query support is not established.",
                                  "No generator sampling, Racket label replay, peer battery, or variant approval was performed.",
                                  "Finite mutation checks support this exporter boundary, not universal privacy or safety."]},
                 sort_keys=True, indent=2))
