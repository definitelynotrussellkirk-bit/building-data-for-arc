from pathlib import Path
import hashlib
import json

import pytest


@pytest.fixture
def library(tmp_path: Path) -> Path:
    root = tmp_path / "library"
    (root / "catalog").mkdir(parents=True)
    (root / "shared/data/canonical").mkdir(parents=True)
    records, canonical, mappings = [], [], []
    program = "(rule! g)"
    rule_hash = hashlib.sha256(program.encode()).hexdigest()[:12]
    for index, tid in enumerate(("aaaa00000001", "aaaa00000002", "aaaa00000003")):
        home = root / "generators" / tid
        home.mkdir(parents=True)
        code = f"VERSION = '1.0.{index}'\n"
        (home / "generator.py").write_text(code)
        records.append({"id": tid, "kind": "per_puzzle", "summary": f"Mirror {index}",
                        "sources": ["training"] if index < 2 else ["bank:one"], "skills": ["reflection"],
                        "difficulties": ["easy" if index == 0 else "hard"], "primitives": ["flip-lr"],
                        "aliases": ["old-first"] if index == 0 else [], "canonical_rows": 1,
                        "generator": f"generators/{tid}/generator.py", "runtime_generator": f"puzzle_generators/per_puzzle/{tid}/generator.py",
                        "version": f"1.0.{index}", "rule_task_id": tid, "family": "family-one", "split": "train",
                        "parent_ids": [], "train_safety": "unverified" if index == 2 else "reviewed_safe",
                        "mix_weight": 1.0, "semantic_veto": False, "veto_reason": "",
                        "reviewed_generator_sha256": hashlib.sha256(code.encode()).hexdigest(),
                        "reviewed_rule_hash": rule_hash, "review_status": "", "health": "whitelist", "notes_count": 0})
        canonical.append({"task_id": tid, "program_solution": program, "written_solution": "private explanation",
                          "train": [{"input": [[1]], "output": [[2]]}],
                          "test": [{"input": [[3]], "output": [[4]]}]})
        mappings.append({"path": f"generators/{tid}/generator.py", "target": f"puzzle_generators/per_puzzle/{tid}/generator.py"})
    (root / "catalog/puzzles.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    (root / "catalog/runtime_files.json").write_text(json.dumps(mappings))
    (root / "catalog/authority_files.json").write_text("{}")
    (root / "shared/data/canonical/puzzles.jsonl").write_text("".join(json.dumps(r) + "\n" for r in canonical))
    return root
