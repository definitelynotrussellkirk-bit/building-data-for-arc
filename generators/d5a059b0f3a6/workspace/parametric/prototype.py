"""Task-local episode-level mirror-mode prototype for d5a059b0f3a6.

The production generator and canonical authority remain fixed.  This proposed
prototype chooses one hidden rule for the complete episode:

``single_axis`` (canonical/default)
    Infer the missing axis independently in each corner-delimited frame and
    mirror the enclosed blue seed only across that axis.

``both_axes`` (proposed)
    Preserve the same frame detection, object roles and distractor removal, but
    complete the seed across both frame axes (including the 180-degree orbit).

Each episode uses three demonstrations and four distinct queries by default.
Every retained input is chosen so the two settings yield different labels.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from typing import Any

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "d5a059b0f3a6"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "mirror_mode"
ALLOWED_SETTINGS = ("single_axis", "both_axes")
DEFAULT_SETTING = "single_axis"
CANONICAL_RULE_HASH = "77f0ca66f33e"
DEFAULT_N_TRAIN = 3
DEFAULT_N_TEST = 4
_BANDS = ("easy", "medium", "hard", "medium", "hard", "easy", "medium")
_UNSET = object()

_OLD_RULE_FRAGMENT = (
    "(mirrored (if (or leftonly rightonly) "
    "(map (lambda (p) (list (first p) (- cc (second p)))) seed) "
    "(map (lambda (p) (list (- cr (first p)) (second p))) seed)))) "
    "(append seed mirrored)"
)
_BOTH_AXES_RULE_FRAGMENT = (
    "(horizontal (map (lambda (p) (list (first p) (- cc (second p)))) seed)) "
    "(vertical (map (lambda (p) (list (- cr (first p)) (second p))) seed)) "
    "(diagonal (map (lambda (p) (list (- cr (first p)) "
    "(- cc (second p)))) seed))) "
    "(append seed horizontal vertical diagonal)"
)


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return seed


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer (not bool)")
    return value


def _validate_setting(setting: Any) -> str:
    if type(setting) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if setting not in ALLOWED_SETTINGS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}, got {setting!r}"
        )
    return setting


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


@lru_cache(maxsize=1)
def _canonical_program() -> str:
    root = find_root(__file__)
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        source = row["program_solution"]
        digest = _normalized_rule_hash(source)
        if digest != CANONICAL_RULE_HASH:
            raise RuntimeError(
                f"canonical rule hash drift: {digest} != {CANONICAL_RULE_HASH}"
            )
        return source
    raise RuntimeError(f"canonical program missing for {TASK_ID}")


@lru_cache(maxsize=1)
def _selected_generator():
    root = find_root(__file__)
    return load_selected_generator(TASK_ID, root=root)


def choose_setting(seed: int) -> str:
    """Choose one deterministic hidden setting for the entire episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}|{PARAMETER_NAME}|{PROTOTYPE_VERSION}|{seed}".encode()
    ).digest()
    return ALLOWED_SETTINGS[digest[0] % len(ALLOWED_SETTINGS)]


def program_for(setting: str) -> str:
    """Return exact Racket source for one bounded prototype setting."""
    setting = _validate_setting(setting)
    source = _canonical_program()
    if setting == DEFAULT_SETTING:
        return source
    if source.count(_OLD_RULE_FRAGMENT) != 1:
        raise RuntimeError(
            "canonical rule no longer contains the pinned mirror fragment"
        )
    return source.replace(
        _OLD_RULE_FRAGMENT,
        _BOTH_AXES_RULE_FRAGMENT,
        1,
    )


def grid_digest(grid: Any) -> str:
    payload = json.dumps(
        grid, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _validated_analysis(grid):
    generator, _, _ = _selected_generator()
    before = deepcopy(grid)
    reasons = generator.self_check(grid)
    if grid != before:
        raise RuntimeError("selected generator self_check mutated the input")
    if reasons:
        raise ValueError("input is outside the selected generator grammar: " + "; ".join(reasons))
    return generator, generator._analyze(grid)


def solve_setting(grid, setting: str):
    """Pure Python authoring mirror for one prototype setting."""
    setting = _validate_setting(setting)
    generator, analysis = _validated_analysis(grid)
    if setting == "single_axis":
        before = deepcopy(grid)
        output = generator.solve_python(grid)
        if grid != before:
            raise RuntimeError("selected generator solve_python mutated the input")
        return output

    height = len(grid)
    width = len(grid[0])
    frame_color = analysis["frame_color"]
    output = [
        [frame_color if value == frame_color else 0 for value in row]
        for row in grid
    ]
    blue = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    }
    for row1, col1, row2, col2 in analysis["frames"]:
        center_row_twice = row1 + row2
        center_col_twice = col1 + col2
        seed = {
            point
            for point in blue
            if row1 <= point[0] <= row2 and col1 <= point[1] <= col2
        }
        orbit = set(seed)
        orbit.update((row, center_col_twice - col) for row, col in seed)
        orbit.update((center_row_twice - row, col) for row, col in seed)
        orbit.update(
            (center_row_twice - row, center_col_twice - col)
            for row, col in seed
        )
        for row, col in orbit:
            output[row][col] = 1
    return output


