"""Focused proposed-prototype checks; these do not approve canonical generation."""
import importlib.util
from functools import cache
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "12ace26107fd"
ROOT = find_root(__file__)
_, SELECTED_SOURCE, _ = load_selected_generator(TASK_ID, root=ROOT)
MANIFEST = ROOT / "RUNTIME_MANIFEST.json"
if MANIFEST.is_file():
    identity = f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    entries = [entry for entry in json.loads(MANIFEST.read_text())["files"]
               if entry["library_path"] == identity]
    # Prefer the mapped execution copy over any library-layout mirror.
    entries.sort(key=lambda entry: entry["runtime_path"] == identity)
    assert entries, "runtime manifest must retain the prototype workspace"
    PROTOTYPE = ROOT / entries[0]["runtime_path"]
else:
    PROTOTYPE = SELECTED_SOURCE.parent / "workspace/parametric/prototype.py"


@cache
def load_prototype():
    assert PROTOTYPE.exists(), "episode-level output-order prototype is not implemented"
    spec = importlib.util.spec_from_file_location("layer_parametric_prototype", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_is_exact_canonical_program_and_bad_order_is_rejected():
    p = load_prototype()
    assert p.program_for() == p.canonical_record()["program_solution"]
    assert p.program_for("inner_to_outer") != p.program_for()
    with pytest.raises(ValueError, match="output_order"):
        p.program_for("random")


def test_shared_lawful_input_changes_executed_racket_output():
    p = load_prototype()
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge() as bridge:
        witness = p.shared_input()
        assert p.execute(bridge, p.program_for(), witness) == [[8, 4, 1]]
        assert p.execute(bridge, p.program_for("inner_to_outer"), witness) == [[1, 4, 8]]


def test_default_matches_all_canonical_examples_through_racket():
    p = load_prototype()
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge() as bridge:
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            assert p.execute(bridge, p.program_for(), pair["input"]) == pair["output"]


def test_mapped_source_lookup_uses_manifest_not_library_parent_guesses(tmp_path):
    p = load_prototype()
    identity = f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    mapped = tmp_path / "task_workspaces" / TASK_ID / "parametric/prototype.py"
    mapped.parent.mkdir(parents=True)
    mapped.write_text("mapped prototype source")
    (tmp_path / "RUNTIME_MANIFEST.json").write_text(json.dumps({"files": [
        {"library_path": identity, "runtime_path": str(mapped.relative_to(tmp_path))}
    ]}))
    assert p.resolve_source(identity, root=tmp_path) == mapped
    with pytest.raises(FileNotFoundError):
        p.resolve_source("shared/runtime/missing.py", root=tmp_path)


@pytest.mark.parametrize("seed,order", [(1, "outer_to_inner"), (0, "inner_to_outer")])
def test_episode_is_deterministic_private_and_distinguishes_parameter(seed, order):
    p = load_prototype()
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge() as bridge:
        public, private = p.generate_episode(seed, bridge)
        public_again, private_again = p.generate_episode(seed, bridge)
        assert public == public_again
        assert private == private_again
        assert private["parameter"] == {"output_order": order}
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 2
        assert len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert private["rival_checks"][order]["matches_all_demonstrations"]
        rival = next(value for value in p.ORDERS if value != order)
        assert not private["rival_checks"][rival]["matches_all_demonstrations"]
        assert private["rival_checks"][rival]["distinguishing_demo_indices"] == [0, 1]
        assert len(private["query_answers"]) == len(public["test"])
        for pair in public["train"]:
            assert p.execute(bridge, private["program"], pair["input"]) == pair["output"]
        assert p.execute(bridge, private["program"], public["test"][0]["input"]) == private["query_answers"][0]
        assert all(0 <= value <= 9 for pair in public["train"] for row in pair["output"] for value in row)


def test_materialization_keeps_rules_and_answers_out_of_public_files(tmp_path):
    p = load_prototype()
    manifest = p.write_evidence(tmp_path, seeds=[0, 1])
    assert manifest["status"] == "proposed prototype; not production-approved"
    assert len(list((tmp_path / "rules").glob("*.rkt"))) == 2
    assert len(list((tmp_path / "public").glob("*.json"))) == 2
    for path in (tmp_path / "public").glob("*.json"):
        public = json.loads(path.read_text())
        assert set(public) == {"train", "test"}
        assert set(public["test"][0]) == {"input"}
    for order in p.ORDERS:
        code = (tmp_path / "rules" / (order + ".rkt")).read_text()
        assert code == p.program_for(order)
        assert p.digest(code.encode()) == manifest["program_sha256"][order]
