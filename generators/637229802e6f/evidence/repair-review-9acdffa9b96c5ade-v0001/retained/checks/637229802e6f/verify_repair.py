"""Check current peer repair against retained protected-Racket labels."""
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator


HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
evidence_path = HERE / "marker-anchor-boundary.json"
before = json.loads(evidence_path.read_text())
gen, source, source_hash = load_selected_generator("637229802e6f", root=ROOT)
canonical = next(
    json.loads(line)["program_solution"]
    for line in canonical_path(ROOT).read_text().splitlines()
    if json.loads(line)["task_id"] == "637229802e6f"
)
assert canonical == before["canonical_program"]
pairs = (before["demonstrations"] + [before["query"]]
         + [before["aligned_control"]["extra_pair"]])
for pair in pairs:
    assert gen.generate(0, pair["sample_index"], difficulty="easy") == pair["input"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert gen.LESSON_COMPETITORS["marker_as_top_left"](pair["input"]) == pair["rival_output"]
reasons = gen.lesson_identifiable(before["demonstrations"], before["query"])
assert len(reasons) == 1 and "marker_as_top_left" in reasons[0]
contract = json.loads((HERE / "contract-after.json").read_text())
assert contract["generator_sha256"] == source_hash
assert len(contract["schedule_failures"]) == 6 and contract["schedule_cases"] == 48
report = {
    "task_id": "637229802e6f",
    "generator_sha256": source_hash,
    "before_generator_sha256": before["generator_sha256"],
    "protected_evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
    "canonical_program_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
    "canonical_program_unchanged": True,
    "sampled_inputs_unchanged": 5,
    "mirror_and_top_left_rival_match_retained_racket_labels": 5,
    "repaired_checker_reasons": reasons,
    "finite_schedule_rejections": 6,
    "finite_schedule_rotations": 48,
    "racket_reexecuted_this_check": False,
    "ok": True,
}
(HERE / "repair-verification.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, sort_keys=True))
