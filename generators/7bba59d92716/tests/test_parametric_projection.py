"""One-query export boundaries; native guard fixtures do not claim Racket replay."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
SOURCE = Path(__file__).resolve().parents[1] / "workspace/parametric/export_qualified.py"


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


@pytest.fixture
def exporter():
    if not SOURCE.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_main_query_projection", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode(seed=0, alternate=False, demos=3, queries=4):
    pairs = [{"input": [[i, seed]], "output": [[seed, i]] if alternate else [[i, seed]]}
             for i in range(demos + queries)]
    program = "(rule! (flip-lr g))" if alternate else "(rule! g)"
    return dict(task_id="projection_fixture", seed=seed, settings={"flip": alternate},
                train=pairs[:demos], test=pairs[demos:], program=program,
                program_sha256=sha(program.encode()))


@pytest.fixture
def qualified(tmp_path):
    """Use real native source/digest guards on explicitly synthetic test receipts."""
    from arcpuzzles import Catalog
    from arcpuzzles import parametric_promotion as native
    root = tmp_path / "fixture"
    home = root / "generators/projection_fixture/workspace/parametric"
    home.mkdir(parents=True)
    code = b"# Synthetic source-binding fixture, never a Racket qualification.\n"
    (home / "adapter.py").write_bytes(code)
    generator = home.parents[1] / "generator.py"
    generator.write_bytes(code)
    program = "(rule! g)"
    contract = dict(schema=native.CONTRACT,
                    adapter="generators/projection_fixture/workspace/parametric/adapter.py",
                    parameters={"flip": [False, True]}, default={"flip": False},
                    limits={"demos": [2, 6], "queries": [1, 4]})
    (home / "promotion.json").write_bytes(raw(contract))
    (root / "catalog").mkdir()
    (root / "catalog/puzzles.jsonl").write_bytes(raw(dict(
        id="projection_fixture", generator="generators/projection_fixture/generator.py",
        train_safety="reviewed_safe", mix_weight=1, reviewed_generator_sha256=sha(code),
        reviewed_rule_hash=sha(program.encode())[:12])))
    (root / "shared/data/canonical").mkdir(parents=True)
    (root / "shared/data/canonical/puzzles.jsonl").write_bytes(
        raw(dict(task_id="projection_fixture", program_solution=program)))
    (home / "evidence").mkdir()
    (home / "evidence/manifest.json").write_bytes(raw(dict(
        task_id="projection_fixture", generator_sha256=sha(code),
        canonical_rule_hash=sha(program.encode())[:12], verification_status="reviewer_reported",
        files=[dict(path=(home / "adapter.py").relative_to(root).as_posix(), sha256=sha(code))])))
    _, binding = native._ready(Catalog(root), "projection_fixture")
    episodes = [episode(seed, alternate) for alternate in (False, True) for seed in (1, 2)]
    jobs = [dict(seed=e["seed"], settings=e["settings"], demos=3, queries=4) for e in episodes]
    execution = dict(episodes=episodes,
                     checks=[dict(survivors=[e["settings"]], label_count=7) for e in episodes],
                     racket={"backend": "racket", "protected": True}, racket_evaluations=28)
    folder = tmp_path / "qualification"
    folder.mkdir()
    (folder / "execution.json").write_bytes(raw(execution))
    q = dict(schema=native.QUALIFICATION, status="qualified", task_id="projection_fixture",
             source_binding=binding, contract=contract, jobs=jobs,
             programs={raw(e["settings"]).decode().strip(): e["program_sha256"] for e in episodes},
             execution={"path": "execution.json", "sha256": sha(raw(execution))},
             training_admitted=False)
    path = folder / "qualification.json"
    path.write_bytes(raw(q))
    return root, path


def test_first_turn_is_single_query_and_private_future_invariant(exporter):
    assert exporter is not None, "The task-local qualified projection exporter is missing"
    original = episode()
    first = exporter.query_views(original)[0]
    expected = (b'{"test":[{"input":[[3,0]]}],"train":[{"input":[[0,0]],"output":[[0,0]]},'
                b'{"input":[[1,0]],"output":[[1,0]]},{"input":[[2,0]],"output":[[2,0]]}]}\n')
    assert first == (sha(expected), expected)
    single = deepcopy(original)
    single["test"] = single["test"][:1]
    assert exporter.query_views(single)[0] == first
    hidden = deepcopy(original)
    hidden.update(seed=99, settings={"unseen": "secret"}, program="private-code", planned_turns=99)
    for pair in hidden["test"]:
        pair["output"] = [[8]]
    hidden["test"][1:]=[{"input": [[9, i]], "output": [[8]]} for i in (6, 7, 8)]
    assert exporter.query_views(hidden)[0] == first
    assert original == episode(), "Projection must not mutate its caller"


@pytest.mark.parametrize("demos,queries", [(2, 1), (6, 4)])
def test_supported_count_boundaries(exporter, demos, queries):
    views = exporter.query_views(episode(demos=demos, queries=queries))
    assert len(views) == queries
    assert all(len(json.loads(payload)["train"]) == demos for _, payload in views)
    assert all(len(json.loads(payload)["test"]) == 1 for _, payload in views)


@pytest.mark.parametrize("change", ["few_demos", "many_demos", "zero_queries", "many_queries",
                                    "duplicate_input", "bool_color", "ragged", "bad_answer"])
def test_invalid_episode_is_rejected(exporter, change):
    value = episode()
    if change == "few_demos": value["train"] = value["train"][:1]
    elif change == "many_demos": value["train"] *= 3
    elif change == "zero_queries": value["test"] = []
    elif change == "many_queries": value["test"] *= 2
    elif change == "duplicate_input": value["test"][0]["input"] = value["train"][0]["input"]
    elif change == "bool_color": value["test"][0]["input"] = [[True]]
    elif change == "ragged": value["train"][0]["input"] = [[1, 2], [3]]
    else: value["test"][0]["output"] = [[10]]
    with pytest.raises(ValueError):
        exporter.query_views(value)


def test_export_keeps_order_and_answers_only_in_private_manifest(exporter, qualified, tmp_path):
    root, path = qualified
    out = tmp_path / "projection"
    report = exporter.export_qualified(path, out, root=root)
    files = sorted((out / "public").glob("*.json"))
    assert len(files) == report["public_files"] == 16
    assert sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()) == [
        "private/manifest.json", *["public/" + p.name for p in files]]
    for p in files:
        value = json.loads(p.read_bytes())
        assert p.stem == sha(p.read_bytes())
        assert set(value) == {"train", "test"}
        assert len(value["test"]) == 1 and set(value["test"][0]) == {"input"}
    manifest = json.loads((out / "private/manifest.json").read_bytes())
    assert manifest["qualification_sha256"] == sha(path.read_bytes())
    assert manifest["source_binding"] == json.loads(path.read_bytes())["source_binding"]
    assert manifest["owner_acceptance"] == "pending" and manifest["training_admitted"] is False
    for record, source in zip(manifest["episodes"], json.loads(path.with_name("execution.json").read_bytes())["episodes"]):
        assert record["episode"] == source
        for identifier, pair in zip(record["public_ids"], source["test"]):
            assert json.loads((out / "public" / (identifier + ".json")).read_bytes())["test"] == [{"input": pair["input"]}]
    with pytest.raises(FileExistsError):
        exporter.export_qualified(path, out, root=root)


@pytest.mark.parametrize("change", ["execution_bytes", "source", "unprotected", "foreign_binding", "program_hash", "duplicates"])
def test_native_guards_reject_before_publication(exporter, qualified, tmp_path, change):
    root, path = qualified
    execution_path = path.with_name("execution.json")
    q = json.loads(path.read_bytes())
    data = json.loads(execution_path.read_bytes())
    if change == "execution_bytes": execution_path.write_bytes(execution_path.read_bytes() + b" ")
    elif change == "source":
        (root / "generators/projection_fixture/workspace/parametric/adapter.py").write_text("# changed\n")
    elif change == "foreign_binding":
        q["source_binding"]["generator_sha256"] = "0" * 64
        path.write_bytes(raw(q))
    else:
        if change == "unprotected": data["racket"]["protected"] = False
        elif change == "program_hash": data["episodes"][0]["program_sha256"] = "0" * 64
        else:
            data["episodes"].append(deepcopy(data["episodes"][0]))
            data["checks"].append(deepcopy(data["checks"][0]))
            data["racket_evaluations"] += 7
            q["jobs"].append(deepcopy(q["jobs"][0]))
        execution_path.write_bytes(raw(data))
        q["execution"]["sha256"] = sha(raw(data))
        path.write_bytes(raw(q))
    out = tmp_path / "rejected"
    with pytest.raises(ValueError):
        exporter.export_qualified(path, out, root=root)
    assert not out.exists()
