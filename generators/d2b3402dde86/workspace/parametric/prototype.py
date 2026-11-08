"""Proposed episode-fixed four-corner crop family for ``d2b3402dde86``.

The canonical task is the ``upper_left`` default.  This module is a separate
proposal: it samples inputs without consulting the hidden setting, supports the
native adapter contract, and keeps sequential public turns independent of all
private fields and future queries.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "d2b3402dde86"
HERE = Path(__file__).resolve().parent
PARAMETER_NAME = "corner"
ALLOWED_SETTINGS = ("upper_left", "upper_right", "lower_left", "lower_right")
DEFAULT_SETTING = "upper_left"
PROTOTYPE_VERSION = "2.0.0"
_UNSET = object()

# Outer height/width, content height/width, top/left.  Prefixes are stable: no
# requested count or private setting enters this table or the per-item RNG.
DEMO_SPECS = (
    (11, 13, 8, 10, 1, 2),
    (14, 12, 9, 8, 3, 1),
    (17, 19, 13, 15, 2, 3),
    (22, 18, 18, 13, 1, 4),
    (26, 27, 21, 23, 4, 2),
    (30, 25, 27, 21, 0, 3),
)
QUERY_SPECS = (
    (12, 14, 10, 12, 1, 1),
    (21, 17, 17, 13, 3, 2),
    (27, 28, 25, 26, 1, 1),
    (30, 30, 30, 30, 0, 0),
)


def _load_selected_generator():
    path = HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("d2_parametric_selected", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load selected generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_SELECTED = _load_selected_generator()


def _integer(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    return value


def _settings(settings: object) -> str:
    if (type(settings) is not dict or set(settings) != {PARAMETER_NAME}
            or type(settings[PARAMETER_NAME]) is not str
            or settings[PARAMETER_NAME] not in ALLOWED_SETTINGS):
        raise ValueError("settings must contain only corner=upper_left|upper_right|lower_left|lower_right")
    return settings[PARAMETER_NAME]


def _validate_setting_legacy(setting: object) -> str:
    if type(setting) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if setting not in ALLOWED_SETTINGS:
        raise ValueError(f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}")
    return setting


def choose_setting(seed: int) -> str:
    if type(seed) is not int:
        raise TypeError("seed must be a non-negative integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be a non-negative integer")
    digest = hashlib.sha256(f"{TASK_ID}:corner:{seed}".encode()).digest()
    return ALLOWED_SETTINGS[digest[0] % len(ALLOWED_SETTINGS)]


def freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _grid(grid: object) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def _content(grid: object) -> list[list[int]]:
    data = _grid(grid)
    cells = [(r, c) for r, row in enumerate(data) for c, value in enumerate(row) if value != 0]
    if not cells:
        raise ValueError("grid contains no non-zero content")
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    return [list(row[left:right + 1]) for row in data[top:bottom + 1]]


def transform(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    corner = _settings(settings)
    content = _content(grid)
    out_h, out_w = len(content) // 2, len(content[0]) // 2
    if out_h < 1 or out_w < 1:
        raise ValueError("cropped content must be at least 2x2")
    top = 0 if corner.startswith("upper_") else len(content) - out_h
    left = 0 if corner.endswith("_left") else len(content[0]) - out_w
    return [row[left:left + out_w] for row in content[top:top + out_h]]


def apply_python(grid: list[list[int]], setting: str) -> list[list[int]]:
    return transform(grid, {PARAMETER_NAME: _validate_setting_legacy(setting)})


def apply_canonical(grid: list[list[int]]) -> list[list[int]]:
    return _SELECTED.rule_mirror(grid)


def program(settings: dict[str, str]) -> str:
    corner = _settings(settings)
    return (HERE / f"{corner}.rkt").read_text(encoding="utf-8").rstrip("\n")


def program_for(setting: str) -> str:
    return program({PARAMETER_NAME: _validate_setting_legacy(setting)})


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:corner-v2:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _draw(seed: int, split: str, index: int) -> list[list[int]]:
    outer_h, outer_w, content_h, content_w, top, left = (
        DEMO_SPECS if split == "train" else QUERY_SPECS
    )[index]
    rng = _rng(seed, split, index)
    palette = rng.sample(range(1, 10), 8)
    grid = [[0] * outer_w for _ in range(outer_h)]
    half_h, half_w = content_h // 2, content_w // 2
    for r in range(content_h):
        for c in range(content_w):
            vertical = 0 if r < half_h else 1 if r >= content_h - half_h else 2
            horizontal = 0 if c < half_w else 1 if c >= content_w - half_w else 2
            if vertical < 2 and horizontal < 2:
                quadrant = 2 * vertical + horizontal
                # Distinct base and deterministic texture make the stress case
                # substantive while retaining an unbroken content bounding box.
                value = palette[quadrant]
                if (r * 3 + c * 5 + seed + index) % 7 == 0:
                    value = palette[4 + quadrant]
            else:
                value = palette[(r + 2 * c + index) % 4]
            grid[top + r][left + c] = value
    outputs = [transform(grid, {PARAMETER_NAME: value}) for value in ALLOWED_SETTINGS]
    if len({json.dumps(value, separators=(",", ":")) for value in outputs}) != 4:
        raise AssertionError("constructed input failed to distinguish all four corners")
    return grid


def teaching_certificate(train: list[dict[str, Any]], query_inputs: list[list[list[int]]],
                         settings: dict[str, str]) -> dict[str, Any]:
    chosen = _settings(settings)
    if type(train) is not list or not train or type(query_inputs) is not list or not query_inputs:
        raise ValueError("nonempty demonstrations and query inputs are required")
    rejected: dict[str, int] = {}
    for index, pair in enumerate(train):
        expected = pair.get("output")
        _grid(expected)
        for candidate in ALLOWED_SETTINGS:
            if transform(pair["input"], {PARAMETER_NAME: candidate}) != expected:
                rejected.setdefault(candidate, index)
    survivors = [candidate for candidate in ALLOWED_SETTINGS if candidate not in rejected]
    if chosen not in survivors:
        raise ValueError("demonstration labels contradict selected corner")
    query_identifiable = []
    for grid in query_inputs:
        chosen_output = transform(grid, settings)
        query_identifiable.append(all(
            transform(grid, {PARAMETER_NAME: survivor}) == chosen_output
            for survivor in survivors
        ))
    return {
        "scope": "the four declared corner settings",
        "survivors": survivors,
        "rejected": rejected,
        "identified": survivors == [chosen],
        "query_identifiable": query_identifiable,
        "query_answers_used_for_fitting": False,
    }


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _settings(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode: dict[str, Any] = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": copy.deepcopy(settings),
        "program_solution": program(settings),
        "reference": "proposed_parametric",
        "training_admitted": False,
    }
    for split, count in (("train", demos), ("test", queries)):
        episode[split] = []
        for index in range(count):
            grid = _draw(seed, split, index)
            episode[split].append({"input": grid, "output": transform(grid, settings)})
    episode["certificate"] = verify_episode(episode)
    return episode


def verify_episode(episode: object) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = episode.get("settings")
    _settings(settings)
    if episode.get("program_solution") != program(settings):
        raise ValueError("program_solution does not match selected corner")
    seen: set[str] = set()
    for split, bounds in (("train", (2, 6)), ("test", (1, 4))):
        pairs = episode.get(split)
        if type(pairs) is not list or not bounds[0] <= len(pairs) <= bounds[1]:
            raise ValueError(f"unsupported {split} count")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("each pair must contain input and output")
            expected = transform(pair["input"], settings)
            _grid(pair["output"])
            if pair["output"] != expected:
                raise ValueError(f"{split} label disagrees with selected corner")
            key = json.dumps(pair["input"], separators=(",", ":"))
            if key in seen:
                raise ValueError("all inputs must be distinct")
            seen.add(key)
    certificate = teaching_certificate(
        episode["train"], [pair["input"] for pair in episode["test"]], settings
    )
    if not certificate["identified"] or not all(certificate["query_identifiable"]):
        raise ValueError("demonstrations do not identify the selected corner")
    return certificate


def visible_turn(episode: dict[str, Any], index: int) -> bytes:
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge_bytes({
        "train": episode["train"],
        "test": [episode["test"][index]],
    })


def write_export(episodes: list[dict[str, Any]], output: str | Path) -> dict[str, Any]:
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    if type(episodes) is not list or not episodes:
        raise ValueError("a nonempty episode list is required")
    rows = []
    for episode in episodes:
        certificate = verify_episode(episode)
        turns = []
        for index in range(len(episode["test"])):
            payload = visible_turn(episode, index)
            turns.append((hashlib.sha256(payload).hexdigest(), payload))
        private = copy.deepcopy(episode)
        private["certificate"] = certificate
        private["reveal_ids"] = [item[0] for item in turns]
        rows.append((turns, private))
    public_payloads = {identifier: payload for turns, _ in rows for identifier, payload in turns}
    if len(public_payloads) != sum(len(turns) for turns, _ in rows):
        raise ValueError("duplicate visible challenge")
    output.mkdir(parents=True)
    (output / "public").mkdir()
    for identifier, payload in sorted(public_payloads.items()):
        (output / "public" / f"{identifier}.json").write_bytes(payload)
    private_bytes = b"".join(
        (json.dumps(private, sort_keys=True, separators=(",", ":")) + "\n").encode()
        for _, private in rows
    )
    (output / "private.jsonl").write_bytes(private_bytes)
    manifest = {
        "schema": f"{TASK_ID}-corner-parametric-export-v2",
        "status": "proposed",
        "training_admitted": False,
        "public_ids": sorted(public_payloads),
        "private_sha256": hashlib.sha256(private_bytes).hexdigest(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


# Compatibility with the earlier task-local prototype API.
def build_episode(seed: int, *, setting: object = _UNSET) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be a non-negative integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be a non-negative integer")
    selected = choose_setting(seed) if setting is _UNSET else _validate_setting_legacy(setting)
    episode = generate(seed, {PARAMETER_NAME: selected}, 3, 1)
    episode["program"] = episode["program_solution"]
    episode["meta"] = {
        "seed": seed,
        PARAMETER_NAME: selected,
        "allowed_settings": list(ALLOWED_SETTINGS),
        "default_setting": DEFAULT_SETTING,
        "prototype_version": PROTOTYPE_VERSION,
        "selected_generator_version": getattr(_SELECTED, "VERSION", "unknown"),
        "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest(),
    }
    return episode


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return json.loads(public_challenge_bytes(episode))
