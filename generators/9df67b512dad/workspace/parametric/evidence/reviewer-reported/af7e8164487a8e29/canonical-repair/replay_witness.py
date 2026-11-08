"""Replay the retained rotation witness against the canonical Racket rule."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys
import types

parser = argparse.ArgumentParser()
parser.add_argument("--runtime", type=Path, required=True)
args = parser.parse_args()
runtime = args.runtime.resolve()
sys.path[:0] = [str(runtime), str(runtime / "src")]
from reviewer_support import load_selected_generator
from scripts.generator_semantic_gate import _RuleOracle
from scripts.lesson_census import score_rotations

base = Path(__file__).resolve().parent
fixture = json.loads((base / "retained-witness.json").read_text())
current, source_path, source_sha = load_selected_generator("9df67b512dad", root=runtime)
before_bytes = (base / "generator.before.py").read_bytes()
before = types.ModuleType("canonical_generator_before_repair")
exec(compile(before_bytes, str(base / "generator.before.py"), "exec"), before.__dict__)
pairs = fixture["instance"]["train"] + fixture["instance"]["test"]
oracle = _RuleOracle("9df67b512dad")
assert oracle.ready, oracle.error
labels = []
try:
    rule_source_sha = hashlib.sha256(oracle.bundle.rule_source.encode()).hexdigest()
    rule_callable_sha = hashlib.sha256(oracle.bundle.rule_callable_text.encode()).hexdigest()
    for index, pair in enumerate(pairs):
        output, error = oracle.apply(pair["input"])
        labels.append({"pair_index": index, "matches_retained_label": output == pair["output"], "error": error})
        assert error is None and output == pair["output"], labels[-1]
        kwargs = {"difficulty": fixture["band"]}
        sample_index = fixture["sample_index"] + index
        assert current.generate(fixture["seed"], sample_index, **kwargs) == pair["input"]
        assert before.generate(fixture["seed"], sample_index, **kwargs) == pair["input"]
finally:
    oracle.close()

old_rotations = score_rotations(before, before.LESSON_COMPETITORS, fixture["instance"])
new_rotations = score_rotations(current, current.LESSON_COMPETITORS, fixture["instance"])
assert sum(bool(row["warnings"]) for row in old_rotations) == 3
assert all(not row["ambiguous"] and not row["warnings"] and not row["errors"] for row in new_rotations)
record = {
    "schema": "canonical-lesson-rotation-replay-v1",
    "task_id": "9df67b512dad",
    "before_source_sha256": hashlib.sha256(before_bytes).hexdigest(),
    "after_source_sha256": source_sha,
    "rule_source_sha256": rule_source_sha,
    "rule_callable_sha256": rule_callable_sha,
    "replay": {key: fixture[key] for key in ("band", "seed", "sample_index", "query_index")},
    "label_basis": "All five retained labels re-executed using the selected canonical Racket rule.",
    "racket_label_checks": labels,
    "generator_draws_unchanged": len(pairs),
    "before_rotations": old_rotations,
    "after_rotations": new_rotations,
    "passed": True,
}
(base / "retained-witness-replay.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({key: record[key] for key in ("task_id", "before_source_sha256", "after_source_sha256", "rule_source_sha256", "generator_draws_unchanged", "passed")}, indent=2))
