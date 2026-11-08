from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id


TASK = "9c5259babb4b"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
SETTINGS = ("top_bottom_first", "left_right_first")


def _load(path: Path, label: str):
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    name = f"_{label}_{hashlib.sha256(path.read_bytes()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE_PATH, "symmetry_precedence_prototype")


def _adapter():
    return _load(ADAPTER_PATH, "symmetry_precedence_adapter")


def _canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == TASK
    }
    assert len(programs) == 1
    return next(iter(programs))


def _background(grid: list[list[int]]) -> int:
    counts = Counter(value for row in grid for value in row)
    return max(counts, key=lambda value: (counts[value], -value))


def _objects8(grid: list[list[int]], background: int):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if (row, col) in seen or grid[row][col] == background:
                continue
            color = grid[row][col]
            queue = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        other = current_row + dr, current_col + dc
                        if not (dr or dc) or other in seen:
                            continue
                        if 0 <= other[0] < height and 0 <= other[1] < width and grid[other[0]][other[1]] == color:
                            seen.add(other)
                            queue.append(other)
            result.append(cells)
    return result


def _flags(cells: list[tuple[int, int]]) -> tuple[bool, bool, set[tuple[int, int]]]:
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    norm = {(row - row0, col - col0) for row, col in cells}
    height = max(row for row, _ in norm) + 1
    width = max(col for _, col in norm) + 1
    top_bottom = {(height - 1 - row, col) for row, col in norm} == norm
    left_right = {(row, width - 1 - col) for row, col in norm} == norm
    return top_bottom, left_right, norm


def _connected4(cells: set[tuple[int, int]]) -> bool:
    seen = {next(iter(cells))}
    queue = list(seen)
    for row, col in queue:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            other = row + dr, col + dc
            if other in cells and other not in seen:
                seen.add(other)
                queue.append(other)
    return seen == cells


def _oracle(grid: list[list[int]], precedence: str) -> list[list[int]]:
    background = _background(grid)
    output = [[background] * len(grid[0]) for _ in grid]
    for cells in _objects8(grid, background):
        if len(cells) <= 1:
            continue
        top_bottom, left_right, _ = _flags(cells)
        if precedence == "top_bottom_first":
            color = 1 if top_bottom else 3 if left_right else 6
        elif precedence == "left_right_first":
            color = 3 if left_right else 1 if top_bottom else 6
        else:
            raise AssertionError(precedence)
        for row, col in cells:
            output[row][col] = color
    return output


def _input_sequence(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_exact_canonical_default_and_finite_contract():
    adapter = _adapter()
    contract = json.loads(PROMOTION_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK}/workspace/parametric/adapter.py",
        "parameters": {"precedence": list(SETTINGS)},
        "default": {"precedence": "top_bottom_first"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK}/workspace/parametric/prototype.py",
            f"generators/{TASK}/workspace/parametric/top_bottom_first.rkt",
            f"generators/{TASK}/workspace/parametric/left_right_first.rkt",
        ],
    }
    canonical = _canonical_program()
    assert adapter.program({"precedence": "top_bottom_first"}) == canonical
    assert adapter.program({"precedence": "left_right_first"}) != canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == "782048948469c5306f558c8710ece1104ac6b76ad4e414791b5dcf9cdf2d275c"


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"precedence": "bad"}, {"precedence": True}, {"precedence": "top_bottom_first", "x": 1}],
)
def test_settings_fail_closed(settings):
    adapter = _adapter()
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, settings, 3, 4)


@pytest.mark.parametrize("seed", [-1, 2**63, True, 1.0, "1"])
def test_seed_fails_closed(seed):
    adapter = _adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"precedence": "top_bottom_first"}, 3, 4)


@pytest.mark.parametrize("demos", [0, 1, 7, True, 3.0])
def test_demo_count_fails_closed(demos):
    adapter = _adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"precedence": "top_bottom_first"}, demos, 4)


@pytest.mark.parametrize("queries", [0, 1, 3, 5, True, 4.0])
def test_query_count_fails_closed(queries):
    adapter = _adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"precedence": "top_bottom_first"}, 3, queries)


def test_matched_inputs_prefix_stability_distinctness_and_fresh_returns():
    adapter = _adapter()
    top2 = adapter.generate(17, {"precedence": "top_bottom_first"}, 2, 4)
    left2 = adapter.generate(17, {"precedence": "left_right_first"}, 2, 4)
    top6 = adapter.generate(17, {"precedence": "top_bottom_first"}, 6, 4)
    assert [pair["input"] for pair in top2["train"]] == [pair["input"] for pair in left2["train"]]
    assert [pair["input"] for pair in top2["test"]] == [pair["input"] for pair in left2["test"]]
    assert top2["train"] == top6["train"][:2]
    assert [pair["input"] for pair in top2["test"]] == [pair["input"] for pair in top6["test"]]
    assert len({json.dumps(grid) for grid in _input_sequence(top6)}) == 10
    again = adapter.generate(17, {"precedence": "top_bottom_first"}, 2, 4)
    assert again == top2 and again is not top2 and again["train"][0] is not top2["train"][0]
    mutated = copy.deepcopy(top2)
    mutated["train"][0]["input"][0][0] = 9
    assert adapter.generate(17, {"precedence": "top_bottom_first"}, 2, 4) == top2


