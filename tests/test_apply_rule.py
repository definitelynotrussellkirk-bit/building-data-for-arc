"""Supported reference-rule application for hand-made audit inputs."""
import importlib.util
import json
from pathlib import Path
import shutil
import types

import pytest

from arcpuzzles import Catalog, runtime
from arcpuzzles.cli import main


@pytest.mark.parametrize("payload,count", [
    ([[1, 2], [3, 4]], 1),
    ({"input": [[0]]}, 1),
    ({"inputs": [[[0]], [[1, 1]]]}, 2),
    ([[[0]], {"input": [[5]]}], 2),
])
def test_parse_accepts_documented_shapes(payload, count):
    assert len(runtime.parse_apply_inputs(payload)) == count


@pytest.mark.parametrize("payload,message", [
    ([[1, 2], [3]], "ragged"),
    ([[True]], "integers 0..9"),
    ([[1.0]], "integers 0..9"),
    ([[10]], "integers 0..9"),
    ([], "nonempty"),
    ([[]], "1..30 rows"),
    ([[0] * 31], "1..30 cells"),
    ({"input": [[0]], "output": [[0]]}, "exactly one key"),
    ([[[0]]] * (runtime.MAX_APPLY_INPUTS + 1), "at most"),
])
def test_parse_rejects_invalid_grids(payload, message):
    with pytest.raises(ValueError, match=message):
        runtime.parse_apply_inputs(payload)


def _worker():
    path = Path(runtime.__file__).with_name("worker.py")
    spec = importlib.util.spec_from_file_location("apply_worker_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_worker_records_each_input_failure_and_closes_the_bridge(tmp_path, monkeypatch):
    worker = _worker()
    calls = {"shutdown": 0}

    class Bridge:
        def shutdown(self):
            calls["shutdown"] += 1

    def apply_rule(bridge, name, grid):
        if grid == [[9]]:
            raise RuntimeError("racket: car: contract violation")
        return "not a grid" if grid == [[8]] else [[cell + 1 for cell in row] for row in grid]

    bundle = types.SimpleNamespace(rule_task_id="t", rule_file="data/canonical/puzzles.jsonl",
                                   rule_source="(rule! g)", rule_callable_text="(lambda (g) g)")
    runner = types.SimpleNamespace(_open_bridge_with_rule=lambda text: (Bridge(), "__pg_rule"),
                                   _apply_rule=apply_rule, _load_bundle=lambda tid: bundle)
    request = {"task_id": "t", "reference": "archival", "inputs": [[[1]], [[9]], [[8]]]}
    worker._apply(tmp_path, request, runner, lambda g: isinstance(g, list))
    result = json.loads((tmp_path / "applied.json").read_text())
    assert calls["shutdown"] == 2
    assert [r["output"] for r in result["results"]] == [[[2]], None, None]
    assert "contract violation" in result["results"][1]["error"]
    assert "not a rectangular" in result["results"][2]["error"]


def test_apply_recovers_rule_after_a_bridge_dies(tmp_path):
    worker = _worker()
    bridges = []

    class Bridge:
        alive = True

        def shutdown(self):
            self.alive = False

    def open_bridge(text):
        bridge = Bridge()
        bridges.append(bridge)
        return bridge, "__pg_rule"

    def apply(bridge, name, grid):
        if grid == [[9]]:
            bridge.alive = False
            raise RuntimeError("Racket timed out")
        assert bridge.alive, "dead child has lost the named rule"
        return grid

    bundle = types.SimpleNamespace(rule_task_id="t", rule_file="canonical",
                                   rule_source="(rule! g)", rule_callable_text="(lambda (g) g)")
    runner = types.SimpleNamespace(_open_bridge_with_rule=open_bridge, _apply_rule=apply,
                                   _load_bundle=lambda tid: bundle)
    worker._apply(tmp_path, {"task_id": "t", "reference": "archival", "inputs": [[[9]], [[1]]]},
                  runner, lambda grid: isinstance(grid, list))
    results = json.loads((tmp_path / "applied.json").read_text())["results"]
    assert "timed out" in results[0]["error"]
    assert results[1]["output"] == [[1]] and results[1]["error"] is None
    assert len(bridges) == 2 and all(not bridge.alive for bridge in bridges)


def test_archival_reference_requires_explicit_opt_in():
    with pytest.raises(ValueError, match="allow_unapproved"):
        runtime.apply_rule(Catalog(), "6c68e1b008a5", [[[0]]], reference="archival")


def test_cli_refuses_to_overwrite_output(tmp_path):
    grid = tmp_path / "grid.json"
    grid.write_text("[[0]]")
    out = tmp_path / "out.json"
    out.write_text("keep")
    assert main(["apply", "6c68e1b008a5", "--input", str(grid), "--out", str(out)]) == 1
    assert out.read_text() == "keep"


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_apply_reproduces_generated_labels_with_the_canonical_rule():
    catalog = Catalog()
    episode, = catalog.generate("6c68e1b008a5", seed=23, n_train=2, n_test=1)
    pairs = episode["train"] + episode["test"]
    record = catalog.apply("6c68e1b008a5", [pair["input"] for pair in pairs])
    assert record["rule_hash_matches_catalog"]
    assert record["executed_rule_hash"] == episode["executed_rule_hash"]
    assert [r["output"] for r in record["results"]] == [pair["output"] for pair in pairs]
    assert all(r["error"] is None and r["input_sha256"] and r["output_sha256"] for r in record["results"])


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_apply_timeout_is_a_failure_not_an_output():
    with pytest.raises(runtime.ApplyFailure) as caught:
        runtime.apply_rule(Catalog(), "6c68e1b008a5", [[[0]]], timeout=0.05)
    assert caught.value.run["timed_out"]


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_archival_apply_never_inherits_canonical_approval():
    catalog = Catalog()
    row = catalog.describe("6c68e1b008a5")
    episode, = catalog.generate(row["id"], seed=23, n_train=1, n_test=1)
    record = catalog.apply(row["id"], [episode["train"][0]["input"]],
                           reference="archival", allow_unapproved=True)
    assert record["catalog_approved"] == row["approved"]
    assert record["approved"] is False

@pytest.mark.parametrize('behavior,status', [('invalid','invalid'),('error','error'),('missing','not_declared')])
def test_generator_domain_is_independent_of_rule_and_cannot_mutate_input(tmp_path, behavior, status):
    worker = _worker()
    def checker(grid):
        grid[0][0] = 9
        if behavior == 'error': raise RuntimeError('bad checker')
        return ['outside intended domain']
    module = types.SimpleNamespace(self_check=checker) if behavior != 'missing' else types.SimpleNamespace()
    class Bridge:
        def shutdown(self): pass
    bundle = types.SimpleNamespace(generator_module=module, rule_task_id='t', rule_file='canonical',
                                   rule_source='(rule! g)', rule_callable_text='(lambda (g) g)')
    runner = types.SimpleNamespace(_open_bridge_with_rule=lambda text:(Bridge(),'rule'),
                                  _apply_rule=lambda bridge,name,grid:grid, _load_bundle=lambda tid:bundle)
    worker._apply(tmp_path, {'task_id':'t','reference':'archival','inputs':[[[1]]],
                            'check_generator_domain':True}, runner, lambda g:True)
    row = json.loads((tmp_path/'applied.json').read_text())['results'][0]
    assert row['output'] == [[1]]
    assert row['generator_domain']['status'] == status
