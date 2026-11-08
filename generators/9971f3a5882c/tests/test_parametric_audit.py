from __future__ import annotations

import importlib.util
import json
from pathlib import Path


TASK = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK / "workspace" / "parametric"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_audit_runner_emits_replayable_masked_evidence(tmp_path):
    native = load("native_for_audit_test", PARAMETRIC / "native.py")
    audit = load("audit_under_test", PARAMETRIC / "audit.py")
    witness = native.dependency_witness()

    by_program = {
        native.program({"marker_selection": setting}):
            (lambda grid, setting=setting: native.native_transform(
                grid, {"marker_selection": setting}
            ))
        for setting in native.SETTINGS
    }
    by_program.update({
        text: (lambda grid, name=name: native.rival_transform(grid, name))
        for name, text in native.plausible_programs().items()
    })
    by_program[native.wrong_intermediate_program()] = (
        lambda grid: witness["counterfactual_output"]
        if grid == witness["input"]
        else (_ for _ in ()).throw(AssertionError("unexpected counterfactual grid"))
    )

    def apply(program, grid):
        return by_program[program](grid)

    summary = audit.run_audit(
        tmp_path,
        seeds=(0,),
        demo_counts=(2, 6),
        queries=4,
        apply_program=apply,
        runtime_identity={"backend": "test", "protected": False},
    )

    assert summary["status"] == "pass"
    assert summary["jobs"] == 4
    assert summary["failures"] == []
    assert summary["thirty_by_thirty_queries"] == 4
    assert summary["causal_witness"]["outputs_differ"] is True
    assert (tmp_path / "summary.json").is_file()
    case = json.loads((tmp_path / "audited-case.json").read_text())
    assert case["settings"] == {"marker_selection": "nearest"}
    assert case["output"] != case["counterfactual_output"]

    public_files = sorted((tmp_path / "public").glob("*.json"))
    assert len(public_files) == 2
    for path in public_files:
        payload = json.loads(path.read_text())
        assert all("output" in pair for pair in payload["train"])
        assert all(set(pair) == {"input"} for pair in payload["test"])
        raw = path.read_text()
        assert "program_solution" not in raw
        assert "marker_selection" not in raw
