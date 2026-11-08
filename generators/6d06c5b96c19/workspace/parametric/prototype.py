"""Task-local prototype for an episode-level row-shift direction parameter.

This proposal is intentionally separate from the selected production generator
and canonical authority.  One hidden ``shift_direction`` value is fixed for an
entire episode:

``down``
    Canonical/default behavior: remove column 0 and rotate payload rows down by
    the red marker's zero-based row index.
``up``
    Nearby alternative: remove column 0 and rotate payload rows up by that row
    index.

The demonstrations include direction-sensitive marker rows, so the setting is
learnable before the held-out query.  Inputs are identical across settings.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Sequence

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "6d06c5b96c19"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "shift_direction"
ALLOWED_SETTINGS = ("down", "up")
DEFAULT_SETTING = "down"
CANONICAL_RULE_HASH = "9b7b9cf11c40"
_SAMPLE_INDICES = (0, 2, 3, 6, 7)
_DIFFICULTIES = ("easy", "medium", "hard", "medium", "hard")
_UNSET = object()
_DOWN_FORM = "(down-shift (remainder (- h red-row) h))"
_UP_FORM = "(down-shift red-row)"


def public_filename(challenge):
    """Hash only visible inputs and demonstration labels, never private metadata."""
    visible = {"train": [{"input": p["input"], "output": p["output"]} for p in challenge["train"]],
               "test": [{"input": p["input"]} for p in challenge["test"]]}
    raw = json.dumps(visible, sort_keys=True, separators=(",", ":")).encode()
    return "challenge-" + hashlib.sha256(raw).hexdigest() + ".json"


def _require_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    return seed


def _require_setting(setting: Any) -> str:
    if type(setting) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if setting not in ALLOWED_SETTINGS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}, got {setting!r}"
        )
    return setting


def _canonical_program() -> str:
    root = find_root(__file__)
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        source = row["program_solution"]
        normalized = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        if normalized != CANONICAL_RULE_HASH:
            raise RuntimeError(
                f"canonical rule hash drift: expected {CANONICAL_RULE_HASH}, got {normalized}"
            )
        return source
    raise RuntimeError(f"canonical program missing for {TASK_ID}")


def choose_setting(seed: int) -> str:
    """Choose one deterministic hidden setting for the complete episode."""
    _require_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}|{PARAMETER_NAME}|v1|{seed}".encode()
    ).digest()
    return ALLOWED_SETTINGS[digest[0] % len(ALLOWED_SETTINGS)]


def program_for(setting: str) -> str:
    """Return exact canonical text for ``down`` and a one-site ``up`` variant."""
    setting = _require_setting(setting)
    source = _canonical_program()
    if setting == DEFAULT_SETTING:
        return source
    if source.count(_DOWN_FORM) != 1:
        raise RuntimeError("canonical program no longer has one expected shift binding")
    return source.replace(_DOWN_FORM, _UP_FORM, 1)


def _validated_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty sequence")
    if not isinstance(grid[0], (list, tuple)) or len(grid[0]) < 2:
        raise ValueError("grid rows must contain an instruction and payload")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be literal ARC colors 0..9")
    red_rows = [index for index, row in enumerate(grid) if row[0] == 2]
    if len(red_rows) != 1:
        raise ValueError("instruction column must contain exactly one red marker")
    return [list(row) for row in grid]


def apply_python(grid: Sequence[Sequence[int]], setting: str) -> list[list[int]]:
    """Independent Python mirror for the bounded parameter family."""
    setting = _require_setting(setting)
    source = _validated_grid(grid)
    payload = [row[1:] for row in source]
    marker = next(index for index, row in enumerate(source) if row[0] == 2)
    shift = marker % len(payload)
    if shift == 0:
        return payload
    if setting == "down":
        return payload[-shift:] + payload[:-shift]
    return payload[shift:] + payload[:shift]


def build_episode(seed: int, *, setting: object = _UNSET) -> dict[str, Any]:
    """Build four demonstrations and one query under one fixed hidden setting."""
    seed = _require_seed(seed)
    selected = choose_setting(seed) if setting is _UNSET else _require_setting(setting)
    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)

    pairs: list[dict[str, Any]] = []
    for sample_index, difficulty in zip(_SAMPLE_INDICES, _DIFFICULTIES):
        grid = generator.generate(seed, sample_index, difficulty=difficulty)
        pairs.append(
            {
                "input": grid,
                "output": apply_python(grid, selected),
                "sampling": {
                    "seed": seed,
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                },
            }
        )

    episode = {
        "schema": "6d06c5b96c19-parametric-shift-direction-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {PARAMETER_NAME: selected},
        "program": program_for(selected),
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "train": pairs[:4],
        "test": pairs[4:],
    }
    errors = episode_errors(episode)
    if errors:
        raise RuntimeError("constructed invalid prototype episode: " + "; ".join(errors))
    return episode


def episode_errors(episode: Any) -> list[str]:
    """Validate episode constancy, labels, and learnability from demonstrations."""
    if not isinstance(episode, dict):
        return ["episode must be a mapping"]
    parameter = episode.get("parameter")
    if not isinstance(parameter, dict) or PARAMETER_NAME not in parameter:
        return [f"episode must declare parameter {PARAMETER_NAME!r}"]
    try:
        selected = _require_setting(parameter[PARAMETER_NAME])
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    if episode.get("program") != program_for(selected):
        return ["episode program does not match its selected parameter"]

    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not train:
        return ["episode needs at least one training pair"]
    if not isinstance(test, list) or not test:
        return ["episode needs at least one test pair"]

    rival = "up" if selected == "down" else "down"
    errors: list[str] = []
    train_distinguishes = False
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                errors.append(f"{split_name}[{index}] must contain input and output")
                continue
            try:
                expected = apply_python(pair["input"], selected)
                rival_output = apply_python(pair["input"], rival)
            except (TypeError, ValueError) as exc:
                errors.append(f"{split_name}[{index}] invalid: {exc}")
                continue
            if pair["output"] != expected:
                errors.append(f"{split_name}[{index}] output disagrees with selected setting")
            differs = rival_output != expected
            if split_name == "train":
                train_distinguishes = train_distinguishes or differs
            elif not differs:
                errors.append(f"{split_name}[{index}] is not direction-sensitive")
    if not train_distinguishes:
        errors.append("demonstrations do not distinguish down from up")
    return errors


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove rule metadata, sampling metadata, and the query answer."""
    errors = episode_errors(episode)
    if errors:
        raise ValueError("invalid episode: " + "; ".join(errors))
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }
