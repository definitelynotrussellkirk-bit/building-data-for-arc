"""Task-local episode-level identity-corner prototype for 90640e0e6314.

The selected production generator and canonical Racket authority remain fixed.
This proposed prototype chooses one hidden corner once per complete episode.  The
unchanged input occupies that output quadrant; reflecting across the horizontal
and vertical seams determines the other three quadrants.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from typing import Any

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "90640e0e6314"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "identity_corner"
ALLOWED_SETTINGS = (
    "top_left",
    "top_right",
    "bottom_left",
    "bottom_right",
)
DEFAULT_SETTING = "bottom_right"
CANONICAL_RULE_HASH = "370706e398d4"
DEFAULT_N_TRAIN = 3
DEFAULT_N_TEST = 4

_SETTING_COORDINATES = {
    "top_left": (0, 0),
    "top_right": (0, 1),
    "bottom_left": (1, 0),
    "bottom_right": (1, 1),
}
_BANDS = {
    "train": ("easy", "medium", "hard"),
    "test": ("medium", "hard", "easy", "medium"),
}
_UNSET = object()


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (not bool)")
    if value < 1:
        raise ValueError(f"{name} must be positive")
    if value > 64:
        raise ValueError(f"{name} must be at most 64 for this bounded prototype")
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
    generator, source_path, source_sha256 = load_selected_generator(
        TASK_ID, root=root
    )
    if generator.RULE_HASH != CANONICAL_RULE_HASH:
        raise RuntimeError(
            "selected generator authority pin disagrees with the prototype"
        )
    return generator, source_path, source_sha256


def choose_setting(seed: int) -> str:
    """Choose one deterministic hidden setting for the complete episode."""
    seed = _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}|{PARAMETER_NAME}|{PROTOTYPE_VERSION}|{seed}".encode()
    ).digest()
    return ALLOWED_SETTINGS[digest[0] % len(ALLOWED_SETTINGS)]


def _coordinate_program(setting: str) -> str:
    anchor_row, anchor_col = _SETTING_COORDINATES[setting]
    if anchor_row == 0:
        row_expr = "(if (zero? qr) lr (- n 1 lr))"
    else:
        row_expr = "(if (zero? qr) (- n 1 lr) lr)"
    if anchor_col == 0:
        col_expr = "(if (zero? qc) lc (- n 1 lc))"
    else:
        col_expr = "(if (zero? qc) (- n 1 lc) lc)"
    return f"""(rule! (lambda (g)
         (let ((n (rows g)))
           (build-grid (* 2 n)
                       (* 2 n)
                       (r c)
                       (let ((qr (quotient r n))
                             (qc (quotient c n))
                             (lr (remainder r n))
                             (lc (remainder c n)))
                         (at g
                             {row_expr}
                             {col_expr}))))))"""


def program_for(setting: str) -> str:
    """Return exact executable Racket source for one bounded setting."""
    setting = _validate_setting(setting)
    if setting == DEFAULT_SETTING:
        return _canonical_program()
    return _coordinate_program(setting)


def grid_digest(grid: Any) -> str:
    payload = json.dumps(
        grid, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _validated_grid(grid: Any) -> list[list[int]]:
    generator, _, _ = _selected_generator()
    before = deepcopy(grid)
    reasons = generator.self_check(grid)
    if grid != before:
        raise RuntimeError("selected generator self_check mutated the input")
    if reasons:
        raise ValueError(
            "input is outside the selected generator grammar: " + "; ".join(reasons)
        )
    return grid


def _solve_valid_grid(grid: list[list[int]], setting: str) -> list[list[int]]:
    anchor_row, anchor_col = _SETTING_COORDINATES[setting]
    n = len(grid)
    output = [[0] * (2 * n) for _ in range(2 * n)]
    for row in range(2 * n):
        quadrant_row, local_row = divmod(row, n)
        source_row = (
            local_row
            if quadrant_row == anchor_row
            else n - 1 - local_row
        )
        for col in range(2 * n):
            quadrant_col, local_col = divmod(col, n)
            source_col = (
                local_col
                if quadrant_col == anchor_col
                else n - 1 - local_col
            )
            output[row][col] = grid[source_row][source_col]
    return output


def solve_setting(grid: Any, setting: str) -> list[list[int]]:
    """Pure Python parity mirror for one proposed identity-corner setting."""
    setting = _validate_setting(setting)
    validated = _validated_grid(grid)
    return _solve_valid_grid(validated, setting)


def _candidate_seed(seed: int, split: str, attempt: int) -> int:
    digest = hashlib.sha256(
        (
            f"{TASK_ID}|{PARAMETER_NAME}|{PROTOTYPE_VERSION}|input|"
            f"{seed}|{split}|{attempt}"
        ).encode()
    ).digest()
    return int.from_bytes(digest[:8], "big") & 0x7FFFFFFF


def _sample_split(seed: int, split: str, count: int) -> list[dict[str, Any]]:
    generator, _, _ = _selected_generator()
    accepted: list[dict[str, Any]] = []
    seen: set[str] = set()
    max_attempts = max(128, count * 32)
    for attempt in range(max_attempts):
        if len(accepted) == count:
            break
        difficulty = _BANDS[split][len(accepted) % len(_BANDS[split])]
        generator_seed = _candidate_seed(seed, split, attempt)
        sample_index = attempt + (0 if split == "train" else 1_000_000)
        grid = generator.generate(
            generator_seed,
            sample_index,
            difficulty=difficulty,
        )
        digest = grid_digest(grid)
        if digest in seen:
            continue
        reasons = generator.self_check(grid)
        if reasons:
            raise RuntimeError(
                "selected generator returned an invalid prototype input: "
                + "; ".join(reasons)
            )
        outputs = {
            setting: _solve_valid_grid(grid, setting)
            for setting in ALLOWED_SETTINGS
        }
        if len({grid_digest(value) for value in outputs.values()}) != len(
            ALLOWED_SETTINGS
        ):
            continue
        seen.add(digest)
        accepted.append(
            {
                "grid": deepcopy(grid),
                "outputs": deepcopy(outputs),
                "sampling": {
                    "split": split,
                    "accepted_index": len(accepted),
                    "attempt": attempt,
                    "generator_seed": generator_seed,
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                    "input_sha256": digest,
                },
            }
        )
    if len(accepted) != count:
        raise RuntimeError(
            f"only found {len(accepted)}/{count} distinct four-setting inputs "
            f"for {split} within {max_attempts} attempts"
        )
    return accepted


def build_episode(
    seed: int,
    *,
    setting: object = _UNSET,
    n_train: int = DEFAULT_N_TRAIN,
    n_test: int = DEFAULT_N_TEST,
) -> dict[str, Any]:
    """Build one fixed-setting episode with independent demo/query counts."""
    seed = _validate_seed(seed)
    n_train = _validate_count("n_train", n_train)
    n_test = _validate_count("n_test", n_test)
    selected = choose_setting(seed) if setting is _UNSET else _validate_setting(setting)
    generator, source_path, source_sha256 = _selected_generator()
    root = find_root(__file__)

    train_samples = _sample_split(seed, "train", n_train)
    test_samples = _sample_split(seed, "test", n_test)
    train_hashes = {sample["sampling"]["input_sha256"] for sample in train_samples}
    test_hashes = {sample["sampling"]["input_sha256"] for sample in test_samples}
    overlap = train_hashes & test_hashes
    if overlap:
        raise RuntimeError(
            "independent train/test streams produced duplicate visible inputs: "
            + ", ".join(sorted(overlap))
        )

    def pair(sample: dict[str, Any]) -> dict[str, Any]:
        return {
            "input": deepcopy(sample["grid"]),
            "output": deepcopy(sample["outputs"][selected]),
            "setting": selected,
            "sampling": deepcopy(sample["sampling"]),
        }

    program = program_for(selected)
    episode = {
        "schema": "90640e0e6314-parametric-identity-corner-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameter": {PARAMETER_NAME: selected},
        "program": program,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "train": [pair(sample) for sample in train_samples],
        "test": [pair(sample) for sample in test_samples],
        "meta": {
            "prototype": True,
            "status": "proposed_not_selected",
            "selection_scope": "once_per_episode",
            "allowed_settings": list(ALLOWED_SETTINGS),
            "canonical_default": DEFAULT_SETTING,
            "input_constraint": (
                "selected production-generator inputs with four distinct reflection "
                "variants; all four corner settings must produce distinct outputs"
            ),
        },
    }
    errors = episode_errors(episode)
    if errors:
        raise RuntimeError("constructed invalid prototype episode: " + "; ".join(errors))
    # Keep this reference explicit: source identity is part of the episode contract.
    if generator.TASK_ID != TASK_ID:
        raise RuntimeError("selected generator task identity drift")
    return episode


def episode_errors(episode: Any) -> list[str]:
    """Validate fixed setting, labels, uniqueness, and finite-rival teaching."""
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

    errors: list[str] = []
    seen: set[str] = set()
    demos_refute = {rival: False for rival in ALLOWED_SETTINGS if rival != selected}
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict):
                errors.append(f"{split_name}[{index}] must be a mapping")
                continue
            if pair.get("setting") != selected:
                errors.append(f"{split_name}[{index}] setting drift")
                continue
            grid = pair.get("input")
            try:
                _validated_grid(grid)
            except Exception as exc:
                errors.append(f"{split_name}[{index}] invalid input: {exc}")
                continue
            digest = grid_digest(grid)
            if digest in seen:
                errors.append(f"duplicate input at {split_name}[{index}]")
            seen.add(digest)
            outputs = {
                setting: _solve_valid_grid(grid, setting)
                for setting in ALLOWED_SETTINGS
            }
            expected = outputs[selected]
            if pair.get("output") != expected:
                errors.append(f"{split_name}[{index}] label mismatch")
            for rival, rival_output in outputs.items():
                if rival == selected:
                    continue
                differs = rival_output != expected
                if split_name == "train":
                    demos_refute[rival] = demos_refute[rival] or differs
                elif not differs:
                    errors.append(
                        f"test[{index}] does not distinguish rival {rival}"
                    )
    for rival, refuted in demos_refute.items():
        if not refuted:
            errors.append(f"demonstrations do not distinguish rival {rival}")
    return errors


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project a private episode to visible demos and answer-free query inputs."""
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


def public_bytes(challenge: dict[str, Any]) -> bytes:
    """Return the shared canonical serialization of visible challenge content."""
    return public_challenge_bytes(challenge)


def public_identifier(challenge: dict[str, Any]) -> str:
    """Return an opaque filename derived only from exact visible challenge bytes."""
    return f"challenge-{public_challenge_id(challenge)}.json"
