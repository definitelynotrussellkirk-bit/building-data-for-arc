"""Native promotion contract for the nearest/farthest marker family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes


TASK_ID = "9971f3a5882c"
ROOT = find_root(__file__)
HERE = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(path: Path, prefix: str):
    source = path.read_bytes()
    name = prefix + hashlib.sha256(str(path).encode() + source).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load(HERE / "prototype.py", "_9971_native_prototype_")


@pytest.fixture(scope="module")
def adapter():
    return _load(HERE / "adapter.py", "_9971_native_adapter_")


def _canonical_program() -> str:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                rows.append(row["program_solution"])
    assert len(set(rows)) == 1
    return rows[0]


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_promotion_contract_declares_native_limits_and_default():
    contract = json.loads((HERE / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"marker_selection": ["nearest", "farthest"]},
        "default": {"marker_selection": "nearest"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [f"generators/{TASK_ID}/workspace/parametric/nearest.rkt"],
    }


def test_default_program_is_exact_canonical_and_alternate_is_distinct(adapter):
    nearest = adapter.program({"marker_selection": "nearest"})
    farthest = adapter.program({"marker_selection": "farthest"})
    assert nearest == _canonical_program()
    assert nearest == (HERE / "nearest.rkt").read_text(encoding="utf-8")
    assert farthest != nearest
    assert hashlib.sha256(farthest.encode()).hexdigest() == hashlib.sha256(
        adapter.program({"marker_selection": "farthest"}).encode()
    ).hexdigest()


@pytest.mark.parametrize("setting", ["nearest", "farthest"])
def test_counts_are_independent_prefix_stable_and_deterministic(adapter, setting):
    settings = {"marker_selection": setting}
    short = adapter.generate(17, settings, 2, 1)
    long = adapter.generate(17, settings, 6, 4)
    replay = adapter.generate(17, settings, 6, 4)
    assert long == replay
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    assert len(long["train"]) == 6
    assert len(long["test"]) == 4
    assert long["program_solution"] == adapter.program(settings)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(long)}) == 10


def test_same_seed_uses_matched_inputs_across_settings(adapter):
    nearest = adapter.generate(91, {"marker_selection": "nearest"}, 3, 4)
    farthest = adapter.generate(91, {"marker_selection": "farthest"}, 3, 4)
    assert _inputs(nearest) == _inputs(farthest)
    assert any(a["output"] != b["output"] for a, b in zip(nearest["train"], farthest["train"]))
    assert any(a["output"] != b["output"] for a, b in zip(nearest["test"], farthest["test"]))


@pytest.mark.parametrize("setting", ["nearest", "farthest"])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_visible_demonstrations_identify_setting_and_declared_shortcuts(
    prototype, adapter, setting, demos
):
    episode = adapter.generate(0, {"marker_selection": setting}, demos, 4)
    certificate = prototype.teaching_certificate(episode)
    assert certificate["setting_survivors"] == [setting]
    assert certificate["plausible_rival_survivors"] == []
    assert certificate["demonstrations_checked"] == demos


def test_four_queries_are_novel_and_include_substantive_30x30_stress(prototype, adapter):
    episode = adapter.generate(123, {"marker_selection": "nearest"}, 3, 4)
    queries = episode["test"]
    assert len({json.dumps(pair["input"], separators=(",", ":")) for pair in queries}) == 4
    stress = queries[-1]
    assert (len(stress["input"]), len(stress["input"][0])) == (30, 30)
    analysis = prototype.native_analysis(stress["input"])
    assert analysis["bbox"][1] - analysis["bbox"][0] + 1 >= 14
    assert analysis["bbox"][3] - analysis["bbox"][2] + 1 >= 16
    assert len(analysis["full_rows"]) >= 5
    assert len(analysis["full_cols"]) >= 5
    changed = [
        (r, c)
        for r, row in enumerate(stress["output"])
        for c, value in enumerate(row)
        if value != stress["input"][r][c]
    ]
    assert len(changed) >= 100
    assert max(r for r, _ in changed) - min(r for r, _ in changed) + 1 >= 20
    assert max(c for _, c in changed) - min(c for _, c in changed) + 1 >= 20


@pytest.mark.parametrize("setting", ["nearest", "farthest"])
def test_claimed_labels_match_independent_python_transform(prototype, adapter, setting):
    episode = adapter.generate(42, {"marker_selection": setting}, 3, 4)
    for split in ("train", "test"):
        for pair in episode[split]:
            assert pair["output"] == prototype.native_transform(
                pair["input"], {"marker_selection": setting}
            )


def test_public_projection_masks_all_query_answers_and_first_turn_is_invariant(adapter):
    one = adapter.generate(17, {"marker_selection": "nearest"}, 3, 1)
    four = adapter.generate(17, {"marker_selection": "nearest"}, 3, 4)
    first_turn = {"train": four["train"], "test": [four["test"][0]]}
    assert public_challenge_bytes(one) == public_challenge_bytes(first_turn)
    visible = json.loads(public_challenge_bytes(four))
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    assert all(set(pair) == {"input"} for pair in visible["test"])
    text = json.dumps(visible, sort_keys=True)
    assert "marker_selection" not in text
    assert "nearest" not in text and "farthest" not in text
    assert "program_solution" not in text


def test_dependency_witness_names_real_intermediate_and_changes_output(prototype):
    witness = prototype.dependency_witness()
    assert witness["settings"] == {"marker_selection": "nearest"}
    assert witness["ablation"] == "wrong_intermediate"
    assert witness["program"] == prototype.program(witness["settings"])
    assert witness["counterfactual_program"] != witness["program"]
    assert witness["output"] == prototype.native_transform(witness["input"], witness["settings"])
    assert witness["counterfactual_output"] != witness["output"]
    assert set(witness["intermediate_value"]) == {"bbox", "markers_by_side", "full_rows", "full_cols"}


@pytest.mark.parametrize(
    "settings,demos,queries,match",
    [
        ({"marker_selection": "middle"}, 3, 4, "marker_selection"),
        ({"marker_selection": "nearest", "extra": 1}, 3, 4, "exactly"),
        ({"marker_selection": "nearest"}, True, 4, "demos"),
        ({"marker_selection": "nearest"}, 1, 4, "demos"),
        ({"marker_selection": "nearest"}, 3, 5, "queries"),
    ],
)
def test_adapter_rejects_invalid_typed_requests(adapter, settings, demos, queries, match):
    with pytest.raises(ValueError, match=match):
        adapter.generate(0, settings, demos, queries)


def test_every_declared_plausible_rival_has_a_distinct_racket_program(prototype):
    programs = prototype.plausible_programs()
    assert set(programs) == {
        "ignore_top_nearest",
        "ignore_top_farthest",
        "unit_expansion",
        "boundaries_only_nearest",
        "boundaries_only_farthest",
        "identity",
    }
    assert len(set(programs.values())) == len(programs)
    assert all(source.startswith("(rule!") for source in programs.values())
