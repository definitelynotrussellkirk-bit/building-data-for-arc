"""Task-local episode-fixed rule variants for ``0f7d80015d9d``.

The canonical rule moves the red marker to the cyan position and stamps a new
cyan cell outside the bottom gray rectangle, opposite the original red marker.
This proposed prototype varies two nearby semantic choices once per episode:

* ``stamp_relation``: stamp on the side opposite red (canonical) or the same
  side as red;
* ``midpoint_side``: count the rectangle midpoint as right (canonical) or left.

Production generation and canonical authority remain unchanged.  The default
setting returns the registered canonical Racket program byte-for-byte.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from functools import lru_cache
from typing import Any, Iterable

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
)


TASK_ID = "0f7d80015d9d"
PROTOTYPE_VERSION = "1.0.0"
STAMP_RELATIONS = ("opposite", "same")
MIDPOINT_SIDES = ("right", "left")
MIN_TRAIN = 3
MIN_TEST = 4


@dataclass(frozen=True, order=True)
class RuleSetting:
    stamp_relation: str
    midpoint_side: str


DEFAULT_SETTING = RuleSetting("opposite", "right")
SETTINGS = (
    DEFAULT_SETTING,
    RuleSetting("opposite", "left"),
    RuleSetting("same", "right"),
    RuleSetting("same", "left"),
)

_RED_LEFT_CANONICAL = "(red-left (< (snd red-cell) mid-c))"
_RED_LEFT_MIDPOINT_LEFT = "(red-left (<= (snd red-cell) mid-c))"
_DESTINATION_OPPOSITE = "(new-cyan-c (if red-left (+ gc1 1) (- gc0 1)))"
_DESTINATION_SAME = "(new-cyan-c (if red-left (- gc0 1) (+ gc1 1)))"

_TRAIN_PROFILES = ("left_opposite", "center_opposite", "right_opposite")
_TEST_PROFILES = (
    "right_same_side",
    "left_opposite",
    "center_opposite",
    "right_opposite",
)
_ASPECTS = ("wide", "tall", "square", "wide", "tall", "square")
_DIMENSIONS = (
    (9, 11),
    (11, 9),
    (13, 13),
    (7, 7),
    (12, 14),
    (15, 10),
    (10, 16),
    (14, 12),
    (8, 15),
    (16, 9),
    (17, 17),
    (19, 13),
)


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return seed


def validate_setting(setting: Any) -> RuleSetting:
    if not isinstance(setting, RuleSetting):
        raise TypeError("setting must be a RuleSetting")
    if setting.stamp_relation not in STAMP_RELATIONS:
        raise ValueError(f"stamp_relation must be one of {STAMP_RELATIONS}")
    if setting.midpoint_side not in MIDPOINT_SIDES:
        raise ValueError(f"midpoint_side must be one of {MIDPOINT_SIDES}")
    return setting


def setting_key(setting: RuleSetting) -> str:
    setting = validate_setting(setting)
    return f"{setting.stamp_relation}__midpoint-{setting.midpoint_side}"


def choose_setting(seed: int) -> RuleSetting:
    """Choose one hidden setting deterministically for the complete episode."""
    seed = _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}|{PROTOTYPE_VERSION}|episode-setting|{seed}".encode()
    ).digest()
    return SETTINGS[int.from_bytes(digest[:8], "big") % len(SETTINGS)]


@lru_cache(maxsize=1)
def canonical_program() -> str:
    root = find_root(__file__)
    matches: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one canonical record for {TASK_ID}, found {len(matches)}"
        )
    return matches[0]


def _replace_once(source: str, old: str, new: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"canonical rule drift: expected one {old!r}, found {count}")
    return source.replace(old, new, 1)


def program_for(setting: RuleSetting = DEFAULT_SETTING) -> str:
    """Return the exact Racket program for one proposed setting.

    The canonical default is returned untouched.  Each non-default program is
    derived by one checked local branch replacement per changed parameter.
    """
    setting = validate_setting(setting)
    source = canonical_program()
    if setting.midpoint_side == "left":
        source = _replace_once(source, _RED_LEFT_CANONICAL, _RED_LEFT_MIDPOINT_LEFT)
    elif source.count(_RED_LEFT_CANONICAL) != 1:
        raise RuntimeError("canonical midpoint branch drifted")
    if setting.stamp_relation == "same":
        source = _replace_once(source, _DESTINATION_OPPOSITE, _DESTINATION_SAME)
    elif source.count(_DESTINATION_OPPOSITE) != 1:
        raise RuntimeError("canonical destination branch drifted")
    return source


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    result: list[list[int]] = []
    for row in grid:
        if not isinstance(row, list) or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid values must be exact ARC integers 0..9")
        result.append(list(row))
    if len(result) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30")
    return result


def analyze_scene(grid: Any) -> dict[str, Any]:
    """Independently recover the task's rectangle and marker roles."""
    original = _coerce_grid(grid)
    height, width = len(original), len(original[0])
    palette = {value for row in original for value in row}
    if palette != {2, 5, 7, 8}:
        raise ValueError(f"palette must be exactly {{2,5,7,8}}, got {sorted(palette)}")

    by_color = {
        color: [
            (row, col)
            for row in range(height)
            for col in range(width)
            if original[row][col] == color
        ]
        for color in (2, 5, 8)
    }
    if len(by_color[2]) != 1 or len(by_color[8]) != 1:
        raise ValueError("scene needs exactly one red and one cyan marker")
    if not by_color[5]:
        raise ValueError("scene needs a gray rectangle")

    red = by_color[2][0]
    cyan = by_color[8][0]
    gray = by_color[5]
    top = min(row for row, _ in gray)
    bottom = max(row for row, _ in gray)
    left = min(col for _, col in gray)
    right = max(col for _, col in gray)
    rectangle = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }
    if set(gray) != rectangle:
        raise ValueError("gray cells must form one solid rectangle")
    if bottom != height - 1:
        raise ValueError("gray rectangle must be bottom anchored")
    if right - left + 1 < 3:
        raise ValueError("gray rectangle must be at least three columns wide")
    for name, marker in (("red", red), ("cyan", cyan)):
        if not (marker[0] < top and left <= marker[1] <= right):
            raise ValueError(f"{name} marker must be above and within rectangle span")
    expected_background = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in rectangle and (row, col) not in {red, cyan}
    }
    if any(original[row][col] != 7 for row, col in expected_background):
        raise ValueError("all other cells must be background 7")

    return {
        "grid": original,
        "height": height,
        "width": width,
        "rect": (top, bottom, left, right),
        "red": red,
        "cyan": cyan,
        "midpoint": (left + right) // 2,
    }


