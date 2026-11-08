"""Proposed, task-local alternating-tile rules; no production generator imports.

Labels are obtained only by execute_program() through a caller-owned RacketBridge.
This module is intentionally outside the selected fixed-rule generator interface.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import random
from typing import Any

from reviewer_support import normalize_grid

TASK_ID = "75ba893e1e36"
FIRST_TILES = ("mirror", "input")
TILE_PAIRS = (1, 2, 3)
SETTINGS = tuple((first, pairs) for first in FIRST_TILES for pairs in TILE_PAIRS)
DEFAULT_PARAMETERS = ("mirror", 2)
DEFAULT_SEED = 1
PALETTE = (5, 7, 8)

# Authored teaching witnesses, independent of the live production generator.
# Each has an asymmetric row, so a starting-phase change is observable.
WITNESSES = (
    ((5, 7, 8), (5, 5, 7), (8, 7, 7)),
    ((8, 8, 5), (7, 5, 7), (5, 8, 7)),
    ((7, 5, 5), (8, 7, 8), (5, 5, 8)),
    ((5, 8, 7), (8, 5, 8), (7, 7, 5)),
)


def _seed(seed: int) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    return seed


def choose_parameters(seed: int) -> tuple[str, int]:
    """Choose both rule parameters exactly once from the episode seed.

    Six consecutive seeds cover all settings. Paired seeds within one block
    share input draws to make the bounded parameter comparison direct.
    """
    return SETTINGS[_seed(seed) % len(SETTINGS)]


def program_for(first_tile: str, tile_pairs: int) -> str:
    if first_tile not in FIRST_TILES or type(tile_pairs) is not int or tile_pairs not in TILE_PAIRS:
        raise ValueError("first_tile must be mirror/input and tile_pairs must be 1/2/3")
    pair = ("(flip-lr g)", "g") if first_tile == "mirror" else ("g", "(flip-lr g)")
    tiles = " ".join(pair * tile_pairs)
    return "(rule! (lambda (g) (stack-grids 'horizontal (list " + tiles + "))))"


def episode_inputs(seed: int) -> list[list[list[int]]]:
    """Return three demonstrations and one query, all 3x3 and lawful.

    Only color/row permutations are seeded. The rule setting is not resampled
    per pair. This deliberately small teaching family makes no distributional
    diversity claim about the production sampler.
    """
    rng = random.Random(_seed(seed) // len(SETTINGS))
    colors = list(PALETTE)
    rng.shuffle(colors)
    mapping = dict(zip(PALETTE, colors))
    result = []
    for witness in WITNESSES:
        rows = list(witness)
        rng.shuffle(rows)
        result.append([[mapping[cell] for cell in row] for row in rows])
    return result


def validate_input(grid: list[list[int]]) -> list[list[int]]:
    rows = normalize_grid(grid)
    if len(rows) != 3 or len(rows[0]) != 3:
        raise ValueError("prototype inputs must be exactly 3x3")
    if set(cell for row in rows for cell in row) != set(PALETTE):
        raise ValueError("prototype inputs must use exactly colors 5, 7, and 8")
    if all(row == row[::-1] for row in rows):
        raise ValueError("teaching inputs need an asymmetric row to identify first_tile")
    return rows


def racket_application(program: str, grid: list[list[int]]) -> str:
    """Embed the exact callable-form rule text, without rewriting its body.

    rule! is the REPL's registration form, not an ARC grid primitive. These six
    programs all supply a closed lambda, so an identity binding returns that
    very lambda for application. The full emitted program remains byte-for-byte
    inside the executed expression. This is deliberately not a general rule!
    interpreter, nor a shared runtime-interface change.
    """
    rows = validate_input(grid)
    if program not in {program_for(*setting) for setting in SETTINGS}:
        raise ValueError("only the six emitted closed-lambda programs are supported")
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in rows) + ")"
    return "(let ((rule! (lambda (f) f))) (" + program + " " + literal + "))"


def execute_program(bridge: Any, program: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute an emitted Racket rule and validate the actual grid result."""
    output = normalize_grid(bridge.eval_text(racket_application(program, grid)))
    if len(output) != 3 or len(output[0]) > 30:
        raise ValueError("Racket output exceeds the declared 3-row / 30-column bound")
    return output


def build_episode(seed: int, bridge: Any) -> dict[str, Any]:
    """Build a private, complete 3-demonstration/1-query episode through Racket."""
    first_tile, tile_pairs = choose_parameters(seed)
    program = program_for(first_tile, tile_pairs)
    pairs = [
        {"input": grid, "output": execute_program(bridge, program, grid)}
        for grid in episode_inputs(seed)
    ]
    return {
        "schema": "75ba893e1e36-parametric-private-v1",
        "status": "proposed_prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": {"first_tile": first_tile, "tile_pairs": tile_pairs},
        "program": program,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "train": pairs[:3],
        "test": pairs[3:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Only demonstrated pairs and query inputs cross the public boundary."""
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }
