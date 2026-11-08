"""Source-bound tests for the aad4e3a1d5e3 parametric authoring family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
ADAPTER_PATH = HOME / "workspace/parametric/adapter.py"


def adapter():
    spec = importlib.util.spec_from_file_location("_aad4e3a1d5e3_parametric_test", ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def literal_input() -> list[list[int]]:
    h, w, row_axis, col_axis = 11, 13, 5, 6
    grid = [[0] * w for _ in range(h)]
    for c in range(w):
        grid[row_axis][c] = 6
    for r in range(h):
        grid[r][col_axis] = 5
    grid[row_axis][col_axis] = 5
    for r, c, value in (
        (1, 1, 2),
        (1, 2, 3),
        (2, 1, 3),
        (2, 2, 2),
        (3, 1, 2),
        (3, 2, 3),
    ):
        grid[r][c] = value
    return grid


def literal_expected(*, include_horizontal_copy: bool) -> list[list[int]]:
    source = literal_input()
    out = [row[:] for row in source]
    row_axis, col_axis = 5, 6
    motif = [
        (r, c, value)
        for r, row in enumerate(source)
        for c, value in enumerate(row)
        if value not in (0, 5, 6)
    ]
    for r, c, value in motif:
        out[r][2 * col_axis - c] = value
        out[2 * row_axis - r][2 * col_axis - c] = value
        if include_horizontal_copy:
            out[2 * row_axis - r][c] = value
    return out


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge(timeout=10) as bridge:
        assert bridge.runtime_identity["protected"] is True

        def apply(program: str, grid: list[list[int]]) -> list[list[int]]:
            bridge.define_grid("aad-parametric-test-grid", grid)
            return bridge.eval_text(f"({wrap_rule(program)} aad-parametric-test-grid)")

        yield apply


def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if (row := json.loads(line))["task_id"] == "aad4e3a1d5e3"
    }
    assert len(programs) == 1
    return programs.pop()


def inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def public_projection(episode: dict) -> dict:
    return {
        "train": episode["train"],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def test_default_is_exact_canonical_program_and_alternative_is_distinct():
    module = adapter()
    default = module.program({"mode": "complete_orbit"})
    alternate = module.program({"mode": "chain_only"})
    assert default == canonical_program()
    assert alternate != default
    assert hashlib.sha256(default.encode()).hexdigest() != hashlib.sha256(alternate.encode()).hexdigest()


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("complete_orbit", literal_expected(include_horizontal_copy=True)),
        ("chain_only", literal_expected(include_horizontal_copy=False)),
    ],
)
def test_literal_labels_match_independent_expected_and_protected_racket(racket, mode, expected):
    module = adapter()
    grid = literal_input()
    assert module.transform(grid, mode) == expected
    assert racket(module.program({"mode": mode}), grid) == expected


def test_chain_only_consumes_vertical_pass_created_cells():
    module = adapter()
    explanation = module.explain_chain(literal_input())
    original = {
        (r, c, value)
        for r, row in enumerate(literal_input())
        for c, value in enumerate(row)
        if value not in (0, 5, 6)
    }
    created = {tuple(cell) for cell in explanation["created_by_vertical_pass"]}
    assert created
    assert created.isdisjoint(original)
    assert explanation["vertical_pass"] != literal_input()
    assert explanation["final"] == literal_expected(include_horizontal_copy=False)
    assert explanation["skip_vertical_then_horizontal"] != explanation["final"]


@pytest.mark.parametrize("mode", ["complete_orbit", "chain_only"])
def test_generated_inputs_are_setting_neutral_deterministic_and_count_independent(mode):
    module = adapter()
    before = random.getstate()
    selected = module.generate(17, {"mode": mode}, 2, 4)
    other_mode = "chain_only" if mode == "complete_orbit" else "complete_orbit"
    other = module.generate(17, {"mode": other_mode}, 2, 4)
    one_query = module.generate(17, {"mode": mode}, 2, 1)
    six_demo = module.generate(17, {"mode": mode}, 6, 4)

    assert inputs(selected) == inputs(other)
    assert selected == module.generate(17, {"mode": mode}, 2, 4)
    assert random.getstate() == before
    assert len(selected["train"]) == 2 and len(selected["test"]) == 4
    assert len(six_demo["train"]) == 6 and len(six_demo["test"]) == 4
    assert selected["train"] == six_demo["train"][:2]
    assert [pair["input"] for pair in selected["test"]] == [pair["input"] for pair in six_demo["test"]]
    assert selected["train"] == one_query["train"]
    assert selected["test"][0] == one_query["test"][0]
    keys = [json.dumps(value, separators=(",", ":")) for value in inputs(six_demo)]
    assert len(keys) == len(set(keys)) == 10


@pytest.mark.parametrize("mode,multiplier", [("complete_orbit", 4), ("chain_only", 3)])
def test_fourth_query_is_substantive_30x30_boundary_stress(mode, multiplier):
    module = adapter()
    episode = module.generate(91, {"mode": mode}, 3, 4)
    pair = episode["test"][3]
    grid = pair["input"]
    motif = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5, 6)
    ]
    output_motif = sum(value not in (0, 5, 6) for row in pair["output"] for value in row)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert len(motif) >= 16
    assert any(r in (0, 29) or c in (0, 29) for r, c in motif)
    assert output_motif == multiplier * len(motif)


@pytest.mark.parametrize("mode", ["complete_orbit", "chain_only"])
def test_two_demonstrations_identify_setting_and_declared_shortcuts_without_queries(mode):
    module = adapter()
    episode = module.generate(23, {"mode": mode}, 2, 4)
    certificate = module.certificate(episode["train"], [pair["input"] for pair in episode["test"]])
    assert certificate["survivors"] == [mode]
    assert certificate["demonstrations"] == 2
    assert certificate["queries"] == 4
    assert certificate["legacy_unbroken_vertical_guide_refuted"] is True
    assert set(certificate["declared_hypotheses"]) >= {
        "complete_orbit",
        "chain_only",
        "vertical_only",
        "horizontal_only",
        "diagonal_only",
        "identity",
        "horizontal_chain_only",
        "require_unbroken_vertical_guide",
    }


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"mode": "complete_orbit"}, 2, 4),
        (0, {"mode": "wrong"}, 2, 4),
        (0, {"mode": "complete_orbit", "extra": 1}, 2, 4),
        (0, {"mode": "complete_orbit"}, 1, 4),
        (0, {"mode": "complete_orbit"}, 7, 4),
        (0, {"mode": "complete_orbit"}, 2, 0),
        (0, {"mode": "complete_orbit"}, 2, 5),
        (0, {"mode": "complete_orbit"}, 2, True),
    ],
)
def test_bad_requests_fail_explicitly(seed, settings, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, settings, demos, queries)


def test_boolean_grid_cells_are_not_integer_colors():
    grid = literal_input()
    grid[0][0] = False
    with pytest.raises(ValueError):
        adapter().transform(grid, "chain_only")


def test_public_projection_contains_no_settings_programs_or_query_answers():
    episode = adapter().generate(5, {"mode": "chain_only"}, 3, 4)
    public = public_projection(episode)
    raw = json.dumps(public, sort_keys=True, separators=(",", ":"))
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "settings" not in raw and "program_solution" not in raw


def audit_module():
    path = HOME / "workspace/parametric/audit.py"
    spec = importlib.util.spec_from_file_location("_aad4e3a1d5e3_parametric_audit_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load audit module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_audit_writes_hash_named_one_query_public_views_and_replays(tmp_path):
    module = audit_module()
    output = tmp_path / "audit"
    jobs = [
        {"seed": 0, "settings": {"mode": "complete_orbit"}},
        {"seed": 0, "settings": {"mode": "chain_only"}},
    ]
    report = module.build_audit(output, jobs, demos=2, queries=4)
    assert report["episodes"] == 2
    assert report["public_turns"] == 8
    assert report["query_labels"] == 8
    assert report["racket"]["protected"] is True
    replay = module.verify_audit(output)
    assert replay["status"] == "replayed"
    assert replay["episodes"] == 2 and replay["public_turns"] == 8

    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["training_admitted"] is False
    assert len(manifest["records"]) == 2
    for record in manifest["records"]:
        private = json.loads((output / record["private"]).read_text())
        assert private["settings"]["mode"] in {"complete_orbit", "chain_only"}
        assert len(private["query_turns"]) == 4
        one_query = adapter().generate(private["seed"], private["settings"], 2, 1)
        first_expected = module.public_turn(one_query, 0)
        first_path = output / private["query_turns"][0]["public"]
        assert first_path.read_bytes() == module.encoded(first_expected)
        for turn in private["query_turns"]:
            path = output / turn["public"]
            assert path.stem == hashlib.sha256(path.read_bytes()).hexdigest()
            visible = json.loads(path.read_text())
            assert set(visible) == {"train", "test"}
            assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
            raw = path.read_text()
            assert "settings" not in raw and "program" not in raw and "output\"" not in json.dumps(visible["test"])


def test_audit_refuses_overwrite_and_detects_public_tampering(tmp_path):
    import shutil

    module = audit_module()
    output = tmp_path / "audit"
    jobs = [{"seed": 7, "settings": {"mode": "chain_only"}}]
    module.build_audit(output, jobs, demos=2, queries=4)
    with pytest.raises(FileExistsError):
        module.build_audit(output, jobs, demos=2, queries=4)

    tampered = tmp_path / "tampered"
    shutil.copytree(output, tampered)
    public_path = next((tampered / "public").glob("*.json"))
    visible = json.loads(public_path.read_text())
    visible["test"][0]["input"][0][0] = (visible["test"][0]["input"][0][0] + 1) % 10
    public_path.write_text(json.dumps(visible))
    with pytest.raises(ValueError, match="hash|changed|identity"):
        module.verify_audit(tampered)
