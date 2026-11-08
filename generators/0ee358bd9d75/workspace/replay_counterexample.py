"""Execute the retained 8x8 shortcut witness through canonical Racket."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import find_root, load_selected_generator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New evidence JSON path")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out already exists; preserve the old receipt and choose a new path")
    root = find_root(__file__)
    task = "0ee358bd9d75"
    fixture = root / "generators" / task / "counterexamples/first_nonzero_8x8.json"
    case = json.loads(fixture.read_text())
    generator, _, source_hash = load_selected_generator(task, root=root)
    assert generator.self_check(case["input"]) == []
    assert generator.rival_first_nonzero(case["input"]) == case["first_nonzero_rival_output"]
    assert case["first_nonzero_rival_output"] != case["expected_output"]
    result = Catalog(root).apply(task, [case["input"]], allow_unapproved=True,
                                 check_generator_domain=True)
    assert result["generator_sha256"] == source_hash
    assert result["executed_rule_hash"] == case["canonical_rule_hash"]
    assert result["results"][0]["output"] == case["expected_output"]
    result["fixture_sha256"] = hashlib.sha256(fixture.read_bytes()).hexdigest()
    result["rival_output"] = case["first_nonzero_rival_output"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"status": "reference_confirmed", "generator_sha256": source_hash,
                      "expected": case["expected_output"], "rival": result["rival_output"]}))


if __name__ == "__main__":
    main()
