"""Replay task-owned literal counterexamples with the public Racket API.

From a packet: run_with_racket.py python3
generators/881173b7bc9d/workspace/probe_frame_semantics.py
From an installed checkout: python3 generators/881173b7bc9d/workspace/probe_frame_semantics.py
The exact authority bytes are checked before reference execution.
"""
import hashlib
import json

from arcpuzzles import Catalog
from reviewer_support import find_root


def main():
    root = find_root(__file__)
    path = root / "generators" / "881173b7bc9d" / "counterexamples" / "frame_semantics.json"
    fixture = json.loads(path.read_text())
    authority = fixture["authority"]
    actual_hash = hashlib.sha256((root / authority["path"]).read_bytes()).hexdigest()
    if actual_hash != authority["sha256"]:
        raise RuntimeError("Selected Racket authority differs from the retained fixture authority")
    cases = [dict(c, expected=c["racket_output"]) for c in fixture["witnesses"]]
    cases += [dict(c, expected=c["racket_output"]) for c in fixture["authority_endpoints"]]
    cases += [dict(c, name=f"canonical-v{c['variant']}-{c['split']}-{c['pair_index']}",
                   expected=c["output"]) for c in fixture["canonical"]]
    result = Catalog(root).apply(fixture["task_id"], [case["input"] for case in cases])
    if result["executed_rule_hash"] != authority["executed_rule_hash"]:
        raise RuntimeError("Executed rule identity differs from the retained fixture authority")
    mismatches = []
    for case, row in zip(cases, result["results"], strict=True):
        if row["output"] != case["expected"]:
            mismatches.append({"name":case["name"], "expected":case["expected"],
                               "actual":row["output"]})
    summary = {"task_id":fixture["task_id"], "authority_sha256":actual_hash,
               "executed_rule_hash":result["executed_rule_hash"], "cases":len(cases),
               "matched":len(cases)-len(mismatches), "mismatches":mismatches}
    print(json.dumps(summary, indent=2))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
