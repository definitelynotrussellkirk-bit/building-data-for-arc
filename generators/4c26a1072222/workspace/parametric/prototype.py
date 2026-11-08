"""Task-local episode-fixed forward/inverse rule variants for ``4c26a1072222``.

The canonical setting infers one D4 transform and one functional color map from
A→B in each band, then applies that same transform and map to C.  This proposed
prototype varies one nearby semantic choice once per episode:

* ``forward``: apply the inferred transform to C (the registered canonical rule);
* ``inverse``: apply the inverse of the inferred transform to C while retaining
  the same A→B color map.

Only quarter-turn transforms differ between the settings.  Production generation
and canonical authority remain unchanged, and the default setting returns the
registered canonical Racket source byte-for-byte.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from typing import Any, Iterable

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_id,
)


TASK_ID = "4c26a1072222"
PROTOTYPE_VERSION = "1.0.0"
DEFAULT_SETTING = "forward"
SETTINGS = (DEFAULT_SETTING, "inverse")
MIN_TRAIN = 4
MIN_TEST = 4

_CANONICAL_C_BINDING = "(v (c-val gr t lr c))"
_INVERSE_C_BINDING = (
    "(v (c-val gr (cond ((= t 4) 5) ((= t 5) 4) (else t)) lr c))"
)
_INVERSE_TRANSFORM = {0: 0, 1: 1, 2: 2, 3: 3, 4: 5, 5: 4, 6: 6, 7: 7}
_DIFFICULTIES = ("easy", "medium", "hard", None)
_QUARTER_TURNS = ("rotate_cw", "rotate_ccw")


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return seed


def validate_setting(setting: Any) -> str:
    if type(setting) is not str:
        raise TypeError("application_direction must be a string")
    if setting not in SETTINGS:
        raise ValueError(f"application_direction must be one of {SETTINGS}")
    return setting


def setting_key(setting: str) -> str:
    return validate_setting(setting)


def choose_setting(seed: int) -> str:
    """Choose one hidden application direction for the complete episode."""
    seed = _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}|{PROTOTYPE_VERSION}|episode-setting|{seed}".encode()
    ).digest()
    return SETTINGS[int.from_bytes(digest[:8], "big") % len(SETTINGS)]


@lru_cache(maxsize=1)
def canonical_program() -> str:
    root = find_root(__file__)
    programs: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise RuntimeError(
            f"expected one unique canonical program for {TASK_ID}, found {len(programs)}"
        )
    return programs.pop()


def _replace_once(source: str, old: str, new: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"canonical rule drift: expected one {old!r}, found {count}")
    return source.replace(old, new, 1)


def program_for(setting: str = DEFAULT_SETTING) -> str:
    """Return exact Racket source for one proposed application direction."""
    setting = validate_setting(setting)
    source = canonical_program()
    if setting == DEFAULT_SETTING:
        if source.count(_CANONICAL_C_BINDING) != 1:
            raise RuntimeError("canonical C-transform binding drifted")
        return source
    return _replace_once(source, _CANONICAL_C_BINDING, _INVERSE_C_BINDING)


@lru_cache(maxsize=1)
def _selected_generator():
    root = find_root(__file__)
    return load_selected_generator(TASK_ID, root=root)


def apply_setting(grid: Any, setting: str = DEFAULT_SETTING) -> list[list[int]]:
    """Apply one direction using the selected generator's exact band analysis."""
    setting = validate_setting(setting)
    generator, _source_path, _source_sha256 = _selected_generator()
    info, errors = generator._analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))

    output = [[0 for _ in range(2)] for _ in range(info["height"])]
    for band in info["bands"]:
        transform = band["transform"]
        if setting == "inverse":
            transform = _INVERSE_TRANSFORM[transform]
        generator._render_band(output, band, transform, band["mapping"])
    return output


