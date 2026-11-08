"""Prototype-only regressions: executed stencil rules, teaching, and exports."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace/parametric"


def load(name):
    path = PROTOTYPE / (name + ".py")
    assert path.is_file(), "The runnable parametric stencil prototype is missing"
    spec = importlib.util.spec_from_file_location("_test_stencil_" + name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load("prototype")


@pytest.fixture(scope="module")
def engine(prototype):
    with prototype.RacketEngine() as engine:
        yield engine


# Hand-calculated fixture: all eight (A,B,C) occupancy states, plus a zero.
FIXTURE = [
    [0, 0, 0, 8, 0, 0, 2, 8, 0, 6, 0],
    [0, 2, 2, 8, 2, 0, 0, 8, 6, 0, 6],
    [2, 2, 0, 8, 2, 2, 0, 8, 0, 6, 0],
]


def test_forward_and_reverse_execute_hand_derived_labels(prototype, engine):
    assert engine.apply(prototype.program({"direction": "forward"}), FIXTURE) == [
        [0, 6, 6], [6, 0, 0], [0, 6, 0]]
    assert engine.apply(prototype.program({"direction": "reverse"}), FIXTURE) == [
        [0, 6, 0], [0, 6, 6], [0, 6, 0]]


def test_default_is_exact_canonical_program(prototype):
    from reviewer_support import canonical_path, find_root
    root = find_root(HOME)
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()]
    sources = {row["program_solution"] for row in rows if row["task_id"] == "8a851bf5cdd7"}
    assert sources == {prototype.program({"direction": "forward"})}


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_matched_inputs_counts_and_all_query_labels(prototype, engine, demos):
    episodes = [prototype.generate(17, {"direction": d}, demos, 4, engine=engine)
                for d in ("forward", "reverse")]
    for episode in episodes:
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [p["input"] for p in episode["train"] + episode["test"]]
        assert len({json.dumps(g) for g in inputs}) == demos + 4
        assert [len(inputs[-1]), len(inputs[-1][0])] == [30, 29]
        check = prototype.verify_episode(episode, engine=engine)
        assert check["survivors"] == [episode["settings"]["direction"]]
        assert check["fit_scope"] == "demonstrations_only"
        assert len(check["queries"]) == 4
        assert all(row["label_matches"] for row in check["queries"])
        first = inputs[0]
        ph, pw = len(first), (len(first[0]) - 2) // 3
        states = {(bool(first[r][c]), bool(first[r][pw + 1 + c]),
                   bool(first[r][2 * pw + 2 + c])) for r in range(ph) for c in range(pw)}
        assert len(states) == 8
    for split in ("train", "test"):
        assert [p["input"] for p in episodes[0][split]] == [p["input"] for p in episodes[1][split]]
    assert episodes[0]["test"][0]["output"] != episodes[1]["test"][0]["output"]


@pytest.mark.parametrize("field,value", [
    ("demos", 1), ("demos", 7), ("demos", True), ("demos", 3.0),
    ("queries", 0), ("queries", 5), ("queries", "4"), ("seed", -1), ("seed", True),
])
def test_invalid_requests_fail_before_generation(prototype, field, value):
    args = dict(seed=0, settings={"direction": "forward"}, demos=3, queries=4)
    args[field] = value
    with pytest.raises(ValueError):
        prototype.generate(**args)


@pytest.mark.parametrize("settings", [{}, {"direction": "sideways"},
                                        {"direction": "forward", "extra": 1},
                                        {"direction": True}])
def test_unknown_settings_fail(prototype, settings):
    with pytest.raises(ValueError):
        prototype.program(settings)


def test_verifier_rejects_tampered_labels_and_borrowed_certificate(prototype, engine):
    episode = prototype.generate(5, {"direction": "reverse"}, 2, 4, engine=engine)
    bad = deepcopy(episode)
    bad["test"][0]["output"][0][0] = (bad["test"][0]["output"][0][0] + 1) % 10
    with pytest.raises(ValueError, match="label"):
        prototype.verify_episode(bad, engine=engine)
    bad = deepcopy(episode)
    bad["train"] = [{"input": FIXTURE, "output": [[0, 6, 6], [6, 0, 0], [0, 6, 0]]}] * 2
    with pytest.raises(ValueError):
        prototype.verify_episode(bad, engine=engine)


def test_demonstration_checker_cannot_use_query_answers(prototype, engine):
    episode = prototype.generate(11, {"direction": "forward"}, 2, 4, engine=engine)
    certificate = prototype.check_teaching(episode["train"], episode["settings"], engine=engine)
    assert certificate["survivors"] == ["forward"]
    # A legal but uninformative A==B lesson cannot distinguish the two directions.
    grid = deepcopy(FIXTURE)
    for row in grid:
        row[4:7] = row[:3]
    query = [row[8:] for row in grid]
    with pytest.raises(ValueError, match="identify"):
        prototype.check_teaching([{"input": grid, "output": query}], {"direction": "forward"}, engine=engine)


def test_boolean_cell_ragged_and_duplicate_inputs_rejected(prototype, engine):
    episode = prototype.generate(23, {"direction": "forward"}, 2, 1, engine=engine)
    for mutation in ("bool", "ragged", "duplicate", "settings", "program"):
        bad = deepcopy(episode)
        if mutation == "bool": bad["train"][0]["input"][0][0] = True
        elif mutation == "ragged": bad["test"][0]["input"][0].pop()
        elif mutation == "duplicate": bad["test"][0] = deepcopy(bad["train"][0])
        elif mutation == "settings": bad["settings"]["direction"] = "reverse"
        else: bad["program_solution"] = "(rule! g)"
        with pytest.raises(ValueError):
            prototype.verify_episode(bad, engine=engine)


def test_verifier_rejects_forged_private_evidence(prototype, engine, tmp_path):
    export = load("export")
    episode = prototype.generate(101, {"direction": "forward"}, 2, 1, engine=engine)
    for key, value in (("certificate", {"fit_scope": "queries_only", "survivors": ["reverse"]}),
                       ("program_sha256", "0" * 64),
                       ("racket", {"backend": "test", "protected": False}),
                       ("variant_approved", True), ("training_admitted", True)):
        bad = deepcopy(episode)
        bad[key] = value
        with pytest.raises(ValueError):
            prototype.verify_episode(bad, engine=engine)
        with pytest.raises(ValueError):
            export.write_export([bad], tmp_path / key, engine=engine)
        assert not (tmp_path / key).exists()
    # Valid file hashes cannot vouch for a false private admission claim.
    import hashlib
    destination = tmp_path / "rehashed"
    export.write_export([episode], destination, engine=engine)
    manifest = json.loads((destination / "manifest.json").read_text())
    private_name = manifest["episodes"][0]["private"]
    private = json.loads((destination / private_name).read_text())
    private["training_admitted"] = True
    raw = json.dumps(private).encode()
    (destination / private_name).write_bytes(raw)
    manifest["files"][private_name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    (destination / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="training_admitted"):
        export.verify_export(destination, engine=engine)


def test_public_projection_hides_private_data_and_preserves_first_turn(prototype, engine, tmp_path):
    export = load("export")
    one = prototype.generate(31, {"direction": "reverse"}, 3, 1, engine=engine)
    four = prototype.generate(31, {"direction": "reverse"}, 3, 4, engine=engine)
    assert export.turn_bytes(one, 0) == export.turn_bytes(four, 0)
    visible = json.loads(export.turn_bytes(four, 0))
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}
    bad_private = deepcopy(four)
    bad_private["seed"] = 999
    bad_private["settings"] = {"direction": "forward"}
    bad_private["test"][0]["output"][0][0] = 9
    assert export.turn_bytes(bad_private, 0) == export.turn_bytes(four, 0)
    destination = tmp_path / "bundle"
    export.write_export([four], destination, engine=engine)
    assert export.verify_export(destination, engine=engine)["episodes"] == 1
    public = list((destination / "public").glob("*.json"))
    assert len(public) == 4
    import hashlib
    for path in public:
        assert path.stem == hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        export.write_export([four], destination, engine=engine)
    # Rehashing a leaked public object must still fail schema/projection validation.
    target = public[0]
    value = json.loads(target.read_text())
    value["settings"] = four["settings"]
    raw = json.dumps(value).encode()
    new_target = target.with_name(hashlib.sha256(raw).hexdigest() + ".json")
    new_target.write_bytes(raw)
    target.unlink()
    manifest = json.loads((destination / "manifest.json").read_text())
    old_name = target.relative_to(destination).as_posix()
    new_name = new_target.relative_to(destination).as_posix()
    del manifest["files"][old_name]
    manifest["files"][new_name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    for record in manifest["episodes"]:
        record["turns"] = [new_name if name == old_name else name for name in record["turns"]]
    (destination / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        export.verify_export(destination, engine=engine)