def _pair_inputs(seed: int, count: int):
    generator, _, _ = _selected_generator()
    accepted = []
    seen = set()
    sample_index = 0
    max_attempts = max(64, count * 16)
    while len(accepted) < count and sample_index < max_attempts:
        difficulty = _BANDS[len(accepted) % len(_BANDS)]
        grid = generator.generate(seed, sample_index, difficulty=difficulty)
        digest = grid_digest(grid)
        candidate_index = sample_index
        sample_index += 1
        if digest in seen:
            continue
        outputs = {
            setting: solve_setting(grid, setting)
            for setting in ALLOWED_SETTINGS
        }
        if outputs[ALLOWED_SETTINGS[0]] == outputs[ALLOWED_SETTINGS[1]]:
            continue
        seen.add(digest)
        accepted.append(
            {
                "grid": grid,
                "outputs": outputs,
                "sampling": {
                    "seed": seed,
                    "sample_index": candidate_index,
                    "difficulty": difficulty,
                    "scene_profile": generator.observe_overrides(grid)["scene_profile"],
                },
            }
        )
    if len(accepted) != count:
        raise RuntimeError(
            f"only found {len(accepted)}/{count} distinct setting-sensitive inputs "
            f"within {max_attempts} attempts"
        )
    return accepted


def build_episode(
    seed: int,
    *,
    setting: object = _UNSET,
    n_train: int = DEFAULT_N_TRAIN,
    n_test: int = DEFAULT_N_TEST,
):
    """Build one complete fixed-setting episode with separate pair counts."""
    seed = _validate_seed(seed)
    n_train = _validate_count("n_train", n_train)
    n_test = _validate_count("n_test", n_test)
    selected = choose_setting(seed) if setting is _UNSET else _validate_setting(setting)
    generator, source_path, source_sha256 = _selected_generator()
    root = find_root(__file__)
    samples = _pair_inputs(seed, n_train + n_test)
    pairs = [
        {
            "input": deepcopy(sample["grid"]),
            "output": deepcopy(sample["outputs"][selected]),
            "setting": selected,
            "sampling": deepcopy(sample["sampling"]),
        }
        for sample in samples
    ]
    episode = {
        "schema": "d5a059b0f3a6-parametric-mirror-mode-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {PARAMETER_NAME: selected},
        "program": program_for(selected),
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "train": pairs[:n_train],
        "test": pairs[n_train:],
    }
    errors = episode_errors(episode)
    if errors:
        raise RuntimeError("constructed invalid prototype episode: " + "; ".join(errors))
    # Referencing the loaded module prevents linters from mistaking the load for
    # dead provenance work; the hash is checked in the verifier.
    if generator.RULE_HASH != CANONICAL_RULE_HASH:
        raise RuntimeError("selected generator authority pin disagrees with prototype")
    return episode


def episode_errors(episode: Any) -> list[str]:
    """Validate fixed setting, labels, uniqueness and teaching sufficiency."""
    if not isinstance(episode, dict):
        return ["episode must be a mapping"]
    parameter = episode.get("parameter")
    if not isinstance(parameter, dict) or PARAMETER_NAME not in parameter:
        return [f"episode must declare parameter {PARAMETER_NAME!r}"]
    try:
        selected = _validate_setting(parameter[PARAMETER_NAME])
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    if episode.get("program") != program_for(selected):
        return ["episode program does not match selected setting"]
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not train:
        return ["episode needs at least one demonstration"]
    if not isinstance(test, list) or not test:
        return ["episode needs at least one query"]

    rival = next(value for value in ALLOWED_SETTINGS if value != selected)
    errors = []
    seen = set()
    demo_refutes = False
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if pair.get("setting") != selected:
                errors.append(f"{split_name}[{index}] setting drift")
                continue
            grid = pair.get("input")
            digest = grid_digest(grid)
            if digest in seen:
                errors.append(f"duplicate input at {split_name}[{index}]")
            seen.add(digest)
            try:
                expected = solve_setting(grid, selected)
                rival_output = solve_setting(grid, rival)
            except Exception as exc:
                errors.append(f"{split_name}[{index}] invalid input: {exc}")
                continue
            if pair.get("output") != expected:
                errors.append(f"{split_name}[{index}] label mismatch")
            differs = rival_output != expected
            if split_name == "train":
                demo_refutes = demo_refutes or differs
            elif not differs:
                errors.append(f"test[{index}] is not setting-sensitive")
    if not demo_refutes:
        errors.append("demonstrations do not distinguish the rival setting")
    return errors


def public_challenge(episode):
    """Return only visible demos and answer-free query inputs."""
    return {
        "train": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def public_identifier(challenge) -> str:
    """Opaque filename derived solely from public visible challenge content."""
    payload = json.dumps(
        challenge, sort_keys=True, separators=(",", ":")
    ).encode()
    return f"challenge-{hashlib.sha256(payload).hexdigest()[:16]}.json"
