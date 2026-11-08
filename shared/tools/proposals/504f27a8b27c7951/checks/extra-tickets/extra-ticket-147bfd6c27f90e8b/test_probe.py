from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_probe():
    path = HERE / "probe.py"
    spec = importlib.util.spec_from_file_location("extra_2359_probe", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_lower_half_witness_refutes_top_half_shortcut() -> None:
    result = load_probe().build_result()
    assert result["ticket_id"] == "extra-ticket-147bfd6c27f90e8b"
    assert result["task_id"] == "2359fcadf037"
    assert result["generator_sha256"] == (
        "c39c1581114dab28df27a7529c31d6f962d87d147a0851bd9622b603fc357e4b"
    )
    assert result["normalized_rule_hash"] == "e7d1bc8a4d75"
    assert result["canonical_pairs"]["count"] == 3
    assert result["canonical_pairs"]["shortcut_matches_every_pair"] is True
    witness = result["generated_witness"]
    assert witness["seed"] == 3466568204717384385
    assert witness["sample_index"] == 0
    assert witness["difficulty"] is None
    assert witness["self_check_errors"] == []
    assert witness["lower_half_active_spans"] == [
        {"column": 3, "top": 6, "bottom": 8},
        {"column": 6, "top": 8, "bottom": 10},
        {"column": 7, "top": 8, "bottom": 10},
    ]
    assert witness["canonical_racket_equals_shortcut_racket"] is False
    assert witness["mismatch_cells"] == [[7, 3], [9, 6], [9, 7]]
    assert result["bounded_result"] == "lawful_generated_witness_refutes_shortcut"
