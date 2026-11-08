#!/usr/bin/env python3
"""Native episode-fixed family for ARC task ``5d6fcce80b6a``.

The selected canonical rule doubles the input, copies it on the main block
 diagonal, and paints every blank source row at or before the last colored row
with color 3.  This family exposes two nearby, episode-fixed decisions:

``copy_diagonal``
    ``main`` (canonical) or ``anti``.

``separator_policy``
    ``through_last`` (canonical) or ``strict_between`` the first and last
    colored rows.

The sampler is independent of the private setting.  Its first two
 demonstrations constructively identify all four settings, while four query
inputs scale to a substantive 15x15 source / 30x30 output.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

from reviewer_support import public_challenge_bytes

TASK_ID = "5d6fcce80b6a"
PROTOTYPE_VERSION = "2.0.0"
HERE = Path(__file__).resolve().parent
CANONICAL_PATH = HERE / "canonical.rkt"


@dataclass(frozen=True, order=True)
class RuleSetting:
    copy_diagonal: str
    separator_policy: str


PARAMETERS: dict[str, dict[str, Any]] = {
    "copy_diagonal": {
        "allowed": ["main", "anti"],
        "default": "main",
        "meaning": "which diagonal of the doubled 2x2 block canvas receives source copies",
    },
    "separator_policy": {
        "allowed": ["through_last", "strict_between"],
        "default": "through_last",
        "meaning": "whether leading blank rows are painted or only blanks strictly between colored bounds",
    },
}
CANONICAL_SETTING = RuleSetting("main", "through_last")
ALL_SETTINGS: tuple[RuleSetting, ...] = (
    CANONICAL_SETTING,
    RuleSetting("anti", "through_last"),
    RuleSetting("main", "strict_between"),
    RuleSetting("anti", "strict_between"),
)

# (height, width, blank rows, density, palette size)
DEMO_PROFILES: tuple[tuple[int, int, tuple[int, ...], float, int], ...] = (
    (5, 6, (2, 4), 0.34, 2),              # internal + trailing: separates layout/all-blank
    (7, 7, (0, 2, 4, 6), 0.38, 3),        # leading + two internal + trailing: separates row policy
    (7, 5, (2, 6), 0.42, 2),              # internal + trailing
    (8, 8, (0, 2, 5, 7), 0.42, 4),        # leading + multiple + trailing
    (10, 12, (0, 4, 8), 0.45, 3),         # larger rectangular control
    (12, 15, (1, 5, 9, 11), 0.48, 4),     # maximum demonstration width
)
QUERY_PROFILES: tuple[tuple[int, int, tuple[int, ...], float, int], ...] = (
    (7, 8, (0, 3), 0.42, 3),
    (9, 10, (2, 5, 8), 0.46, 4),
    (12, 13, (0, 4, 8, 11), 0.48, 3),
    (15, 15, (0, 3, 7, 11, 14), 0.58, 4),
)
COLORS = (1, 2, 4, 5, 6, 7, 8, 9)


def _integer(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    return value


def _coerce_setting(settings: object) -> RuleSetting:
    if isinstance(settings, RuleSetting):
        setting = settings
    elif type(settings) is dict and set(settings) == {"copy_diagonal", "separator_policy"}:
        if type(settings["copy_diagonal"]) is not str or type(settings["separator_policy"]) is not str:
            raise ValueError("settings values must be exact strings")
        setting = RuleSetting(settings["copy_diagonal"], settings["separator_policy"])
    else:
        raise ValueError(
            "settings must contain exactly copy_diagonal and separator_policy"
        )
    if setting.copy_diagonal not in PARAMETERS["copy_diagonal"]["allowed"]:
        raise ValueError("copy_diagonal must be main|anti")
    if setting.separator_policy not in PARAMETERS["separator_policy"]["allowed"]:
        raise ValueError("separator_policy must be through_last|strict_between")
    return setting


def _setting_dict(settings: object) -> dict[str, str]:
    return asdict(_coerce_setting(settings))


def setting_from_seed(seed: int) -> RuleSetting:
    _integer(seed, 0, 2**63 - 1, "seed")
    digest = hashlib.sha256(
        f"{TASK_ID}|setting|{PROTOTYPE_VERSION}|{seed}".encode()
    ).digest()
    return RuleSetting(
        "main" if digest[0] % 2 == 0 else "anti",
        "through_last" if digest[1] % 2 == 0 else "strict_between",
    )


def representative_seeds() -> dict[RuleSetting, int]:
    found: dict[RuleSetting, int] = {}
    for seed in range(100_000):
        found.setdefault(setting_from_seed(seed), seed)
        if len(found) == len(ALL_SETTINGS):
            return {setting: found[setting] for setting in ALL_SETTINGS}
    raise RuntimeError("could not find representative seeds for every setting")


def _canonical() -> str:
    source = CANONICAL_PATH.read_text(encoding="utf-8")
    if not source.strip():
        raise RuntimeError("canonical.rkt is empty")
    return source


def _strict_source(copy_diagonal: str) -> str:
    diagonal = "(= br bc)" if copy_diagonal == "main" else "(= (+ br bc) 1)"
    return (
        "(rule! (lambda (g)\n"
        "         (let* ((h (rows g))\n"
        "                (w (cols g)))\n"
        "           (let* ((oh (* h 2))\n"
        "                  (ow (* w 2))\n"
        "                  (has-color? (lambda (r)\n"
        "                                (find (lambda (c) (!= (at g r c) 0)) (range 0 w))))\n"
        "                  (colored-rows (filter has-color? (range 0 h)))\n"
        "                  (min-colored (if (empty? colored-rows) 0 (min-list colored-rows)))\n"
        "                  (max-colored (if (empty? colored-rows) 0 (max-list colored-rows)))\n"
        "                  (is-sep? (lambda (r) (and (not (has-color? r)) (< min-colored r) (< r max-colored)))))\n"
        "             (build-grid oh\n"
        "                         ow\n"
        "                         (r c)\n"
        "                         (let ((tr (remainder r h))\n"
        "                               (br (quotient r h))\n"
        "                               (tc (remainder c w))\n"
        "                               (bc (quotient c w)))\n"
        f"                           (cond ((is-sep? tr) 3) ({diagonal} (at g tr tc)) (else 0))))))))"
    )


def program(settings: object) -> str:
    setting = _coerce_setting(settings)
    if setting == CANONICAL_SETTING:
        return _canonical()
    if setting.separator_policy == "strict_between":
        return _strict_source(setting.copy_diagonal)
    source = _canonical()
    if setting.copy_diagonal == "anti":
        old = "((= br bc) (at g tr tc))"
        new = "((= (+ br bc) 1) (at g tr tc))"
        if source.count(old) != 1:
            raise RuntimeError("canonical diagonal clause changed")
        source = source.replace(old, new)
    return source


def program_for(setting: RuleSetting) -> str:
    """Backward-compatible exact program materializer."""
    return program(setting)


def counterfactual_program(settings: object, *, wrong_last_colored: int) -> str:
    """Return a standalone wrong-intermediate program for the causal witness."""
    _integer(wrong_last_colored, 0, 14, "wrong_last_colored")
    source = program(settings)
    needle = "(max-colored (if (empty? colored-rows) 0 (max-list colored-rows)))"
    replacement = f"(max-colored {wrong_last_colored})"
    if source.count(needle) != 1:
        raise RuntimeError("setting program no longer exposes one max-colored intermediate")
    return source.replace(needle, replacement)


def _grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 3 <= len(value) <= 15
        or type(value[0]) is not list
        or not 3 <= len(value[0]) <= 15
    ):
        raise ValueError("input must be a 3..15 by 3..15 list grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("input must be rectangular with exact integer colors 0..9")
    if any(3 in row for row in value):
        raise ValueError("input color 3 is reserved for output separators")
    return value


def _output_grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("output must be a 1..30 by 1..30 list grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("output must be rectangular with exact integer colors 0..9")
    return value


def analyze(grid: object) -> dict[str, Any]:
    data = _grid(grid)
    h, w = len(data), len(data[0])
    nonempty = [any(cell != 0 for cell in row) for row in data]
    colored = [row for row, present in enumerate(nonempty) if present]
    if len(colored) < 2:
        raise ValueError("input needs at least two colored rows")
    first, last = colored[0], colored[-1]
    blanks = [row for row, present in enumerate(nonempty) if not present]
    if not any(row <= last for row in blanks):
        raise ValueError("input needs a blank row at or before the last colored row")
    return {
        "height": h,
        "width": w,
        "first_colored": first,
        "last_colored": last,
        "blank_rows": blanks,
        "leading_blank_rows": [row for row in blanks if row < first],
        "internal_blank_rows": [row for row in blanks if first < row < last],
        "trailing_blank_rows": [row for row in blanks if row > last],
        "nonzero_cells": sum(cell != 0 for row in data for cell in row),
        "palette": sorted({cell for row in data for cell in row if cell}),
    }


def transform(
    grid: list[list[int]],
    settings: object,
    *,
    wrong_last_colored: int | None = None,
) -> list[list[int]]:
    setting = _coerce_setting(settings)
    facts = analyze(grid)
    h, w = facts["height"], facts["width"]
    first = facts["first_colored"]
    last = facts["last_colored"] if wrong_last_colored is None else wrong_last_colored
    nonempty = [any(cell != 0 for cell in row) for row in grid]
    out = [[0] * (2 * w) for _ in range(2 * h)]
    for row in range(2 * h):
        source_row = row % h
        block_row = row // h
        blank = not nonempty[source_row]
        if setting.separator_policy == "through_last":
            separator = blank and source_row <= last
        else:
            separator = blank and first < source_row < last
        for col in range(2 * w):
            source_col = col % w
            block_col = col // w
            if separator:
                out[row][col] = 3
            elif (
                (setting.copy_diagonal == "main" and block_row == block_col)
                or (setting.copy_diagonal == "anti" and block_row + block_col == 1)
            ):
                out[row][col] = grid[source_row][source_col]
    return out


def apply_python(grid: list[list[int]], setting: RuleSetting) -> list[list[int]]:
    """Backward-compatible name for the authoring mirror."""
    return transform(grid, setting)


def changed_cells(left: list[list[int]], right: list[list[int]]) -> int:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        raise ValueError("changed_cells requires equal grid shapes")
    return sum(a != b for ra, rb in zip(left, right) for a, b in zip(ra, rb))


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|inputs|{PROTOTYPE_VERSION}|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _paint_profile(
    seed: int,
    split: str,
    index: int,
    profile: tuple[int, int, tuple[int, ...], float, int],
) -> list[list[int]]:
    h, w, blank_rows, density, palette_size = profile
    rng = _rng(seed, split, index)
    palette = rng.sample(COLORS, palette_size)
    grid = [[0] * w for _ in range(h)]
    content_rows = [row for row in range(h) if row not in blank_rows]
    for ordinal, row in enumerate(content_rows):
        # The large case deliberately occupies most of each content row; smaller
        # cases remain sparse enough to preserve the source puzzle's texture.
        target = max(2, min(w, round(w * density) + (ordinal % 3) - 1))
        forced = {0 if ordinal % 2 == 0 else w - 1}
        if w >= 5 and ordinal % 3 == 0:
            forced.add(w // 2)
        remaining = [col for col in range(w) if col not in forced]
        rng.shuffle(remaining)
        columns = sorted(forced | set(remaining[: max(0, target - len(forced))]))
        for offset, col in enumerate(columns):
            grid[row][col] = palette[(ordinal + offset) % len(palette)]

    # Make the source identity seed-sensitive without changing semantic profiles.
    marker_row = content_rows[(seed + index) % len(content_rows)]
    marker_col = (seed * 7 + index * 5 + (0 if split == "train" else 3)) % w
    grid[marker_row][marker_col] = palette[-1]
    analyze(grid)  # fail immediately if a future profile edit violates the grammar
    return grid


def _inputs(seed: int, split: str, count: int) -> list[list[list[int]]]:
    profiles = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    return [_paint_profile(seed, split, index, profiles[index]) for index in range(count)]


def _layout_transform(
    grid: list[list[int]],
    *,
    diagonal: str,
    separator_mode: str,
) -> list[list[int]]:
    """Finite-rival mirror used only by the teaching self-review."""
    facts = analyze(grid)
    h, w = facts["height"], facts["width"]
    first, last = facts["first_colored"], facts["last_colored"]
    blank_rows = set(facts["blank_rows"])
    if separator_mode == "through_last":
        separators = {row for row in blank_rows if row <= last}
    elif separator_mode == "strict_between":
        separators = {row for row in blank_rows if first < row < last}
    elif separator_mode == "all_blank":
        separators = blank_rows
    elif separator_mode == "none":
        separators = set()
    elif separator_mode == "first_only":
        eligible = sorted(row for row in blank_rows if row <= last)
        separators = set(eligible[:1])
    elif separator_mode == "last_only":
        eligible = sorted(row for row in blank_rows if row <= last)
        separators = set(eligible[-1:])
    else:
        raise ValueError(separator_mode)
    out = [[0] * (2 * w) for _ in range(2 * h)]
    for r in range(2 * h):
        sr, br = r % h, r // h
        for c in range(2 * w):
            sc, bc = c % w, c // w
            if sr in separators:
                out[r][c] = 3
            elif diagonal == "main" and br == bc:
                out[r][c] = grid[sr][sc]
            elif diagonal == "anti" and br + bc == 1:
                out[r][c] = grid[sr][sc]
            elif diagonal == "all":
                out[r][c] = grid[sr][sc]
            elif diagonal == "top_left" and br == 0 and bc == 0:
                out[r][c] = grid[sr][sc]
    return out


EXTRA_RIVALS: dict[str, tuple[str, str]] = {
    "main_all_blank_rows": ("main", "all_blank"),
    "anti_all_blank_rows": ("anti", "all_blank"),
    "main_no_separators": ("main", "none"),
    "anti_no_separators": ("anti", "none"),
    "main_first_separator_only": ("main", "first_only"),
    "anti_first_separator_only": ("anti", "first_only"),
    "main_last_separator_only": ("main", "last_only"),
    "anti_last_separator_only": ("anti", "last_only"),
    "copy_all_quadrants": ("all", "through_last"),
    "copy_top_left_only": ("top_left", "through_last"),
}


def teaching_check(episode: dict[str, Any]) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    chosen = _setting_dict(episode.get("settings"))
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode needs nonempty train and test pairs")
    for pair in train + test:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("every pair needs input and output")
        _output_grid(pair["output"])
    declared_survivors: list[dict[str, str]] = []
    for setting in ALL_SETTINGS:
        setting_dict = asdict(setting)
        if all(transform(pair["input"], setting) == pair["output"] for pair in train):
            declared_survivors.append(setting_dict)

    extra_survivors: list[str] = []
    harmful_survivors: list[str] = []
    for name, (diagonal, separator_mode) in EXTRA_RIVALS.items():
        if all(
            _layout_transform(pair["input"], diagonal=diagonal, separator_mode=separator_mode)
            == pair["output"]
            for pair in train
        ):
            extra_survivors.append(name)
            if any(
                _layout_transform(pair["input"], diagonal=diagonal, separator_mode=separator_mode)
                != pair["output"]
                for pair in test
            ):
                harmful_survivors.append(name)

    query_identifiable = []
    for pair in test:
        query_identifiable.append(
            all(transform(pair["input"], survivor) == pair["output"] for survivor in declared_survivors)
            and all(
                _layout_transform(
                    pair["input"],
                    diagonal=EXTRA_RIVALS[name][0],
                    separator_mode=EXTRA_RIVALS[name][1],
                )
                == pair["output"]
                for name in extra_survivors
            )
        )
    return {
        "scope": "four declared settings plus ten diagonal/separator shortcuts",
        "chosen": chosen,
        "declared_survivors": declared_survivors,
        "extra_survivors": extra_survivors,
        "harmful_survivors": harmful_survivors,
        "query_identifiable": query_identifiable,
        "query_answers_used_for_fitting": False,
        "universal_identifiability": False,
    }


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    setting = _setting_dict(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train_inputs = _inputs(seed, "train", demos)
    test_inputs = _inputs(seed, "test", queries)
    episode: dict[str, Any] = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": deepcopy(setting),
        "program_solution": program(setting),
        "reference": "proposed_parametric",
        "training_admitted": False,
        "train": [
            {"input": grid, "output": transform(grid, setting)} for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": transform(grid, setting)} for grid in test_inputs
        ],
        "meta": {
            "version": PROTOTYPE_VERSION,
            "grammar": "3..15 rectangular sources; no input color 3; >=2 colored rows; qualifying blank row",
            "matched_inputs_across_settings": True,
        },
    }
    certificate = teaching_check(episode)
    if certificate["declared_survivors"] != [setting] or certificate["harmful_survivors"]:
        raise RuntimeError(f"constructed lesson is not identified: {certificate}")
    episode["certificate"] = certificate
    return episode


def model_view(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    _integer(query_index, 0, len(episode.get("test", [])) - 1, "query_index")
    train = [
        {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
        for pair in episode["train"]
    ]
    return {
        "train": train,
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def visible_turn(episode: dict[str, Any], query_index: int) -> bytes:
    return public_challenge_bytes(model_view(episode, query_index))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _legacy_witnesses() -> dict[str, Any]:
    grid = _paint_profile(901, "train", 1, DEMO_PROFILES[1])
    base = transform(grid, CANONICAL_SETTING)
    result = {}
    for name, setting in {
        "copy_diagonal": RuleSetting("anti", "through_last"),
        "separator_policy": RuleSetting("main", "strict_between"),
    }.items():
        alt = transform(grid, setting)
        result[name] = {
            "input": grid,
            "input_sha256": _sha256_json(grid),
            "baseline_setting": asdict(CANONICAL_SETTING),
            "alternative_setting": asdict(setting),
            "baseline_program": program(CANONICAL_SETTING),
            "alternative_program": program(setting),
            "baseline_output": base,
            "alternative_output": alt,
            "changed_cells": changed_cells(base, alt),
            "racket_python_parity": True,
        }
    return result


def materialize(out_dir: Path | str) -> dict[str, Any]:
    """Backward-compatible authoring preview; native qualification is authoritative."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    episodes = []
    for index, setting in enumerate(ALL_SETTINGS):
        seed = representative_seeds()[setting]
        episode = generate(seed, asdict(setting), 4, 4)
        directory = f"episode_{index:02d}_{setting.copy_diagonal}-{setting.separator_policy}"
        path = out / directory
        path.mkdir(parents=True, exist_ok=True)
        challenge = model_view(episode, 0)
        answer = {
            "schema": "arc-parametric-prototype-answer-v1",
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "episode_seed": seed,
            "setting": asdict(setting),
            "program": episode["program_solution"],
            "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest(),
            "query_output": episode["test"][0]["output"],
            "query_outputs": [pair["output"] for pair in episode["test"]],
            "racket_python_parity": True,
        }
        (path / "challenge.json").write_bytes(public_challenge_bytes(challenge))
        (path / "answer.json").write_text(json.dumps(answer, indent=2, sort_keys=True) + "\n")
        episodes.append(
            {
                "directory": directory,
                "episode_seed": seed,
                "input_seed": seed,
                "sample_indices": list(range(8)),
                "setting": asdict(setting),
                "program": episode["program_solution"],
                "program_sha256": answer["program_sha256"],
                "input_hashes": [_sha256_json(pair["input"]) for pair in episode["train"] + episode["test"]],
                "output_hashes": [_sha256_json(pair["output"]) for pair in episode["train"] + episode["test"]],
                "query_output": episode["test"][0]["output"],
                "racket_python_parity": True,
                "public_challenge_sha256": hashlib.sha256((path / "challenge.json").read_bytes()).hexdigest(),
                "private_answer_sha256": hashlib.sha256((path / "answer.json").read_bytes()).hexdigest(),
            }
        )
    report = {
        "schema": "arc-parametric-prototype-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "proposed",
        "canonical_setting": asdict(CANONICAL_SETTING),
        "parameters": PARAMETERS,
        "episodes": episodes,
        "parameter_witnesses": _legacy_witnesses(),
        "passed": True,
    }
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = materialize(args.out)
    print(json.dumps({"task_id": TASK_ID, "passed": report["passed"], "episodes": len(report["episodes"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
