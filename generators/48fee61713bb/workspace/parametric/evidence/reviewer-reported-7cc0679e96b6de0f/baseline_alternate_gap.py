"""Failing-before probe: unchanged canonical execution cannot supply alternate stacks."""
import hashlib
import json
from pathlib import Path
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper

root = Path.cwd()
rows = [json.loads(line) for line in (root / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == "48fee61713bb"]
program = rows[0]["program_solution"]
pairs = {}
for row in rows:
    for split in ("train", "test"):
        for pair in row[split]:
            pairs.setdefault(json.dumps(pair["input"]), pair)
failures = []
with RacketBridge() as bridge:
    for index, pair in enumerate(pairs.values()):
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"]) + ")"
        actual = bridge.eval_text(f"({strip_rule_wrapper(strip_line_comments(program))} {literal})")
        desired = [list(reversed(row)) for row in pair["output"]] if len(pair["output"]) == 7 else list(reversed(pair["output"]))
        assert actual == pair["output"], "canonical authority unexpectedly disagrees"
        if actual != desired:
            failures.append({"canonical_input_sha256": hashlib.sha256(json.dumps(pair["input"], separators=(",", ":")).encode()).hexdigest(),
                             "alternate_contract": "short-axis reflected canonical output", "matched": False})
print(json.dumps({"baseline": "unchanged canonical Racket", "alternate_expected_failures": failures}, indent=2))
assert not failures, f"Requested alternate stack placement is absent on {len(failures)} lawful canonical inputs"
