"""Tests for the proposed, unselected corner-copy direction prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "61c0bcd32328"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def prototype():
    assert PROTOTYPE_PATH.is_file(), "the corner-direction prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        f"parametric_{TASK_ID}", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verifier():
    path = PROTOTYPE_PATH.with_name("verify.py")
    spec = importlib.util.spec_from_file_location(
        f"parametric_verify_{TASK_ID}", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def witness_grid():
    return [
        [1, 1, 7, 7, 7, 7],
        [1, 7, 7, 7, 7, 7],
        [7, 7, 2, 7, 7, 7],
        [7, 7, 7, 7, 3, 7],
        [7, 7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7, 7],
    ]


def test_direction_solver_moves_top_left_object_to_the_selected_adjacent_corner():
    proto = prototype()
    grid = witness_grid()
    clockwise = [
        [1, 1, 7, 7, 1, 1],
        [1, 7, 7, 7, 1, 7],
        [7, 7, 2, 7, 7, 7],
        [7, 7, 7, 7, 3, 7],
        [7, 7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7, 7],
    ]
    counterclockwise = [
        [1, 1, 7, 7, 7, 7],
        [1, 7, 7, 7, 7, 7],
        [7, 7, 2, 7, 7, 7],
        [7, 7, 7, 7, 3, 7],
        [1, 1, 7, 7, 7, 7],
        [1, 7, 7, 7, 7, 7],
    ]
    assert proto.solve(grid, direction="clockwise") == clockwise
    assert proto.solve(grid, direction="counterclockwise") == counterclockwise
    assert grid == witness_grid()


def test_clockwise_default_matches_all_canonical_pairs_and_pinned_rule():
    proto = prototype()
    assert proto.DEFAULT_DIRECTION == "clockwise"
    assert proto.normalized_program_hash("clockwise") == (
        "e3835c9a174e5fd8b8be9b2c3a7bd754629ce5f5197d6e25d7be704d40d32692"
    )
    assert proto.program_for("clockwise") == proto.canonical_source()
    assert proto.program_for("counterclockwise") != proto.program_for("clockwise")
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert proto.solve(pair["input"], direction="clockwise") == pair["output"]


def test_episode_has_three_demos_four_distinct_queries_and_one_fixed_setting():
    proto = prototype()
    episode = proto.generate_episode(
        17,
        direction="counterclockwise",
        n_train=3,
        n_test=4,
    )
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert episode["parameters"] == {"direction": "counterclockwise"}
    assert episode["meta"]["n_train"] == 3
    assert episode["meta"]["n_test"] == 4

    pairs = episode["train"] + episode["test"]
    input_signatures = {tuple(map(tuple, pair["input"])) for pair in pairs}
    assert len(input_signatures) == 7
    selected_generator, _, _ = proto.selected_generator()
    for pair in pairs:
        assert selected_generator.self_check(pair["input"]) == []
        assert pair["output"] == proto.solve(
            pair["input"], direction="counterclockwise"
        )
        assert pair["output"] != proto.solve(pair["input"], direction="clockwise")


def test_public_projection_hides_setting_rule_metadata_and_query_answers():
    proto = prototype()
    episode = proto.generate_episode(5, direction="clockwise", n_train=3, n_test=4)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

    original_id = proto.public_id(episode)
    changed_private = deepcopy(episode)
    changed_private["parameters"]["direction"] = "counterclockwise"
    changed_private["program"] = "private replacement"
    changed_private["meta"]["seed"] = 999999
    changed_private["test"][0]["output"] = [[9]]
    assert proto.public_id(changed_private) == original_id
    filename = proto.public_filename(episode)
    assert filename == f"challenge-{original_id}.json"
    assert "clockwise" not in filename and "counterclockwise" not in filename
    assert "seed" not in filename


def test_runtime_identity_paths_are_portable_and_hashes_are_preserved():
    verify = verifier()
    identity = {
        "backend": "racket",
        "binary_path": "/tmp/review/.review/racket-runtime/racket/bin/racket",
        "binary_sha256": "binary-hash",
        "bridge_path": str(
            ROOT / "shared" / "runtime" / "arc_repl" / "racket_bridge.py"
        ),
        "bridge_sha256": "bridge-hash",
        "prelude_path": str(
            ROOT
            / "shared"
            / "runtime"
            / "arc_repl"
            / "racket_prelude"
            / "arc-prelude.rkt"
        ),
        "prelude_sha256": "prelude-hash",
    }

    portable = verify.portable_runtime_identity(identity)

    assert portable == {
        "backend": "racket",
        "binary_path": "racket",
        "binary_sha256": "binary-hash",
        "bridge_path": "shared/runtime/arc_repl/racket_bridge.py",
        "bridge_sha256": "bridge-hash",
        "prelude_path": "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt",
        "prelude_sha256": "prelude-hash",
    }
    assert all(
        not Path(value).is_absolute()
        for key, value in portable.items()
        if key.endswith("_path")
    )


@pytest.mark.parametrize(
    "call",
    [
        lambda proto: proto.solve(witness_grid(), direction="sideways"),
        lambda proto: proto.generate_episode(-1),
        lambda proto: proto.generate_episode(1, n_train=0),
        lambda proto: proto.generate_episode(1, n_test=True),
    ],
)
def test_invalid_settings_seeds_and_counts_fail_loudly(call):
    with pytest.raises(ValueError):
        call(prototype())


def _run_isolated_materializer(monkeypatch, tmp_path, proto, public_write_order):
    """Run the real materializer while replacing only external Racket execution."""
    verify = verifier()
    fake_verify_path = tmp_path / "verify.py"
    fake_verify_path.write_text("# isolated materializer test\n", encoding="utf-8")
    fake_verify_path.with_name("prototype.py").write_text(
        "# isolated materializer test\n", encoding="utf-8"
    )
    monkeypatch.setattr(verify, "HERE", fake_verify_path)
    monkeypatch.setattr(verify, "_load_prototype", lambda: proto)

    class FakeBridge:
        runtime_identity = {
            "backend": "test-double",
            "binary_path": "racket",
            "binary_sha256": "test-binary",
            "bridge_path": "arc_repl/racket_bridge.py",
            "bridge_sha256": "test-bridge",
            "prelude_path": "arc_repl/racket_prelude/arc-prelude.rkt",
            "prelude_sha256": "test-prelude",
        }

        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

    def apply_with_python_mirror(_bridge, program, grids):
        direction = next(
            setting
            for setting in proto.ALLOWED_DIRECTIONS
            if program == proto.program_for(setting)
        )
        return [proto.solve(grid, direction=direction) for grid in grids]

    monkeypatch.setattr(verify, "RacketBridge", FakeBridge)
    monkeypatch.setattr(verify, "_racket_apply_many", apply_with_python_mirror)
    monkeypatch.setattr(
        verify,
        "_singleton_repair_report",
        lambda *_args: {
            "racket_matches_production_mirror": True,
            "ignore_singleton_rival_refuted": True,
        },
    )

    public_dir = tmp_path / "episodes" / "public"
    original_write_bytes = Path.write_bytes

    def record_public_write(path, data):
        if path.parent == public_dir:
            public_write_order.append(path.name)
        return original_write_bytes(path, data)

    monkeypatch.setattr(Path, "write_bytes", record_public_write)
    return verify.build_report()


def test_materializer_emits_public_files_in_public_id_order_when_settings_reverse(
    monkeypatch, tmp_path
):
    """Private setting enumeration must not determine public creation order."""
    proto = prototype()
    retained_dir = PROTOTYPE_PATH.parent / "episodes" / "private"
    retained = {
        setting: json.loads(
            (retained_dir / f"{setting}-complete.json").read_text(encoding="utf-8")
        )
        for setting in proto.SETTINGS
    }
    monkeypatch.setattr(
        proto,
        "generate_episode",
        lambda _seed, *, direction, **_kwargs: deepcopy(retained[direction]),
    )
    monkeypatch.setattr(proto, "SETTINGS", tuple(reversed(proto.SETTINGS)))
    public_write_order = []

    report = _run_isolated_materializer(
        monkeypatch, tmp_path, proto, public_write_order
    )

    public_ids = [row["public_id"] for row in report["settings"]]
    expected_filenames = [f"challenge-{value}.json" for value in sorted(public_ids)]
    assert public_write_order == expected_filenames
    assert public_ids == sorted(public_ids)


def test_materializer_rejects_duplicate_public_ids_before_any_public_write(
    monkeypatch, tmp_path
):
    """A colliding batch must leave no partially emitted public challenge."""
    proto = prototype()
    duplicate_episode = json.loads(
        (
            PROTOTYPE_PATH.parent
            / "episodes"
            / "private"
            / "clockwise-complete.json"
        ).read_text(encoding="utf-8")
    )
    monkeypatch.setattr(
        proto,
        "generate_episode",
        lambda *_args, **_kwargs: deepcopy(duplicate_episode),
    )
    public_write_order = []

    with pytest.raises(ValueError, match="duplicate visible public challenge payload"):
        _run_isolated_materializer(monkeypatch, tmp_path, proto, public_write_order)

    assert public_write_order == []
