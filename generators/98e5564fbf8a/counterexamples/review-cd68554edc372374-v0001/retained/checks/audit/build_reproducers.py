from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "repo"
CANON = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(task_id: str):
    path = ROOT / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


def canonical(task_id: str):
    for line in CANON.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


# 98e: preserve the exact canonical examples rejected by the live self_check.
task_id = "98e5564fbf8a"
module, source = load(task_id)
row = canonical(task_id)
rejections = []
for split in ("train", "test"):
    for index, pair in enumerate(row[split]):
        errors = module.self_check(pair["input"])
        if errors:
            rejections.append({
                "split": split,
                "index": index,
                "errors": errors,
                "input": pair["input"],
            })
out = {
    "schema": "arcpuzzles-audit-reproducer-v1",
    "task_id": task_id,
    "generator_sha256": sha(source),
    "canonical_sha256": sha(CANON),
    "command": ["python3", "checks/audit/build_reproducers.py"],
    "cwd": "WORK",
    "finding": "live self_check rejects canonical inputs",
    "rejection_count": len(rejections),
    "canonical_input_count": len(row["train"]) + len(row["test"]),
    "rejections": rejections,
}
Path("checks/audit/98e5564fbf8a/canonical-selfcheck-rejections.json").write_text(
    json.dumps(out, indent=2) + "\n"
)

# e58: record the source-level absence that strict lint/selfcheck reproduce.
task_id = "e58b545527d3"
module, source = load(task_id)
out = {
    "schema": "arcpuzzles-audit-reproducer-v1",
    "task_id": task_id,
    "generator_sha256": sha(source),
    "command": ["python3", "checks/audit/build_reproducers.py"],
    "cwd": "WORK",
    "finding": "required executable review contracts are absent",
    "has_self_check": callable(getattr(module, "self_check", None)),
    "has_rule_hash": isinstance(getattr(module, "RULE_HASH", None), str),
    "semantic_contract_symbols": {
        name: hasattr(module, name)
        for name in ("strict_canonical_like", "SEMANTIC_WITNESSES", "lesson_identifiable")
    },
    "task_test_files": sorted(
        str(path.relative_to(ROOT))
        for path in (ROOT / "generators" / task_id).rglob("test*.py")
    ),
}
Path("checks/audit/e58b545527d3/missing-contracts.json").write_text(
    json.dumps(out, indent=2) + "\n"
)
