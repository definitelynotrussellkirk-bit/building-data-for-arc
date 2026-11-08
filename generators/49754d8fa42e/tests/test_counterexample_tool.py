"""Task-local tool regressions; correct labels are tested separately via Racket."""
from pathlib import Path
import importlib.util
import json
import pytest

HOME = Path(__file__).resolve().parents[1]


@pytest.fixture
def tool():
    spec = importlib.util.spec_from_file_location("spatial_counterexamples_test", HOME / "workspace/counterexamples.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_emit_keeps_controlled_endpoints_and_both_spatial_endpoint_conditions(tool, tmp_path):
    tool.emit(tmp_path)
    generated = json.loads((tmp_path / "generated.json").read_text())
    examples = generated["examples"]
    assert len(examples) == 4
    assert {e["mode_at_endpoint_count"] for e in examples if e["overrides"]} == {0, 1}
    assert {e["mode_at_endpoint_count"] for e in examples if not e["overrides"]} == {0, 1}
    gen = tool._load()
    for e in examples:
        assert e["input"] == gen.generate(e["seed"], e["sample_index"], difficulty=e["difficulty"], **e["overrides"])
        assert set(e["rival_outputs"]) == set(gen.CANONICAL_SHORTCUTS)
        if not e["overrides"]:
            assert gen.SEMANTIC_WITNESSES["component_size_decoy"](e["input"])
            assert gen.SEMANTIC_WITNESSES["bbox_area_decoy"](e["input"])


def test_emit_refuses_to_overwrite_retained_evidence(tool, tmp_path):
    sentinel = tmp_path / "input.json"
    sentinel.write_text("retain failed attempt")
    with pytest.raises(FileExistsError):
        tool.emit(tmp_path)
    assert sentinel.read_text() == "retain failed attempt"


@pytest.fixture(scope="module")
def executed_witness_bundle(tmp_path_factory):
    """One real public Racket execution, never fabricated reference labels."""
    spec = importlib.util.spec_from_file_location("executed_witness_tool", HOME / "workspace/counterexamples.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    directory = tmp_path_factory.mktemp("executed-spatial-witnesses")
    module.emit(directory)
    from arcpuzzles import Catalog
    inputs = json.loads((directory / "input.json").read_text())
    receipt = Catalog(HOME.parents[1]).apply("49754d8fa42e", inputs, reference="canonical", timeout=120)
    (directory / "racket.json").write_text(json.dumps(receipt))
    return directory


def test_verify_accepts_current_registry_and_real_reference_receipt(tool, executed_witness_bundle, tmp_path):
    import shutil
    directory = tmp_path / "copy"
    shutil.copytree(executed_witness_bundle, directory)
    report = tool.verify(directory)
    assert report["passed"] and report["inputs_verified"] == 4
    assert set(report["rival_refuted_on_input_indices"]) == set(tool._load().CANONICAL_SHORTCUTS)


@pytest.mark.parametrize("corruption", ["source_hash", "reference_error", "invalid_output", "rival_prediction", "rival_registry", "input_file"])
def test_verify_rejects_stale_or_inconsistent_evidence(tool, executed_witness_bundle, tmp_path, corruption):
    import shutil
    directory = tmp_path / "copy"
    shutil.copytree(executed_witness_bundle, directory)
    generated = json.loads((directory / "generated.json").read_text())
    reference = json.loads((directory / "racket.json").read_text())
    if corruption == "source_hash":
        reference["generator_sha256"] = "0" * 64
    elif corruption == "reference_error":
        reference["results"][0]["error"] = "intentional unit-test corruption"
    elif corruption == "invalid_output":
        reference["results"][0]["valid_output"] = False
    elif corruption == "rival_prediction":
        name = next(iter(generated["examples"][0]["rival_outputs"]))
        generated["examples"][0]["rival_outputs"][name] = [[9]]
    elif corruption == "rival_registry":
        generated["examples"][0]["rival_outputs"].popitem()
    elif corruption == "input_file":
        (directory / "input.json").write_text("[]")
    (directory / "generated.json").write_text(json.dumps(generated))
    (directory / "racket.json").write_text(json.dumps(reference))
    with pytest.raises(ValueError):
        tool.verify(directory)
    assert not (directory / "verified.json").exists()