def apply_setting(grid: Any, setting: RuleSetting = DEFAULT_SETTING) -> list[list[int]]:
    """Independent Python mirror for tests and Racket parity checks."""
    setting = validate_setting(setting)
    facts = analyze_scene(grid)
    output = [row[:] for row in facts["grid"]]
    red_row, red_col = facts["red"]
    cyan_row, cyan_col = facts["cyan"]
    _top, bottom, left, right = facts["rect"]
    midpoint = facts["midpoint"]

    if setting.midpoint_side == "right":
        red_left = red_col < midpoint
    else:
        red_left = red_col <= midpoint

    if setting.stamp_relation == "opposite":
        destination = right + 1 if red_left else left - 1
    else:
        destination = left - 1 if red_left else right + 1
    if not 0 <= destination < facts["width"]:
        raise ValueError("setting selects an out-of-bounds stamp destination")

    output[red_row][red_col] = 7
    output[cyan_row][cyan_col] = 2
    output[bottom][destination] = 8
    return output


def _input_spec(split: str, index: int) -> tuple[str, int, int, str]:
    if split == "train":
        profile = _TRAIN_PROFILES[index % len(_TRAIN_PROFILES)]
        offset = index
    elif split == "test":
        profile = _TEST_PROFILES[index % len(_TEST_PROFILES)]
        offset = index + len(_TRAIN_PROFILES)
    else:
        raise ValueError(f"unknown split: {split}")
    height, width = _DIMENSIONS[offset % len(_DIMENSIONS)]
    aspect = _ASPECTS[offset % len(_ASPECTS)]
    return profile, height, width, aspect


