"""Retain exact mirror differences using existing actual-Racket audit labels.

Run through review.py run. This script never creates a Catalog or invokes Racket.
It preserves the original probe, its source hash, and the actual reference file.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import find_root, load_selected_generator


def main():
    out = Path(__file__).resolve().parent
    probe = json.loads((out / "probe.json").read_text())
    reference = json.loads((out / "reference.json").read_text())
    module, source, source_sha = load_selected_generator("9e80ef661ecc", root=find_root(__file__))
    assert source_sha == probe["source"]["generator_sha256"] == reference["generator_sha256"]
    assert source_sha == "b60ba4b5640da51fde70f6ba8c114942f31c7535ac12b70c55fc68d2cd4fc51d"
    mismatches = []
    for index in probe["summary"]["parity_errors"]:
        record = probe["records"][index]
        actual = reference["results"][index]
        assert record["input"] == actual["input"]
        assert record["output"] == actual["output"]
        mirror = module.rule_mirror(record["input"])
        diffs = [{"row": r, "column": c, "racket": value, "mirror": mirror[r][c]}
                 for r, row in enumerate(record["output"])
                 for c, value in enumerate(row) if value != mirror[r][c]]
        assert diffs
        mismatches.append({"record": index, "name": record["name"],
                           "input_sha256": record["input_sha256"],
                           "input": record["input"], "racket_output": record["output"],
                           "python_mirror_output": mirror, "differences": diffs,
                           "self_check": module.self_check(record["input"]),
                           "strict_canonical_like": module.strict_canonical_like(record["input"]),
                           "public_generator_domain": actual["generator_domain"]})
    extended = next(r for r in probe["rotations"] if r["start"] == 0 and r["query_position"] == 3)
    query = probe["records"][extended["query_record"]]
    extended_witness = {"recipe": extended, "query": query,
                        "demos": [probe["records"][i] for i in extended["demo_records"]],
                        "rival_outputs": {name: module.LESSON_COMPETITORS[name](query["input"])
                                          for name in extended["ambiguous_rivals"]}}
    result = {"schema": "arcpuzzles-cached-audit-analysis-v1", "source": probe["source"],
              "execution": {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
                            "new_catalog_apply_batches": 0, "new_racket_calls": 0},
              "reference_file_sha256": hashlib.sha256((out / "reference.json").read_bytes()).hexdigest(),
              "canonical_catalog_program_sha256": probe["source"]["rule_text_sha256"],
              "public_reference_rendered_rule_sha256": reference["rule_text_sha256"],
              "executed_rule_hash": reference["executed_rule_hash"],
              "mirror_mismatches": mismatches,
              "extended_rotation_witness": extended_witness}
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_sha
    (out / "cached-analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"mismatches": [{"record": r["record"], "differing_cells": len(r["differences"]),
                                      "color_pairs": sorted({(d["racket"], d["mirror"]) for d in r["differences"]}),
                                      "public_domain": r["public_generator_domain"]}
                                     for r in mismatches],
                      "extended_rotation_rivals": extended["ambiguous_rivals"]}, indent=2))


if __name__ == "__main__":
    main()
