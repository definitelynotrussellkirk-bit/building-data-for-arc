"""Source-bound count defaults and actual materialized lesson verdicts."""
from copy import deepcopy
import hashlib
import json
import shutil
from types import SimpleNamespace

import pytest

from arcpuzzles import Catalog, cli, datasets, runtime
from arcpuzzles.worker import lesson_check


def staged(tmp_path, minimum=None, name="gen"):
    source = ("# no import is needed\n" if minimum is None else f"EXAMPLES_NEEDED = {minimum!r}\n")
    path = tmp_path / f"{name}.py"
    path.write_text(source)
    return {"id": name, "runtime_generator": path.name,
            "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "kind": "per_puzzle", "approved": False, "approval_reasons": [],
            "has_generator": True, "rule_hash": "r", "family": None, "split": None,
            "train_safety": "unverified", "mix_weight": 1}


@pytest.mark.parametrize("minimum,generate_count,export_count", [(None, 3, 4), (1, 3, 4), (6, 6, 6)])
def test_omitted_count_uses_bound_literal_and_historical_floor(tmp_path, minimum, generate_count, export_count):
    row = staged(tmp_path, minimum)
    assert runtime.demonstration_policy(tmp_path, row, None)["resolved_n_train"] == generate_count
    assert runtime.demonstration_policy(tmp_path, row, None, default_floor=4)["resolved_n_train"] == export_count
    assert runtime.demonstration_policy(tmp_path, row, 2)["resolved_n_train"] == 2
    (tmp_path / row["runtime_generator"]).write_text("EXAMPLES_NEEDED = 32\n")
    with pytest.raises(RuntimeError, match="snapshot"):
        runtime.demonstration_policy(tmp_path, row, None)


@pytest.mark.parametrize("declaration", [True, 0, 33, "six"])
def test_invalid_minimum_is_visible(tmp_path, declaration):
    with pytest.raises(ValueError, match="literal integer"):
        runtime.demonstration_policy(tmp_path, staged(tmp_path, declaration), None)


def test_materialized_hook_checks_every_query_and_explicit_short_count_is_diagnostic():
    lesson = {"train": [{"input": [[1]], "output": [[2]]}],
              "test": [{"input": [[3]], "output": [[4]]}, {"input": [[5]], "output": [[6]]}]}
    seen = []
    def hook(demos, query):
        seen.append(deepcopy(query))
        return [] if query["input"] == [[3]] else ["unsupported query"]
    module = SimpleNamespace(lesson_identifiable=hook)
    request = {"demonstration_policy": {"automatic": False, "declared_minimum": 6}}
    verdict = lesson_check(module, lesson, request)
    assert verdict["status"] == "diagnostic_unsupported" and seen == lesson["test"]
    assert "below declared minimum" in verdict["reasons"][0]
    request["demonstration_policy"]["automatic"] = True
    with pytest.raises(ValueError, match="Automatic lesson unsupported"):
        lesson_check(module, lesson, request)


@pytest.mark.parametrize("defect", ["mutation", "malformed", "exception"])
def test_hook_errors_are_diagnostic_and_do_not_change_verified_pairs(defect):
    episode = {"train": [{"input": [[1]], "output": [[2]]}], "test": [{"input": [[3]], "output": [[4]]}]}
    before = deepcopy(episode)
    def hook(demos, query):
        if defect == "mutation":
            demos[0]["output"] = [[9]]
            return []
        if defect == "exception":
            raise RuntimeError("fixture refusal")
        return False
    verdict = lesson_check(SimpleNamespace(lesson_identifiable=hook), episode, {})
    assert verdict["status"] == "diagnostic_unsupported" and episode == before


def test_cli_omission_and_explicit_counts_are_distinct():
    assert cli.parser().parse_args(["generate", "t"]).train is None
    assert cli.parser().parse_args(["generate", "t", "--train", "2"]).train == 2
    assert cli.parser().parse_args(["export", "--count", "1", "--out", "out"]).train is None