def _candidate_seed(seed: int, split: str, index: int, attempt: int) -> int:
    payload = (
        f"{TASK_ID}|{PROTOTYPE_VERSION}|input|{seed}|{split}|{index}|{attempt}"
    ).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _build_input(
    generator: Any,
    *,
    seed: int,
    split: str,
    index: int,
    used: set[str],
) -> tuple[list[list[int]], dict[str, Any]]:
    profile, height, width, aspect = _input_spec(split, index)
    for attempt in range(512):
        draw_seed = _candidate_seed(seed, split, index, attempt)
        grid = generator.generate(
            draw_seed,
            index,
            grid_h=height,
            grid_w=width,
            rect_aspect=aspect,
            scene_profile=profile,
        )
        facts = analyze_scene(grid)
        _top, _bottom, left, right = facts["rect"]
        if left == 0 or right == width - 1:
            continue
        encoded = json.dumps(grid, separators=(",", ":"))
        if encoded in used:
            continue
        observed = generator.observe_overrides(grid)
        if observed.get("scene_profile") != profile:
            raise RuntimeError(
                f"selected generator realized {observed.get('scene_profile')} for {profile}"
            )
        used.add(encoded)
        return grid, {
            "split": split,
            "index": index,
            "profile": profile,
            "grid_h": height,
            "grid_w": width,
            "rect_aspect": aspect,
            "draw_seed": draw_seed,
            "attempt": attempt,
        }
    raise RuntimeError(
        f"could not draw a unique bilateral-margin {split}[{index}] after 512 attempts"
    )


def build_episode(
    seed: int,
    *,
    setting: RuleSetting | None = None,
    n_train: int = MIN_TRAIN,
    n_test: int = MIN_TEST,
) -> dict[str, Any]:
    """Build one complete episode with a single fixed hidden rule setting."""
    seed = _validate_seed(seed)
    if type(n_train) is not int or n_train < MIN_TRAIN:
        raise ValueError(f"n_train must be an integer >= {MIN_TRAIN}")
    if type(n_test) is not int or n_test < MIN_TEST:
        raise ValueError(f"n_test must be an integer >= {MIN_TEST}")
    selected = choose_setting(seed) if setting is None else validate_setting(setting)

    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    used: set[str] = set()
    splits: dict[str, list[dict[str, Any]]] = {"train": [], "test": []}
    for split, count in (("train", n_train), ("test", n_test)):
        for index in range(count):
            grid, sampling = _build_input(
                generator,
                seed=seed,
                split=split,
                index=index,
                used=used,
            )
            splits[split].append(
                {
                    "input": grid,
                    "output": apply_setting(grid, selected),
                    "sampling": sampling,
                }
            )

    return {
        "schema": "0f7d80015d9d-parametric-episode-v1",
        "scope": "proposed task-local prototype; not selected canonical execution",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": {
            "stamp_relation": selected.stamp_relation,
            "midpoint_side": selected.midpoint_side,
        },
        "program": program_for(selected),
        "generator_source": str(source_path),
        "generator_sha256": source_sha256,
        "train": splits["train"],
        "test": splits["test"],
    }


def setting_from_parameters(parameters: Any) -> RuleSetting:
    if not isinstance(parameters, dict):
        raise TypeError("parameters must be a mapping")
    return validate_setting(
        RuleSetting(parameters.get("stamp_relation"), parameters.get("midpoint_side"))
    )


def setting_survivors(demos: Iterable[dict[str, Any]]) -> list[RuleSetting]:
    demos = list(demos)
    survivors: list[RuleSetting] = []
    for candidate in SETTINGS:
        try:
            if all(
                isinstance(pair, dict)
                and pair.get("output") == apply_setting(pair.get("input"), candidate)
                for pair in demos
            ):
                survivors.append(candidate)
        except (TypeError, ValueError):
            continue
    return survivors


