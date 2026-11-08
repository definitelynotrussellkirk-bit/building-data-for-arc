"""Focused base-generator regressions for 8801696784e1."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "8801696784e1"
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PARAMETRIC_HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _canonical_pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT)


def _canonical_program() -> str:
    programs: set[str] = set()
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
            programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _load_parametric_module(name: str):
    path = PARAMETRIC_HOME / name
    assert path.is_file(), f"missing parametric source: {path}"
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}_{name.replace('.', '_')}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_all_canonical_inputs_remain_valid() -> None:
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        assert GEN.self_check(grid) == []
        assert grid == pair["input"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    ("grid_h", "grid_w"),
    [(8, 10), (8, 17), (14, 10), (14, 17)],
)
def test_exact_grid_boundaries_override_sampling_bands(
    difficulty: str | None, grid_h: int, grid_w: int
) -> None:
    grid = GEN.generate(
        4100 + grid_h * 31 + grid_w,
        7,
        difficulty=difficulty,
        grid_h=grid_h,
        grid_w=grid_w,
    )
    assert (len(grid), len(grid[0])) == (grid_h, grid_w)
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"palette_kind": "default"},
        {"palette_kind": "warm"},
        {"palette_kind": "cool"},
        {"palette_kind": "varied"},
        {"texture": "default"},
        {"texture": "warm"},
        {"texture": "cool"},
        {"texture": "varied"},
        {"palette_size": 2},
        {"position_bias": "code_plus_sym_plus_asym"},
        {"n_distinct_colors": 2},
        {"density": "sparse"},
    ],
)
def test_every_declared_helpful_override_is_accepted(overrides: dict) -> None:
    grid = GEN.generate(8123, 3, difficulty="medium", **overrides)
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"misspelled_axis": 1},
        {"grid_h": True},
        {"grid_w": 18},
        {"palette_kind": "typo"},
        {"texture": "typo"},
        {"palette_size": 3},
        {"position_bias": "corner"},
        {"n_distinct_colors": 3},
        {"density": "dense"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides: dict) -> None:
    with pytest.raises((TypeError, ValueError), match="override|grid_|palette|texture|density|position|distinct"):
        GEN.generate(17, 0, **overrides)


def test_self_check_rejects_non_integer_arc_cells() -> None:
    grid = GEN.generate(9231, 2)
    grid[0][0] = 0.0
    errors = GEN.self_check(grid)
    assert errors
    assert any("integer" in error for error in errors)


def test_generation_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(20261026)
    state = random.getstate()
    first = GEN.generate(123456, 13, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(123456, 13, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    frozen = copy.deepcopy(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(123456, 13, difficulty="hard") == frozen


def _strict_grid(grid: list[list[int]]) -> None:
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
    width = len(grid[0])
    assert all(type(row) is list and len(row) == width for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)


def test_parametric_default_program_is_exact_canonical_source() -> None:
    adapter = _load_parametric_module("adapter.py")
    canonical = _canonical_program()
    assert adapter.program({"object_kind": "symmetric"}) == canonical
    alternate = adapter.program({"object_kind": "asymmetric"})
    assert alternate != canonical
    assert hashlib.sha256(alternate.encode()).hexdigest() != hashlib.sha256(canonical.encode()).hexdigest()


@pytest.mark.parametrize("settings", [{"object_kind": "symmetric"}, {"object_kind": "asymmetric"}])
@pytest.mark.parametrize(("demos", "queries"), [(2, 1), (3, 4), (6, 4)])
def test_parametric_episode_counts_types_distinctness_and_determinism(
    settings: dict, demos: int, queries: int
) -> None:
    adapter = _load_parametric_module("adapter.py")
    first = adapter.generate(20261026, settings, demos, queries)
    second = adapter.generate(20261026, settings, demos, queries)
    assert first == second
    assert first is not second
    assert first["program_solution"] == adapter.program(settings)
    assert len(first["train"]) == demos
    assert len(first["test"]) == queries
    pairs = first["train"] + first["test"]
    fingerprints = []
    for pair in pairs:
        assert set(pair) >= {"input", "output"}
        _strict_grid(pair["input"]); _strict_grid(pair["output"])
        fingerprints.append(json.dumps(pair["input"], separators=(",", ":")))
    assert len(fingerprints) == len(set(fingerprints))


def test_parametric_demonstrations_alone_identify_object_kind() -> None:
    prototype = _load_parametric_module("prototype.py")
    for selected in ("symmetric", "asymmetric"):
        episode = prototype.generate(17, {"object_kind": selected}, 2, 4)
        other = "asymmetric" if selected == "symmetric" else "symmetric"
        assert all(
            prototype.transform(pair["input"], {"object_kind": selected}) == pair["output"]
            for pair in episode["train"] + episode["test"]
        )
        assert any(
            prototype.transform(pair["input"], {"object_kind": other}) != pair["output"]
            for pair in episode["train"]
        )


def test_parametric_fourth_query_is_substantive_30x30_stress() -> None:
    adapter = _load_parametric_module("adapter.py")
    episode = adapter.generate(0, {"object_kind": "symmetric"}, 3, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    nonzero = sum(value != 0 for row in grid for value in row)
    rows = {r for r, row in enumerate(grid) for value in row if value != 0}
    cols = {c for row in grid for c, value in enumerate(row) if value != 0}
    assert nonzero >= 40
    assert max(rows) - min(rows) >= 18
    assert max(cols) - min(cols) >= 18


@pytest.mark.parametrize(
    ("settings", "demos", "queries"),
    [
        ({}, 3, 4),
        ({"object_kind": "symmetric", "extra": 1}, 3, 4),
        ({"object_kind": "unknown"}, 3, 4),
        ({"object_kind": "symmetric"}, 1, 4),
        ({"object_kind": "symmetric"}, 7, 4),
        ({"object_kind": "symmetric"}, 3, 0),
        ({"object_kind": "symmetric"}, 3, 5),
    ],
)
def test_parametric_rejects_invalid_settings_and_counts(settings: dict, demos: int, queries: int) -> None:
    adapter = _load_parametric_module("adapter.py")
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings, demos, queries)


def _relative_order(left: float, right: float) -> int:
    return (left > right) - (left < right)


def test_parametric_object_kind_is_not_confounded_with_position_or_component_size() -> None:
    """A location/size shortcut must not recover symmetric versus asymmetric."""
    prototype = _load_parametric_module("prototype.py")
    vertical_orders: set[int] = set()
    horizontal_orders: set[int] = set()
    size_orders: set[int] = set()
    for seed in range(16):
        for split, count in (("demo", 6), ("query", 4)):
            for index in range(count):
                grid = prototype.sample_input(seed, split, index)
                classified = {}
                for component in prototype._components(grid):
                    crop = prototype._crop(grid, component)
                    kind = "symmetric" if prototype._both_symmetric(crop) else "asymmetric"
                    rows = [r for r, _ in component]
                    cols = [c for _, c in component]
                    classified[kind] = {
                        "size": len(component),
                        "row": (min(rows) + max(rows)) / 2,
                        "col": (min(cols) + max(cols)) / 2,
                    }
                assert set(classified) == {"symmetric", "asymmetric"}
                symmetric = classified["symmetric"]
                asymmetric = classified["asymmetric"]
                vertical_orders.add(_relative_order(symmetric["row"], asymmetric["row"]))
                horizontal_orders.add(_relative_order(symmetric["col"], asymmetric["col"]))
                size_orders.add(_relative_order(symmetric["size"], asymmetric["size"]))
    assert {-1, 1} <= vertical_orders
    assert {-1, 1} <= horizontal_orders
    assert {-1, 1} <= size_orders


def test_two_demo_prefix_breaks_position_and_size_shortcuts_for_every_seed() -> None:
    prototype = _load_parametric_module("prototype.py")
    for seed in range(32):
        vertical_orders: set[int] = set()
        horizontal_orders: set[int] = set()
        size_orders: set[int] = set()
        for index in range(2):
            grid = prototype.sample_input(seed, "demo", index)
            classified = {}
            for component in prototype._components(grid):
                crop = prototype._crop(grid, component)
                kind = "symmetric" if prototype._both_symmetric(crop) else "asymmetric"
                rows = [r for r, _ in component]
                cols = [c for _, c in component]
                classified[kind] = (len(component), (min(rows) + max(rows)) / 2,
                                    (min(cols) + max(cols)) / 2)
            symmetric = classified["symmetric"]
            asymmetric = classified["asymmetric"]
            size_orders.add(_relative_order(symmetric[0], asymmetric[0]))
            vertical_orders.add(_relative_order(symmetric[1], asymmetric[1]))
            horizontal_orders.add(_relative_order(symmetric[2], asymmetric[2]))
        assert size_orders == {-1, 1}, seed
        assert vertical_orders == {-1, 1}, seed
        assert horizontal_orders == {-1, 1}, seed


def test_refresh_recipe_intermediate_is_derived_from_selected_asymmetric_case() -> None:
    refresh = _load_parametric_module("refresh_evidence.py")
    prototype = _load_parametric_module("prototype.py")
    pair = prototype.generate(17, {"object_kind": "asymmetric"}, 2, 4)["test"][0]
    draft = {
        "step_a": "",
        "intermediate": "",
        "step_b": "",
        "why_b_depends_on_a": "",
        "selected_case": {
            "settings": {"object_kind": "asymmetric"},
            "input": copy.deepcopy(pair["input"]),
            "output": copy.deepcopy(pair["output"]),
        },
        "cases": [{
            "episode_index": 0,
            "split": "test",
            "pair_index": 0,
            "counterfactual_program": "(lambda (grid) grid)",
            "intermediate_value": None,
            "ablation": "wrong_intermediate",
        }],
    }
    pristine = copy.deepcopy(draft)
    recipe = refresh.fill_recipe(draft)

    candidates = []
    for component in prototype._components(pair["input"]):
        crop = prototype._crop(pair["input"], component)
        if not prototype._both_symmetric(crop):
            candidates.append((len(component), crop))
    expected_crop = max(candidates, key=lambda item: item[0])[1]
    assert recipe["cases"][0]["intermediate_value"] == {
        "selected_object_kind": "asymmetric",
        "corner_code": pair["input"][-1][-1],
        "selected_crop": expected_crop,
    }
    assert all(recipe[name].strip() for name in refresh.DESCRIPTION_FIELDS)
    assert recipe["cases"][0]["counterfactual_program"] == "(lambda (grid) grid)"
    assert draft == pristine


def test_refresh_rejects_a_receipt_from_another_source_binding() -> None:
    refresh = _load_parametric_module("refresh_evidence.py")
    expected = {"task_id": TASK_ID, "files": [{"path": "a", "sha256": "0" * 64}]}
    refresh.require_source_binding(expected, {"source_binding": copy.deepcopy(expected)}, "qualification")
    mixed = copy.deepcopy(expected)
    mixed["files"][0]["sha256"] = "1" * 64
    with pytest.raises(ValueError, match="mixed-source qualification"):
        refresh.require_source_binding(expected, {"source_binding": mixed}, "qualification")


def test_manifest_transaction_rolls_back_uncommitted_replacement(tmp_path: Path) -> None:
    refresh = _load_parametric_module("refresh_evidence.py")
    manifest = tmp_path / "manifest.json"
    manifest.write_bytes(b"old manifest\n")
    with pytest.raises(RuntimeError, match="abort"):
        with refresh.ManifestTransaction(manifest) as transaction:
            transaction.replace(b"new manifest\n")
            raise RuntimeError("abort")
    assert manifest.read_bytes() == b"old manifest\n"

    with refresh.ManifestTransaction(manifest) as transaction:
        transaction.replace(b"committed manifest\n")
        transaction.commit()
    assert manifest.read_bytes() == b"committed manifest\n"


def test_refresh_source_snapshot_covers_tool_and_excludes_evidence() -> None:
    refresh = _load_parametric_module("refresh_evidence.py")
    snapshot = refresh.source_snapshot(ROOT)
    paths = {row["path"] for row in snapshot["files"]}
    assert f"generators/{TASK_ID}/workspace/parametric/refresh_evidence.py" in paths
    assert f"generators/{TASK_ID}/tests/test_generator_{TASK_ID}.py" in paths
    assert all("/evidence/" not in path for path in paths)
    assert snapshot["sha256"] == refresh.snapshot_sha256(snapshot["files"])


def test_refresh_activates_packet_racket_when_environment_is_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    refresh = _load_parametric_module("refresh_evidence.py")
    expected = tmp_path / ".review" / "racket-runtime" / "racket" / "bin" / "racket"
    expected.parent.mkdir(parents=True)
    expected.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    expected.chmod(0o755)
    monkeypatch.delenv("RACKET_PATH", raising=False)
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    selected = refresh.activate_racket(tmp_path)
    assert selected == expected.resolve()
    assert Path(os.environ["RACKET_PATH"]) == expected.resolve()
    assert os.environ["PATH"].split(os.pathsep)[0] == str(expected.resolve().parent)


def test_refresh_portable_relative_rejects_machine_external_paths(tmp_path: Path) -> None:
    refresh = _load_parametric_module("refresh_evidence.py")
    member = tmp_path / "checks" / "receipt.json"
    member.parent.mkdir()
    member.write_text("{}\n", encoding="utf-8")
    assert refresh.portable_relative(member, tmp_path) == "checks/receipt.json"
    with pytest.raises(ValueError, match="outside portable root"):
        refresh.portable_relative(tmp_path.parent / "external.json", tmp_path)


def test_output_transaction_removes_published_directory_until_committed(tmp_path: Path) -> None:
    refresh = _load_parametric_module("refresh_evidence.py")
    destination = tmp_path / "published"
    with pytest.raises(RuntimeError, match="abort after rename"):
        with refresh.OutputTransaction(destination) as publication:
            (publication.stage / "receipt.json").write_text("{}\n", encoding="utf-8")
            publication.publish()
            raise RuntimeError("abort after rename")
    assert not destination.exists()

    with refresh.OutputTransaction(destination) as publication:
        (publication.stage / "receipt.json").write_text("{}\n", encoding="utf-8")
        publication.publish()
        publication.commit()
    assert (destination / "receipt.json").read_text(encoding="utf-8") == "{}\n"






def test_refresh_replaces_runtime_test_tree_with_compact_receipt(tmp_path: Path) -> None:
    refresh = _load_parametric_module("refresh_evidence.py")
    stage = tmp_path / "stage"
    runtime = stage / "task-tests"
    runtime.mkdir(parents=True)
    (runtime / "result.json").write_text(
        '{"runtime_path":"/mnt/data/private/runtime"}\n', encoding="utf-8"
    )
    receipt = {
        "schema": "arcpuzzles-source-bound-task-tests-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "command": ["python3", "-m", "pytest", f"generators/{TASK_ID}/tests"],
        "test_counts": {"tests": 1, "passed": 1, "failed": 0, "errors": 0},
    }
    refresh._publish_compact_task_tests(stage, receipt)
    assert not runtime.exists()
    published = stage / "task-tests.json"
    assert json.loads(published.read_text(encoding="utf-8")) == receipt
    assert "/mnt/data/" not in published.read_text(encoding="utf-8")


def test_refresh_normalizes_causal_replay_witness_path(tmp_path: Path) -> None:
    refresh = _load_parametric_module("refresh_evidence.py")
    stage = tmp_path / "stage"
    causal = stage / "causal"
    causal.mkdir(parents=True)
    witness = causal / "witness.json"
    witness.write_text("{}\n", encoding="utf-8")
    replay = {
        "schema": "test-replay",
        "source_binding": {"task_id": TASK_ID},
        "witness_path": str(witness.resolve()),
    }
    (causal / "replay.json").write_text(json.dumps(replay) + "\n", encoding="utf-8")
    normalized = refresh._normalize_causal_replay(stage)
    assert normalized["witness_path"] == "causal/witness.json"
    assert normalized["source_binding"] == {"task_id": TASK_ID}
    assert json.loads((causal / "replay.json").read_text())["witness_path"] == "causal/witness.json"

def test_refresh_installs_content_addressed_task_evidence(tmp_path: Path) -> None:
    refresh = _load_parametric_module("refresh_evidence.py")
    receipt = {
        "schema": "test-task-evidence",
        "task_id": TASK_ID,
        "source_snapshot_sha256": "a" * 64,
        "test_counts": {"tests": 1, "passed": 1, "failed": 0, "errors": 0},
    }
    destination, created = refresh._install_task_evidence(tmp_path, receipt)
    assert created is True
    assert destination.name.startswith("refresh-aaaaaaaaaaaaaaaa-")
    assert json.loads((destination / "task-tests.json").read_text(encoding="utf-8")) == receipt
    repeated, repeated_created = refresh._install_task_evidence(tmp_path, receipt)
    assert repeated == destination
    assert repeated_created is False

def test_refresh_recovers_manifest_output_and_revision_after_hard_interruption(
    tmp_path: Path,
) -> None:
    refresh = _load_parametric_module("refresh_evidence.py")
    work_root = tmp_path / "WORK"
    root = work_root / "repo"
    manifest = (
        root / "generators" / TASK_ID / "workspace" / "parametric" /
        "evidence" / "manifest.json"
    )
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes(b"old manifest\n")
    output = work_root / "checks" / TASK_ID

    publication = refresh.OutputTransaction(output)
    publication.__enter__()
    assert publication.stage is not None
    journal = refresh.RefreshJournal(work_root, root, manifest, publication)
    journal.__enter__()

    manifest.write_bytes(b"interrupted manifest\n")
    (publication.stage / "partial.json").write_text("{}\n", encoding="utf-8")
    publication.publish()
    revision = (
        root / "generators" / TASK_ID / "workspace" / "parametric" /
        "evidence" / "revisions" / "refresh-interrupted"
    )
    revision.mkdir(parents=True)
    (revision / "task-tests.json").write_text("{}\n", encoding="utf-8")
    journal.record_revision(revision, created=True)

    # Deliberately skip every __exit__: this models SIGKILL/process death.
    assert output.is_dir()
    assert journal.path.is_file()
    assert refresh.recover_interrupted_refresh(work_root, root) is True
    assert manifest.read_bytes() == b"old manifest\n"
    assert not output.exists()
    assert not revision.exists()
    assert not journal.path.exists()
    assert refresh.recover_interrupted_refresh(work_root, root) is False
