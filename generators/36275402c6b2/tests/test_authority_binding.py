"""Keep the selected rule byte-exact while preserving its archival source."""
import hashlib
import json

from reviewer_support import canonical_path, find_root


def test_selected_authority_is_exact_and_archival_source_is_preserved():
    ledger = canonical_path(find_root(__file__))
    rows = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    canonical = next(row for row in rows if row.get("task_id") == "36275402c6b2")
    authority_path = ledger.parent.parent / "base/solutions/training/e9b4f6fc__36275402c6b2.json"
    authority = json.loads(authority_path.read_text())["racket_target"]
    assert authority["target_code"] == canonical["program_solution"]
    assert hashlib.sha256(authority["raw_code"].encode()).hexdigest() == (
        "42a27cd71ba2484c4d0ee5c232ab41224dee212dffa06ab9efc31c6c4c2fc217"
    )