def episode_errors(episode: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(episode, dict):
        return ["episode must be a mapping"]
    try:
        selected = setting_from_parameters(episode.get("parameters"))
    except (TypeError, ValueError) as exc:
        return [f"invalid parameters: {exc}"]
    if episode.get("program") != program_for(selected):
        errors.append("program does not match the fixed setting")

    root = find_root(__file__)
    generator, _source_path, current_sha = load_selected_generator(TASK_ID, root=root)
    if episode.get("generator_sha256") != current_sha:
        errors.append("selected generator source hash drifted")

    seen: set[str] = set()
    for split, minimum in (("train", MIN_TRAIN), ("test", MIN_TEST)):
        pairs = episode.get(split)
        if not isinstance(pairs, list) or len(pairs) < minimum:
            errors.append(f"{split} must contain at least {minimum} pairs")
            continue
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                errors.append(f"{split}[{index}] lacks input/output")
                continue
            try:
                facts = analyze_scene(pair["input"])
                grammar_errors = generator.self_check(pair["input"])
                if grammar_errors:
                    errors.append(f"{split}[{index}] outside selected grammar: {grammar_errors}")
                _top, _bottom, left, right = facts["rect"]
                if left == 0 or right == facts["width"] - 1:
                    errors.append(f"{split}[{index}] lacks bilateral destination margins")
                expected = apply_setting(pair["input"], selected)
                if pair["output"] != expected:
                    errors.append(f"{split}[{index}] label mismatches fixed setting")
                encoded = json.dumps(pair["input"], separators=(",", ":"))
                if encoded in seen:
                    errors.append(f"{split}[{index}] duplicates another episode input")
                seen.add(encoded)
            except (TypeError, ValueError) as exc:
                errors.append(f"{split}[{index}] invalid: {exc}")

    train = episode.get("train")
    if isinstance(train, list) and len(train) >= MIN_TRAIN:
        survivors = setting_survivors(train)
        if survivors != [selected]:
            errors.append(
                "demonstrations do not uniquely identify the fixed setting: "
                + ", ".join(setting_key(item) for item in survivors)
            )
    return errors


def public_projection(episode: dict[str, Any]) -> dict[str, Any]:
    """Return only visible demonstrations and query inputs.

    This projection intentionally ignores all hidden metadata so its content ID
    cannot change when only seed, setting, program, or private query labels do.
    """
    if not isinstance(episode, dict):
        raise ValueError("episode must be a mapping")
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not train or not isinstance(test, list) or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    try:
        return {
            "train": [
                {
                    "input": deepcopy(pair["input"]),
                    "output": deepcopy(pair["output"]),
                }
                for pair in train
            ],
            "test": [{"input": deepcopy(pair["input"])} for pair in test],
        }
    except (KeyError, TypeError) as exc:
        raise ValueError("visible pairs are malformed") from exc


def public_bytes(episode: dict[str, Any]) -> bytes:
    """Return the exact shared serialization of the model-visible challenge."""
    return public_challenge_bytes(public_projection(episode))


def public_identifier(episode: dict[str, Any]) -> str:
    return hashlib.sha256(public_bytes(episode)).hexdigest()


def plan_public_batch(
    episodes: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Preflight and sort a complete public batch before any writer mutates disk."""
    rows: list[dict[str, Any]] = []
    by_id: dict[str, bytes] = {}
    for episode in episodes:
        payload = public_bytes(episode)
        public_id = hashlib.sha256(payload).hexdigest()
        previous = by_id.get(public_id)
        if previous is not None:
            if previous == payload:
                raise ValueError(f"duplicate public challenge: {public_id}")
            raise ValueError(f"public challenge ID collision: {public_id}")
        by_id[public_id] = payload
        rows.append(
            {
                "public_id": public_id,
                "public_bytes": payload,
                "episode": episode,
            }
        )
    if not rows:
        raise ValueError("public batch must contain at least one episode")
    rows.sort(key=lambda row: row["public_id"])
    return rows
