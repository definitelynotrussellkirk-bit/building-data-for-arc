"""Native rotation-policy authoring prototype for ``fd588326c845``.

The default setting returns the canonical program byte-for-byte.  The nearby
``anchor_directed`` setting adds a genuine two-stage dependency: infer a
rotation direction from the unique singleton-color key cell, then use that
intermediate direction to map key colors into the expanded cyan silhouette.
Inputs are setting-neutral; only labels and the program vary by setting.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "fd588326c845"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
POLICIES = ("clockwise", "anchor_directed")
HYPOTHESES = POLICIES + (
    "counterclockwise",
    "anchor_inverted",
    "identity",
    "half_turn",
    "preserve_cyan",
    "solid_anchor",
)
_KEY_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

# Each binary key occupancy is invariant under a 180-degree turn.  Therefore
# its clockwise and counterclockwise silhouettes coincide, preventing the
# selected setting from leaking through the query input geometry.
_MASKS: dict[int, tuple[tuple[tuple[int, ...], ...], ...]] = {
    3: (
        (
            (1, 1, 0),
            (0, 1, 0),
            (0, 1, 1),
        ),
        (
            (1, 0, 1),
            (1, 0, 1),
            (1, 0, 1),
        ),
    ),
    4: (
        (
            (1, 1, 0, 0),
            (1, 0, 1, 0),
            (0, 1, 0, 1),
            (0, 0, 1, 1),
        ),
        (
            (1, 1, 0, 1),
            (1, 0, 1, 0),
            (0, 1, 0, 1),
            (1, 0, 1, 1),
        ),
        (
            (1, 1, 1, 0),
            (1, 1, 0, 1),
            (1, 0, 1, 1),
            (0, 1, 1, 1),
        ),
    ),
}

# (key size, mask index, scale_h, scale_w, height, width,
#  key_row, key_col, cyan_row, cyan_col, anchor side)
_DEMO_PROFILES = (
    (3, 0, 2, 3, 16, 18, 1, 1, 8, 8, "bottom"),
    (4, 1, 2, 2, 18, 20, 13, 1, 1, 10, "top"),
    (3, 1, 3, 1, 18, 14, 1, 9, 7, 1, "bottom"),
    (4, 0, 1, 3, 14, 22, 8, 1, 1, 9, "top"),
    (3, 0, 4, 2, 20, 17, 1, 1, 7, 9, "bottom"),
    (4, 2, 3, 3, 22, 24, 17, 18, 1, 1, "top"),
)
_QUERY_PROFILES = (
    (4, 1, 3, 2, 22, 20, 1, 1, 8, 10, "bottom"),
    (3, 1, 4, 3, 20, 22, 15, 1, 1, 11, "top"),
    (4, 2, 2, 4, 20, 26, 1, 20, 10, 1, "bottom"),
    # Stress case: key reaches top/right, silhouette reaches bottom/left.
    (4, 1, 5, 5, 30, 30, 0, 26, 10, 0, "top"),
)


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _policy(value: Any) -> str:
    if type(value) is not str or value not in POLICIES:
        raise ValueError("rotation_policy must be clockwise or anchor_directed")
    return value


def _settings(value: Any) -> str:
    if type(value) is not dict or set(value) != {"rotation_policy"}:
        raise ValueError("only the rotation_policy setting is declared")
    return _policy(value["rotation_policy"])


def grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError(
            "grid must be rectangular 1..30 with exact integer colors 0..9"
        )
    return value


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line))["task_id"] == TASK_ID
    }
    if len(programs) != 1:
        raise ValueError("require one exact canonical authority")
    return programs.pop()


def program(settings: Any) -> str:
    selected = _settings(settings)
    if selected == "clockwise":
        return canonical_program()
    return (HERE / "anchor_directed.rkt").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _source_module():
    module, _source, _sha256 = load_selected_generator(TASK_ID, root=ROOT)
    return module


def observe(value: Any) -> dict[str, Any]:
    """Parse one generated scene and expose only rule-relevant structure."""
    grid(value)
    coerced, features, errors = _source_module()._scene_analysis(value)
    if errors:
        raise ValueError("invalid rotation-policy scene: " + "; ".join(errors))
    assert features is not None
    key = tuple(tuple(row) for row in features["key_matrix"])
    side = features["key_size"]
    occupancy_symmetric = all(
        bool(key[row][col]) == bool(key[side - 1 - row][side - 1 - col])
        for row in range(side)
        for col in range(side)
    )
    if not occupancy_symmetric:
        raise ValueError("key occupancy must be invariant under a 180-degree turn")

    counts = Counter(
        cell for row in key for cell in row if cell != 0
    )
    singleton_colors = [color for color, count in counts.items() if count == 1]
    if len(singleton_colors) != 1:
        raise ValueError("key must contain exactly one singleton anchor color")
    anchor_color = singleton_colors[0]
    anchor_cells = [
        (row, col)
        for row in range(side)
        for col in range(side)
        if key[row][col] == anchor_color
    ]
    if len(anchor_cells) != 1:
        raise ValueError("singleton anchor must occupy exactly one key cell")
    anchor_row, anchor_col = anchor_cells[0]
    if side % 2 == 1 and anchor_row == side // 2:
        raise ValueError("odd-sized keys may not place the anchor on the middle row")
    anchor_side = "top" if 2 * anchor_row < side else "bottom"

    return {
        "height": len(coerced),
        "width": len(coerced[0]),
        "key_box": list(features["key_box"]),
        "cyan_box": list(features["cyan_box"]),
        "key_size": side,
        "scale_h": features["scale_h"],
        "scale_w": features["scale_w"],
        "key_matrix": [list(row) for row in key],
        "anchor_color": anchor_color,
        "anchor_cell": [anchor_row, anchor_col],
        "anchor_side": anchor_side,
        "occupancy_180_symmetric": occupancy_symmetric,
    }


def direction(value: Any, policy: Any) -> str:
    selected = _policy(policy)
    if selected == "clockwise":
        observe(value)
        return "clockwise"
    return (
        "clockwise"
        if observe(value)["anchor_side"] == "top"
        else "counterclockwise"
    )


def _map_source(side: int, tile_row: int, tile_col: int, mode: str) -> tuple[int, int]:
    if mode == "clockwise":
        return side - 1 - tile_col, tile_row
    if mode == "counterclockwise":
        return tile_col, side - 1 - tile_row
    if mode == "identity":
        return tile_row, tile_col
    if mode == "half_turn":
        return side - 1 - tile_row, side - 1 - tile_col
    raise ValueError(f"unknown mapping mode: {mode}")


def _render_mapping(value: Any, mode: str) -> list[list[int]]:
    state = observe(value)
    key_r1, key_c1, _key_r2, _key_c2 = state["key_box"]
    cyan_r1, cyan_c1, _cyan_r2, _cyan_c2 = state["cyan_box"]
    side = state["key_size"]
    scale_h = state["scale_h"]
    scale_w = state["scale_w"]
    out = [row[:] for row in value]
    for row in range(len(value)):
        for col in range(len(value[0])):
            if value[row][col] != 8:
                continue
            tile_row = (row - cyan_r1) // scale_h
            tile_col = (col - cyan_c1) // scale_w
            source_row, source_col = _map_source(
                side, tile_row, tile_col, mode
            )
            out[row][col] = value[
                key_r1 + source_row
            ][
                key_c1 + source_col
            ]
    return out


def transform(value: Any, policy: Any) -> list[list[int]]:
    return _render_mapping(value, direction(value, policy))


def predict(value: Any, hypothesis: Any) -> list[list[int]]:
    if type(hypothesis) is not str or hypothesis not in HYPOTHESES:
        raise ValueError("unknown declared hypothesis")
    if hypothesis in POLICIES:
        return transform(value, hypothesis)
    if hypothesis == "counterclockwise":
        return _render_mapping(value, "counterclockwise")
    if hypothesis == "anchor_inverted":
        state = observe(value)
        mode = "counterclockwise" if state["anchor_side"] == "top" else "clockwise"
        return _render_mapping(value, mode)
    if hypothesis in ("identity", "half_turn"):
        return _render_mapping(value, hypothesis)
    if hypothesis == "preserve_cyan":
        observe(value)
        return [row[:] for row in value]
    state = observe(value)
    out = [row[:] for row in value]
    for row in range(len(out)):
        for col in range(len(out[0])):
            if out[row][col] == 8:
                out[row][col] = state["anchor_color"]
    return out


def _sha256_grid(value: list[list[int]]) -> str:
    payload = json.dumps(value, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def certificate(
    train: Any, query_inputs: Any
) -> dict[str, Any]:
    """Infer from demonstrations only against a finite declared rival set."""
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("two through six teaching demonstrations are required")
    if type(query_inputs) is not list or len(query_inputs) != 4:
        raise ValueError("exactly four query inputs are required")
    for pair in train:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("each demonstration must contain input and output")
        grid(pair["input"])
        grid(pair["output"])
        observe(pair["input"])
    for value in query_inputs:
        grid(value)
        observe(value)

    survivors = [
        hypothesis
        for hypothesis in HYPOTHESES
        if all(
            predict(pair["input"], hypothesis) == pair["output"]
            for pair in train
        )
    ]
    if len(survivors) != 1 or survivors[0] not in POLICIES:
        raise ValueError(
            "demonstrations do not identify one setting against declared rivals: "
            + repr(survivors)
        )
    predictions = [predict(value, survivors[0]) for value in query_inputs]
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "demos": len(train),
        "queries": len(query_inputs),
        "anchor_sides": [observe(pair["input"])["anchor_side"] for pair in train],
        "query_anchor_sides": [observe(value)["anchor_side"] for value in query_inputs],
        "predicted_query_sha256": [_sha256_grid(value) for value in predictions],
        "scope": (
            "Finite declared rivals. The bottom/top teaching pair separates fixed "
            "clockwise, fixed counterclockwise, anchor-directed, and inverted-anchor "
            "policies; geometric and paint-only shortcuts are also checked."
        ),
    }


def _make_key(
    rng: random.Random, side: int, mask_index: int, anchor_side: str
) -> tuple[tuple[int, ...], ...]:
    mask = _MASKS[side][mask_index]
    occupied = [
        (row, col)
        for row in range(side)
        for col in range(side)
        if mask[row][col]
    ]
    candidates = [
        (row, col)
        for row, col in occupied
        if ("top" if 2 * row < side else "bottom") == anchor_side
        and not (side % 2 == 1 and row == side // 2)
    ]
    if not candidates:
        raise AssertionError("profile has no anchor candidate on requested side")
    anchor = rng.choice(candidates)
    anchor_color, first_color, second_color = rng.sample(_KEY_COLORS, 3)
    remaining = [position for position in occupied if position != anchor]
    rng.shuffle(remaining)
    cut = max(2, min(len(remaining) - 2, len(remaining) // 2))
    assigned = (
        [(anchor, anchor_color)]
        + [(position, first_color) for position in remaining[:cut]]
        + [(position, second_color) for position in remaining[cut:]]
    )
    key = [[0] * side for _ in range(side)]
    for (row, col), color in assigned:
        key[row][col] = color
    return tuple(tuple(row) for row in key)


def _rotate_mask_clockwise(mask: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in zip(*mask[::-1]))


def _scene(
    rng: random.Random,
    profile: tuple[int, int, int, int, int, int, int, int, int, int, str],
) -> list[list[int]]:
    (
        side,
        mask_index,
        scale_h,
        scale_w,
        height,
        width,
        key_row,
        key_col,
        cyan_row,
        cyan_col,
        anchor_side,
    ) = profile
    key = _make_key(rng, side, mask_index, anchor_side)
    canvas = [[0] * width for _ in range(height)]
    for row in range(side):
        for col in range(side):
            canvas[key_row + row][key_col + col] = key[row][col]
    mask = tuple(tuple(int(cell != 0) for cell in row) for row in key)
    rotated = _rotate_mask_clockwise(mask)
    for tile_row in range(side):
        for tile_col in range(side):
            if not rotated[tile_row][tile_col]:
                continue
            for delta_row in range(scale_h):
                for delta_col in range(scale_w):
                    canvas[
                        cyan_row + tile_row * scale_h + delta_row
                    ][
                        cyan_col + tile_col * scale_w + delta_col
                    ] = 8
    # The source parser is an independent guard on geometry and modal background.
    state = observe(canvas)
    if state["anchor_side"] != anchor_side:
        raise AssertionError("constructed anchor side disagrees with observer")
    return canvas


def _pair(value: list[list[int]], policy: str) -> dict[str, list[list[int]]]:
    return {"input": value, "output": transform(value, policy)}


def _inputs(seed: int, demos: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    digest = hashlib.sha256(
        b"fd588326c845-parametric-input-v1:" + str(seed).encode("ascii")
    ).digest()
    rng = random.Random(digest)
    train = [_scene(rng, profile) for profile in _DEMO_PROFILES[:demos]]
    test = [_scene(rng, profile) for profile in _QUERY_PROFILES]
    visible = [json.dumps(value, separators=(",", ":")) for value in train + test]
    if len(visible) != len(set(visible)):
        raise AssertionError("profile construction produced duplicate inputs")
    return train, test


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 4, 4)
    selected = _settings(settings)
    train_inputs, query_inputs = _inputs(seed, demos)

    # Validate the same setting-neutral teaching inputs against both settings so
    # no setting-dependent retry path can leak into visible geometry.
    for policy in POLICIES:
        teaching = [_pair(value, policy) for value in train_inputs]
        proof = certificate(teaching, query_inputs)
        if proof["survivors"] != [policy]:
            raise AssertionError("teaching inputs do not identify both policies")

    train = [_pair(value, selected) for value in train_inputs]
    test = [_pair(value, selected) for value in query_inputs]
    return {
        "train": train,
        "test": test,
        "program_solution": program(settings),
    }
