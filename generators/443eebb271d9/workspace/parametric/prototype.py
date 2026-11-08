"""Isolated episode-level special-period prototype for ARC task 443eebb271d9.

The selected generator and canonical Racket authority remain unchanged. This
prototype varies one nearby rule parameter once per episode:

* ``special_period=3`` (default/original): copies 3, 6, 9, ... are color 6 and
  extend down the lattice (zero-based instance indices 2, 5, 8, ...).
* ``special_period=2`` (alternative): copies 2, 4, 6, ... are color 6 and
  extend down the lattice (zero-based instance indices 1, 3, 5, ...).

The glyph extraction, one-cell lattice gap, complete top row, and vertical
extension mechanism are invariant. Retained labels are produced by executing
the exact callable returned by :func:`racket_program`; :func:`python_reference`
is an independent authoring mirror only.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import stable_rng

TASK_ID = "443eebb271d9"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "special_period"
DEFAULT_SPECIAL_PERIOD = 3
ALLOWED_SPECIAL_PERIODS = (DEFAULT_SPECIAL_PERIOD, 2)
PARAMETER_SPEC = {
    PARAMETER_NAME: {
        "type": "enum[int]",
        "allowed": list(ALLOWED_SPECIAL_PERIODS),
        "default": DEFAULT_SPECIAL_PERIOD,
        "chosen": "once per episode from the deterministic episode seed",
        "input_constraints": (
            "selected-generator inputs with at least three horizontal lattice "
            "instances and one lower lattice row; every retained pair must "
            "distinguish periods 2 and 3"
        ),
    }
}


def _validate_special_period(value: Any) -> int:
    if type(value) is not int or value not in ALLOWED_SPECIAL_PERIODS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_SPECIAL_PERIODS}, got {value!r}"
        )
    return value


def choose_parameters(seed: int) -> dict[str, int]:
    """Choose one hidden period deterministically for the whole episode."""
    if type(seed) is not int:
        raise TypeError("episode seed must be a literal integer (not bool)")
    rng = stable_rng(seed, f"{TASK_ID}|parametric-rule", PROTOTYPE_VERSION)
    return {
        PARAMETER_NAME: ALLOWED_SPECIAL_PERIODS[
            rng.randrange(len(ALLOWED_SPECIAL_PERIODS))
        ]
    }


def _validate_grid(grid: Any) -> tuple[int, int, tuple[tuple[int, int], ...]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must contain at least one row")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        type(value) is not int or value not in (0, 7)
        for row in grid
        for value in row
    ):
        raise ValueError("prototype inputs must contain literal colors 0 and 7 only")
    cells = tuple(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 7
    )
    if not cells:
        raise ValueError("one color-7 source glyph is required")
    return len(grid), width, cells


def _bbox(cells: tuple[tuple[int, int], ...]) -> tuple[int, int, int, int]:
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def python_reference(
    grid: list[list[int]], *, special_period: int = DEFAULT_SPECIAL_PERIOD
) -> list[list[int]]:
    """Independent mirror of the parameterized lattice transformation."""
    period = _validate_special_period(special_period)
    height, width, cells = _validate_grid(grid)
    row0, col0, row1, col1 = _bbox(cells)
    glyph_h, glyph_w = row1 - row0 + 1, col1 - col0 + 1
    hstep, vstep = glyph_w + 1, glyph_h + 1
    normalized = {(row - row0, col - col0) for row, col in cells}
    special_remainder = period - 1

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(row0, height):
        for col in range(col0, width):
            rel_row, rel_col = row - row0, col - col0
            local = (rel_row % vstep, rel_col % hstep)
            instance, row_repeat = rel_col // hstep, rel_row // vstep
            special = instance % period == special_remainder
            if local in normalized and (row_repeat == 0 or special):
                output[row][col] = 6 if special else 7
    return output


def build_input(generator: Any, episode_seed: int, pair_index: int) -> list[list[int]]:
    """Build one deterministic selected-family input without exposing the rule."""
    if type(episode_seed) is not int:
        raise TypeError("episode seed must be a literal integer (not bool)")
    if type(pair_index) is not int:
        raise TypeError("pair_index must be a literal integer (not bool)")
    if not 0 <= pair_index < 4:
        raise ValueError("pair_index must be in 0..3")

    profiles = list(generator.GENERAL_PROFILES)
    rng = stable_rng(
        episode_seed,
        f"{TASK_ID}|parametric-input-profiles",
        PROTOTYPE_VERSION,
    )
    rng.shuffle(profiles)
    profile = profiles[pair_index]
    difficulty = ("easy", "medium", "hard", None)[
        (episode_seed + pair_index) % 4
    ]
    generation_seed = episode_seed * 10_007 + pair_index * 101 + 17
    sample_index = episode_seed * 4 + pair_index
    grid = generator.generate(
        generation_seed,
        sample_index,
        difficulty=difficulty,
        scene_profile=profile,
    )
    if python_reference(grid, special_period=2) == python_reference(
        grid, special_period=3
    ):
        raise AssertionError("constructed input does not distinguish period settings")
    return grid


def racket_program(parameters: dict[str, Any]) -> str:
    """Materialize the exact Racket callable for one episode setting."""
    period = _validate_special_period(parameters.get(PARAMETER_NAME))
    special_remainder = period - 1
    return f"""(lambda (g)
  (let* ((h (rows g))
         (w (cols g)))
    (begin
      (define bb (bbox-of-cells (find-color g 7)))
      (define r0 (first bb))
      (define c0 (second bb))
      (define r1 (third bb))
      (define c1 (fourth bb))
      (define gh (+ 1 (- r1 r0)))
      (define gw (+ 1 (- c1 c0)))
      (define hstep (+ gw 1))
      (define vstep (+ gh 1))
      (define (mask? local-r local-c)
        (= (safe-at g (+ r0 local-r) (+ c0 local-c) 0) 7))
      (define (paint? r c)
        (if (or (< r r0) (< c c0))
            #f
            (let* ((rr (- r r0))
                   (cc (- c c0))
                   (local-r (mod rr vstep))
                   (local-c (mod cc hstep))
                   (inst (quotient cc hstep))
                   (row-rep (quotient rr vstep)))
              (and
                (< local-r gh)
                (< local-c gw)
                (mask? local-r local-c)
                (or (zero? row-rep)
                    (= (mod inst {period}) {special_remainder}))))))
      (cellmap g
               (r c v)
               (if (paint? r c)
                   (if (= (mod (quotient (- c c0) hstep) {period})
                          {special_remainder})
                       6
                       7)
                   0)))))"""


def grid_literal(grid: list[list[int]]) -> str:
    _validate_grid(grid)
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    )
    return f"'({rows})"


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Redact the episode seed, hidden period, Racket source, and query label."""
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "demos": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["output"]),
            }
            for pair in episode["demos"]
        ],
        "query": {"input": deepcopy(episode["query"]["input"])},
    }