def _candidate_seed(seed: int, split: str, index: int, attempt: int) -> int:
    payload = (
        f"{TASK_ID}|{PROTOTYPE_VERSION}|input|{seed}|{split}|{index}|{attempt}"
    ).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _input_spec(split: str, index: int) -> dict[str, Any]:
    if split == "train":
        offset = index
    elif split == "test":
        offset = index + 17
    else:
        raise ValueError(f"unknown split: {split}")
    return {
        "sample_index": offset,
        "n_bands": 3 + (offset % 2),
        "first_transform": _QUARTER_TURNS[offset % len(_QUARTER_TURNS)],
        "difficulty": _DIFFICULTIES[offset % len(_DIFFICULTIES)],
    }


def _build_input(
    generator: Any,
    *,
    seed: int,
    split: str,
    index: int,
    used: set[str],
) -> tuple[list[list[int]], dict[str, Any]]:
    spec = _input_spec(split, index)
    for attempt in range(512):
        draw_seed = _candidate_seed(seed, split, index, attempt)
        grid = generator.generate(
            draw_seed,
            spec["sample_index"],
            difficulty=spec["difficulty"],
            n_bands=spec["n_bands"],
            first_transform=spec["first_transform"],
        )
        encoded = json.dumps(grid, separators=(",", ":"))
        if encoded in used:
            continue
        if generator.self_check(grid, difficulty=spec["difficulty"]):
            continue
        if apply_setting(grid, "forward") == apply_setting(grid, "inverse"):
            continue
        observed = generator.observe_overrides(grid)
        if observed != {
            "n_bands": spec["n_bands"],
            "first_transform": spec["first_transform"],
        }:
            raise RuntimeError(
                f"selected generator realized {observed}, expected input spec {spec}"
            )
        used.add(encoded)
        return grid, {
            "split": split,
            "index": index,
            "draw_seed": draw_seed,
            "attempt": attempt,
            **spec,
        }
    raise RuntimeError(
        f"could not draw a unique direction-distinguishing {split}[{index}] "
        "after 512 attempts"
    )


def build_episode(
    seed: int,
    *,
    application_direction: str | None = None,
    n_train: int = MIN_TRAIN,
    n_test: int = MIN_TEST,
) -> dict[str, Any]:
    """Build an episode with one fixed setting, four demos, and four queries."""
    seed = _validate_seed(seed)
    if type(n_train) is not int or n_train < MIN_TRAIN:
        raise ValueError(f"n_train must be an integer >= {MIN_TRAIN}")
    if type(n_test) is not int or n_test < MIN_TEST:
        raise ValueError(f"n_test must be an integer >= {MIN_TEST}")
    selected = (
        choose_setting(seed)
        if application_direction is None
        else validate_setting(application_direction)
    )

    generator, source_path, source_sha256 = _selected_generator()
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
        "schema": "4c26a1072222-parametric-episode-v1",
        "scope": "proposed task-local prototype; not selected canonical execution",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": {"application_direction": selected},
        "program": program_for(selected),
        "generator_source": str(source_path),
        "generator_sha256": source_sha256,
        "train": splits["train"],
        "test": splits["test"],
    }


def setting_from_parameters(parameters: Any) -> str:
    if not isinstance(parameters, dict):
        raise TypeError("parameters must be a mapping")
    return validate_setting(parameters.get("application_direction"))


def setting_survivors(demos: Iterable[dict[str, Any]]) -> list[str]:
    demos = list(demos)
    survivors: list[str] = []
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

    generator, _source_path, current_sha = _selected_generator()
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
                grammar_errors = generator.self_check(pair["input"])
                if grammar_errors:
                    errors.append(
                        f"{split}[{index}] outside selected grammar: {grammar_errors}"
                    )
                expected = apply_setting(pair["input"], selected)
                if pair["output"] != expected:
                    errors.append(f"{split}[{index}] label mismatches fixed setting")
                if apply_setting(pair["input"], "forward") == apply_setting(
                    pair["input"], "inverse"
                ):
                    errors.append(f"{split}[{index}] does not distinguish settings")
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
                + ", ".join(survivors)
            )
    return errors


def public_projection(episode: dict[str, Any]) -> dict[str, Any]:
    """Return only visible demonstrations and query inputs."""
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


def public_identifier(episode: dict[str, Any]) -> str:
    return public_challenge_id(public_projection(episode))