@pytest.mark.parametrize("invalid_declaration", [None, "0", "len(SCHEDULE_PROFILES)"])
def test_mixed_export_resolves_per_generator_and_binds_lineage(tmp_path, monkeypatch, invalid_declaration):
    source = tmp_path / "sources"
    source.mkdir()
    rows = [staged(source, 1, "low"), staged(source, 6, "high")]
    good_rows = list(rows)
    if invalid_declaration is not None:
        bad = staged(source, name="bad")
        path = source / bad["runtime_generator"]
        path.write_text(f"EXAMPLES_NEEDED = {invalid_declaration}\n")
        bad["generator_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.insert(0, bad)
    class FakeCatalog:
        def query(self, **kwargs): return rows
        def resolve(self, tid): return tid
        def lineage(self, tid): return {"verified": False, "reasons": ["fixture"]}
    def prepare(catalog, stage, **kwargs):
        for row in rows:
            shutil.copyfile(source / row["runtime_generator"], stage / row["runtime_generator"])
        (stage / "data/canonical").mkdir(parents=True)
        (stage / "data/canonical/puzzles.jsonl").write_text("")
        return {}
    selected = iter(rows)
    class FixedDraws(datasets.random.Random):
        def choices(self, *args, **kwargs): return [next(selected)]
    monkeypatch.setattr(datasets, "random", SimpleNamespace(Random=FixedDraws))
    monkeypatch.setattr(datasets, "prepare_runtime", prepare)
    def generate(stage, row, **kwargs):
        policy = runtime.demonstration_policy(stage, row, kwargs["n_train"], default_floor=kwargs["default_n_train"])
        count = policy["resolved_n_train"]
        episode = {"task_id": row["id"], "seed": kwargs["seed"], "rejections": [],
                   "train": [{"input": [[i % 10]], "output": [[(i + 1) % 10]]} for i in range(count)],
                   "test": [{"input": [[0]], "output": [[1]]}], "executed_rule_hash": "r",
                   "lesson_check": {"status": "not_declared"}}
        runtime._attach_provenance([episode], row, None, {}, "canonical", policy)
        return [episode]
    monkeypatch.setattr(datasets, "generate_in_runtime", generate)
    def render(command, stage, **kwargs):
        request = json.loads((stage / "export_request.json").read_text())
        assert request["n_train"] == len(request["episode"]["train"])
        (stage / "export_result.json").write_text(json.dumps({"diagnostics": {}, "rows": []}))
        return {"timed_out": False, "exit_code": 0}
    monkeypatch.setattr(datasets, "run_process", render)
    output = tmp_path / "export"
    manifest = datasets.export_dataset(FakeCatalog(), output, count=2)
    assert manifest["status"] == "complete"
    failures = [json.loads(line) for line in (output / "rejections.jsonl").read_text().splitlines()]
    if invalid_declaration is not None:
        assert manifest["attempted_episodes"] == 3
        assert len(failures) == 1 and failures[0]["task_id"] == "bad"
        assert "EXAMPLES_NEEDED" in failures[0]["reason"]
        runtime_receipt = json.loads((output / "runtime.private.json").read_text())
        assert "bad" in runtime_receipt["demonstration_policy_errors"]
        assert "bad" not in runtime_receipt["demonstration_policies"]
    else:
        assert manifest["attempted_episodes"] == 2 and failures == []
    lineage = [json.loads(line) for line in (output / "lineage.private.jsonl").read_text().splitlines()]
    assert [row["demonstration_policy"]["resolved_n_train"] for row in lineage] == [4, 6]
    assert [row["task_id"] for row in lineage] == [row["id"] for row in good_rows]
    assert all(row["demonstration_policy"]["requested_n_train"] is None for row in lineage)
    assert all(row["lesson_check"]["status"] == "not_declared" for row in lineage)
    assert datasets.verify_dataset(output) == manifest
    for field, replacement in (("demonstration_policy", {"resolved_n_train": 1}),
                               ("lesson_check", {"status": "passed_declared_hook"})):
        tampered = {**lineage[0], field: replacement}
        labels = json.loads((output / "labels.private.jsonl").read_text().splitlines()[0])
        with pytest.raises(ValueError, match="binding differs"):
            datasets._verify_lineage_row(tampered, labels["episode_id"], labels["task_id"], labels["provenance"])
    # A selected default above the native limit must fail before generation.
    rows[:] = [staged(source, 11, "large")]
    monkeypatch.setattr(datasets.importlib.util, "find_spec", lambda name: True)
    with pytest.raises(ValueError, match="resolved demonstrations"):
        datasets.export_dataset(FakeCatalog(), tmp_path / "native", count=1, style="native", tensors="native")


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_actual_v4_default_racket_lesson_and_explicit_diagnostic(tmp_path):
    catalog = Catalog()
    episode, = catalog.generate("40e85135fbf8", seed=17)
    assert episode["generator_version"] == "4.0.0" and len(episode["train"]) == 6
    policy = episode["provenance"]["demonstration_policy"]
    assert policy["requested_n_train"] is None and policy["declared_minimum"] == 6
    assert episode["lesson_check"]["status"] == "passed_declared_hook"
    short, = catalog.generate("40e85135fbf8", seed=17, n_train=3)
    assert len(short["train"]) == 3 and short["lesson_check"]["status"] == "diagnostic_unsupported"