# Native input assembly is independent of the episode's hidden special period.
# The first two roles teach the existing whole-glyph and geometry dependency;
# subsequent roles broaden masks, positions and canvas sizes without rejection.
NATIVE_INPUT_VERSION = "2.0.0"
_NATIVE_DEMO_SIZES = ((11, 18), (17, 23), (14, 21), (20, 24), (25, 28), (28, 30))
_NATIVE_QUERY_SIZES = ((11, 18), (30, 30), (19, 26), (26, 29))
_NATIVE_MINIMUM_PROFILES = (
    "solid_square", "solid_rectangle", "hollow_square", "plus", "tee",
    "aitch", "zigzag", "stair", "asymmetric_branch",
)
_NATIVE_LARGE_DENSE_PROFILES = (
    "solid_square", "solid_rectangle", "hollow_square", "aitch",
)
_NATIVE_LARGE_OPTIONS = tuple(
    (profile, row0, col0)
    for profile in _NATIVE_LARGE_DENSE_PROFILES
    for row0 in range(1, 5)
    for col0 in range(1, 5)
) + tuple(
    (profile, 1, 1)
    for profile in ("tee", "split_bar", "diagonal_cross", "zigzag", "stair", "asymmetric_branch")
)


def validate_native_settings(settings: Any) -> int:
    """Reject missing/extra keys and scalar coercion at the native boundary."""
    if not isinstance(settings, dict) or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain exactly {PARAMETER_NAME!r}")
    return _validate_special_period(settings[PARAMETER_NAME])


def _validate_native_request(seed: Any, demos: Any, queries: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer (not bool)")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be a literal integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be a literal integer in 1..4")


def _native_scene(
    generator: Any,
    profile: str,
    height: int,
    width: int,
    row0: int,
    col0: int,
) -> list[list[int]]:
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in generator._GLYPHS[profile]:
        grid[row0 + row][col0 + col] = 7
    errors = generator.self_check(grid)
    if errors:
        raise AssertionError(f"constructed native input violates grammar: {errors}")
    return grid


def _native_input(generator: Any, seed: int, split: str, index: int) -> list[list[int]]:
    """Construct one role with its own deterministic input-only RNG stream."""
    sizes = _NATIVE_DEMO_SIZES if split == "train" else _NATIVE_QUERY_SIZES
    height, width = sizes[index]
    rng = stable_rng(
        seed, f"{TASK_ID}|native-input|{split}|{index}", NATIVE_INPUT_VERSION
    )
    if split == "train" and index == 0:
        return _native_scene(generator, "split_corner", height, width, 1, 1)
    if split == "train" and index == 1:
        # Both origins expose instance five (the sixth copy), distinguishing
        # every-third propagation from an otherwise fitting third-copy-only rule.
        # Both retain clipping; seed zero keeps the original (2, 2) witness.
        return _native_scene(
            generator, "stair", height, width,
            2 + seed % 2, 2 - ((seed >> 1) % 2),
        )
    if split == "test" and index == 1:
        # Vary masks and origins rather than repeating one memorisable query.
        # All 70 constructive options occupy >=100 output cells for both rules
        # and reach row/column 28 or 29. Settings never influence this draw.
        profile, row0, col0 = _NATIVE_LARGE_OPTIONS[rng.randrange(len(_NATIVE_LARGE_OPTIONS))]
        return _native_scene(generator, profile, height, width, row0, col0)
    profiles = (
        _NATIVE_MINIMUM_PROFILES
        if split == "test" and index == 0
        else generator.GENERAL_PROFILES
    )
    profile = profiles[rng.randrange(len(profiles))]
    cells = generator._GLYPHS[profile]
    glyph_h = max(row for row, _ in cells) + 1
    glyph_w = max(col for _, col in cells) + 1
    row0 = rng.randint(1, height - (2 * glyph_h + 1))
    col0 = rng.randint(1, width - (3 * glyph_w + 2))
    return _native_scene(generator, profile, height, width, row0, col0)


def native_inputs(
    generator: Any, seed: int, demos: int, queries: int
) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    """Return distinct, prefix-stable demo/query inputs in the canonical grammar.

    Each split/index has its own random stream, so changing either count cannot
    affect existing inputs. Distinct canvas sizes separate every role except
    the minimum-size demo/query, whose disconnected/connected masks differ.
    """
    _validate_native_request(seed, demos, queries)
    return (
        [_native_input(generator, seed, "train", index) for index in range(demos)],
        [_native_input(generator, seed, "test", index) for index in range(queries)],
    )