@pytest.mark.parametrize("seed", [0, 17, 81])
@pytest.mark.parametrize("demos", range(2, 7))
def test_demonstrations_identify_selected_setting_and_all_labels_match_independent_oracle(seed, demos):
    adapter = _adapter()
    for selected in SETTINGS:
        episode = adapter.generate(seed, {"precedence": selected}, demos, 4)
        assert episode["program_solution"] == adapter.program({"precedence": selected})
        assert all(pair["output"] == _oracle(pair["input"], selected) for pair in episode["train"] + episode["test"])
        survivors = [
            candidate
            for candidate in SETTINGS
            if all(_oracle(pair["input"], candidate) == pair["output"] for pair in episode["train"])
        ]
        assert survivors == [selected]


def test_two_demo_teaching_core_exposes_all_classes_singletons_and_diagonal_connectivity():
    prototype = _prototype()
    episode = prototype.build_episode(29, "top_bottom_first", demos=2, queries=4)
    for pair in episode["train"]:
        summary = prototype.scene_summary(pair["input"])
        assert summary["class_counts"] == {"top_bottom_only": 2, "left_right_only": 2, "asymmetric": 1, "both": 1}
        assert 3 <= summary["singleton_count"] <= 10
        assert summary["diagonal_asymmetric_count"] >= 1
        assert summary["setting_difference_cells"] >= 6


def test_four_query_roles_include_size_spread_border_contact_and_substantive_30x30():
    prototype = _prototype()
    episode = prototype.build_episode(43, "left_right_first", demos=3, queries=4)
    summaries = [prototype.scene_summary(pair["input"]) for pair in episode["test"]]
    shapes = [(row["height"], row["width"]) for row in summaries]
    assert 18 <= min(shapes[0]) and max(shapes[0]) <= 21
    assert 22 <= min(shapes[1]) and max(shapes[1]) <= 26
    assert 27 <= min(shapes[2]) and max(shapes[2]) <= 30
    assert summaries[2]["foreground_touches_border"] is True
    assert shapes[3] == (30, 30)
    assert summaries[3]["kept_count"] == 6
    assert summaries[3]["foreground_cells"] >= 45
    assert summaries[3]["diagonal_asymmetric_count"] >= 1
    assert all(row["class_counts"]["both"] == 1 for row in summaries)


def test_public_projection_reveals_one_query_without_private_fields_or_future_inputs():
    prototype = _prototype()
    episode = prototype.build_episode(5, "left_right_first", demos=3, queries=4)
    turns = [prototype.public_projection(episode, index) for index in range(4)]
    assert all(set(turn) == {"train", "test"} for turn in turns)
    assert all(len(turn["train"]) == 3 and len(turn["test"]) == 1 for turn in turns)
    assert all(set(turn["test"][0]) == {"input"} for turn in turns)
    assert [turn["test"][0]["input"] for turn in turns] == [pair["input"] for pair in episode["test"]]
    first_only = prototype.build_episode(5, "left_right_first", demos=3, queries=4)
    assert public_challenge_bytes(turns[0]) == public_challenge_bytes(prototype.public_projection(first_only, 0))
    assert len({public_challenge_id(turn) for turn in turns}) == 4
    changed = copy.deepcopy(episode)
    changed["settings"] = {"precedence": "top_bottom_first"}
    changed["program_solution"] = "private-change"
    changed["test"][0]["output"][0][0] = (changed["test"][0]["output"][0][0] + 1) % 10
    assert public_challenge_bytes(prototype.public_projection(changed, 0)) == public_challenge_bytes(turns[0])


def test_bounded_finite_rival_audit_finds_no_demo_fitting_query_disagreement():
    verify = _load(PARAMETRIC / "verify.py", "symmetry_precedence_verify")
    for seed in (0, 17, 81):
        for setting in SETTINGS:
            report = verify.audit_episode(seed, setting, demos=2)
            assert report["ambiguous_rivals"] == []
            assert report["selected_setting"] == setting
            assert report["demonstration_count"] == 2
            assert "other_declared_setting" in report["defeated_rivals"]
            assert set(report["tested_rivals"]) == {
                "other_declared_setting",
                "four_connected_objects",
                "keep_singletons",
                "ignore_asymmetric",
                "both_as_asymmetric",
                "top_bottom_only",
                "left_right_only",
                "size_parity",
            }
