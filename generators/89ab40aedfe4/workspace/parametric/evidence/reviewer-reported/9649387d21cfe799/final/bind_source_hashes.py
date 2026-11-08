#!/usr/bin/env python3
"""Bind the final prototype evidence to production/canonical/source hashes."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from reviewer_support import find_root

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
WORK = ROOT.parent
files = {
    "production_generator": ROOT / "generators/89ab40aedfe4/generator.py",
    "canonical_ledger": ROOT / "shared/data/canonical/puzzles.jsonl",
    "prototype": ROOT / "generators/89ab40aedfe4/workspace/parametric/prototype.py",
    "public_focus": ROOT / "generators/89ab40aedfe4/workspace/parametric/public_focus.py",
    "verifier": ROOT / "generators/89ab40aedfe4/workspace/parametric/verify.py",
    "focused_tests": ROOT / "generators/89ab40aedfe4/tests/test_parametric_legend_selector.py",
}
report = {
    name: {"path": path.relative_to(WORK).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    for name, path in files.items()
}
verification = json.loads((WORK / "checks/parametric-legend-selector/report.json").read_text(encoding="utf-8"))
report["production_generator_matches_assignment"] = (
    report["production_generator"]["sha256"]
    == "2800dab77009ba054309c218507cd1e4a735860dc0f790ade8399d33888deb6b"
)
report["default_program_is_exact_canonical"] = verification["programs"]["all_slots"]["is_exact_canonical"]
if not report["production_generator_matches_assignment"] or not report["default_program_is_exact_canonical"]:
    raise SystemExit("final source binding failed")
(HERE / "source-hashes.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "production_generator_matches_assignment": True,
    "default_program_is_exact_canonical": True,
}, sort_keys=True))
