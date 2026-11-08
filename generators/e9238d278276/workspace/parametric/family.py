"""Native canonical and signal-ranked mixed-gravity family.

The canonical setting packs every column's non-zero values upward while
preserving their top-to-bottom order.  The alternative measures the unique
all-9 signal column's height, uses it as a one-based rank among the other
active columns from left to right, packs every column upward, and then packs
only the selected payload column downward.  Input scenes do not depend on the
private setting.
"""
from __future__ import annotations

import copy
import hashlib
import random
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
POLICIES = ("all_up", "signal_ranked_down")
SETTINGS = tuple({"gravity_policy": policy} for policy in POLICIES)

_TRAIN_PROFILES = (
    ((10, 12), 2, 5, 0),
    ((13, 16), 4, 6, 3),
    ((16, 20), 1, 6, 5),
    ((19, 23), 5, 7, 1),
    ((23, 27), 3, 8, 4),
    ((27, 29), 2, 9, 6),
)
_QUERY_PROFILES = (
    ((14, 16), 1, 5, 2),
    ((19, 21), 3, 6, 6),
    ((24, 27), 5, 8, 1),
    ((30, 30), 2, 12, 0),
)


def _policy(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"gravity_policy"}
        or type(settings["gravity_policy"]) is not str
        or settings["gravity_policy"] not in POLICIES
    ):
        raise ValueError(
            "settings must contain only gravity_policy='all_up' or "
            "'signal_ranked_down'"
        )
    return settings["gravity_policy"]


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: Any) -> str:
    policy = _policy(settings)
    name = "canonical.rkt" if policy == "all_up" else "signal_ranked_down.rkt"
    return (HERE / name).read_text()


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be a rectangular 1..30 ARC grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must use exact integer colors 0..9")
    return value


def _column_values(grid: Any, column: int) -> list[int]:
    source = _grid(grid)
    if type(column) is not int or not 0 <= column < len(source[0]):
        raise ValueError("column is outside the grid")
    return [row[column] for row in source if row[column] != 0]


def _active_columns(grid: Any) -> list[int]:
    source = _grid(grid)
    return [
        column
        for column in range(len(source[0]))
        if any(row[column] != 0 for row in source)
    ]


def apply_all_up(grid: Any) -> list[list[int]]:
    source = _grid(grid)
    height, width = len(source), len(source[0])
    out = [[0] * width for _ in range(height)]
    for column in range(width):
        for row, value in enumerate(_column_values(source, column)):
            out[row][column] = value
    return out


def _signal_and_payload(grid: Any) -> tuple[int, list[int]]:
    source = _grid(grid)
    active = _active_columns(source)
    signals = [
        column
        for column in active
        if _column_values(source, column)
        and all(value == 9 for value in _column_values(source, column))
    ]
    if len(signals) != 1:
        raise ValueError("input must contain exactly one nonempty all-9 signal column")
    signal = signals[0]
    rank = len(_column_values(source, signal))
    if not 1 <= rank <= 5:
        raise ValueError("signal column height must be in 1..5")
    payload = [column for column in active if column != signal]
    if len(payload) < 5 or rank > len(payload):
        raise ValueError("signal rank requires at least five payload columns")
    if any(any(value == 9 for value in _column_values(source, column)) for column in payload):
        raise ValueError("payload columns must not contain signal color 9")
    return signal, payload


def signal_intermediate(grid: Any) -> dict[str, Any]:
    signal, payload = _signal_and_payload(grid)
    rank = len(_column_values(grid, signal))
    target = payload[rank - 1]
    values = _column_values(grid, target)
    return {
        "signal_column": signal,
        "rank": rank,
        "payload_columns": list(payload),
        "target_column": target,
        "target_values": list(values),
        "target_count": len(values),
    }


def _pack_one_down(grid: Any, column: int, values: Iterable[int] | None = None) -> list[list[int]]:
    source = _grid(grid)
    height = len(source)
    out = apply_all_up(source)
    chosen = list(_column_values(source, column) if values is None else values)
    if not chosen or len(chosen) >= height:
        raise ValueError("selected column must be nonempty with at least one zero slot")
    for row in range(height):
        out[row][column] = 0
    start = height - len(chosen)
    for offset, value in enumerate(chosen):
        out[start + offset][column] = value
    return out


def apply_ranked_down(grid: Any, rank: Any) -> list[list[int]]:
    rank = _exact_int(rank, "rank", 1, 64)
    _, payload = _signal_and_payload(grid)
    if rank > len(payload):
        raise ValueError("rank exceeds the payload column count")
    return _pack_one_down(grid, payload[rank - 1])


def transform(grid: Any, settings: Any) -> list[list[int]]:
    policy = _policy(settings)
    if policy == "all_up":
        return apply_all_up(grid)
    return apply_ranked_down(grid, signal_intermediate(grid)["rank"])


def _rng(seed: int, split: str, index: int, salt: str) -> random.Random:
    raw = f"e9238d278276-native-v1:{seed}:{split}:{index}:{salt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _payload_columns(width: int, count: int) -> list[int]:
    columns = [round(index * (width - 1) / (count - 1)) for index in range(count)]
    if len(set(columns)) != count or columns[0] != 0 or columns[-1] != width - 1:
        raise ValueError("payload column spacing is not injective")
    return columns


def _choose_rows(
    height: int,
    count: int,
    rng: random.Random,
    *,
    force_top: bool = False,
    force_bottom: bool = False,
) -> list[int]:
    forced = ({0} if force_top else set()) | ({height - 1} if force_bottom else set())
    available = [row for row in range(height) if row not in forced]
    rows = sorted(forced | set(rng.sample(available, count - len(forced))))
    if rows == list(range(count)):
        rows[-1] = height - 1
        rows = sorted(set(rows))
    if len(rows) != count:
        raise ValueError("row construction lost uniqueness")
    return rows


def _payload_values(seed: int, offset: int, column_index: int, count: int) -> list[int]:
    values = [
        1 + ((seed + offset * 3 + column_index * 5 + position * 3 + position // 2) % 8)
        for position in range(count)
    ]
    if values == sorted(values, reverse=True):
        values = values[1:] + values[:1]
    return values


def _scene(
    seed: int,
    split: str,
    index: int,
    size: tuple[int, int],
    rank: int,
    payload_count: int,
    offset: int,
) -> list[list[int]]:
    height, width = size
    grid = [[0] * width for _ in range(height)]
    payload = _payload_columns(width, payload_count)
    signal_choices = [column for column in range(1, width - 1) if column not in payload]
    signal = signal_choices[(seed + offset * 7 + index * 3) % len(signal_choices)]

    for ordinal, column in enumerate(payload):
        if height == 30:
            count = 8 + ((seed + offset + ordinal) % 4)
        else:
            count = 3 + ((seed + offset + ordinal) % min(4, height - 4))
        count = min(count, height - 2)
        rng = _rng(seed, split, index, f"payload-{ordinal}")
        rows = _choose_rows(
            height,
            count,
            rng,
            force_top=ordinal == 0,
            force_bottom=ordinal == payload_count - 1,
        )
        values = _payload_values(seed, offset, ordinal, count)
        for row, value in zip(rows, values, strict=True):
            grid[row][column] = value

    signal_rows = list(range(height - rank, height))
    for row in signal_rows:
        grid[row][signal] = 9

    observed_signal, observed_payload = _signal_and_payload(grid)
    if observed_signal != signal or observed_payload != payload:
        raise ValueError("constructed signal/payload grammar drifted")
    if len(_column_values(grid, signal)) != rank:
        raise ValueError("constructed signal rank drifted")
    if transform(grid, {"gravity_policy": "all_up"}) == transform(
        grid, {"gravity_policy": "signal_ranked_down"}
    ):
        raise ValueError("constructed settings do not change the answer")
    return grid


def _profile_pairs(
    seed: int,
    split: str,
    profiles: tuple[tuple[tuple[int, int], int, int, int], ...],
    count: int,
    settings: dict[str, str],
) -> list[dict[str, list[list[int]]]]:
    pairs = []
    for index, (size, rank, payload_count, offset) in enumerate(profiles[:count]):
        grid = _scene(seed, split, index, size, rank, payload_count, offset)
        pairs.append({"input": grid, "output": transform(grid, settings)})
    return pairs


def _target_by_selector(grid: Any, selector: str) -> int:
    _, payload = _signal_and_payload(grid)
    if selector.startswith("fixed_"):
        rank = int(selector.removeprefix("fixed_"))
        return payload[rank - 1]
    if selector == "longest":
        return max(payload, key=lambda column: (len(_column_values(grid, column)), -column))
    if selector == "shortest":
        return min(payload, key=lambda column: (len(_column_values(grid, column)), column))
    raise ValueError(f"unknown selector {selector!r}")


RIVALS = (
    "canonical_all_up",
    "all_down",
    "fixed_1",
    "fixed_2",
    "fixed_3",
    "fixed_4",
    "fixed_5",
    "reverse_signal_rank",
    "signal_column_mod_rank",
    "longest",
    "shortest",
    "sort_selected_descending",
)


def _all_down(grid: Any) -> list[list[int]]:
    source = _grid(grid)
    height, width = len(source), len(source[0])
    out = [[0] * width for _ in range(height)]
    for column in range(width):
        values = _column_values(source, column)
        for offset, value in enumerate(values):
            out[height - len(values) + offset][column] = value
    return out


def _rival_output(grid: Any, name: str) -> list[list[int]]:
    if name == "canonical_all_up":
        return apply_all_up(grid)
    if name == "all_down":
        return _all_down(grid)
    if name.startswith("fixed_"):
        return _pack_one_down(grid, _target_by_selector(grid, name))
    signal, payload = _signal_and_payload(grid)
    rank = len(_column_values(grid, signal))
    if name == "reverse_signal_rank":
        return _pack_one_down(grid, payload[-rank])
    if name == "signal_column_mod_rank":
        return _pack_one_down(grid, payload[signal % len(payload)])
    if name in {"longest", "shortest"}:
        return _pack_one_down(grid, _target_by_selector(grid, name))
    if name == "sort_selected_descending":
        target = payload[rank - 1]
        return _pack_one_down(grid, target, sorted(_column_values(grid, target), reverse=True))
    raise ValueError(f"undeclared rival {name!r}")


def teaching_check(episode: Any, settings: Any) -> dict[str, Any]:
    policy = _policy(settings)
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a demonstration list")
    demos = episode["train"]
    survivors = [
        {"gravity_policy": candidate}
        for candidate in POLICIES
        if all(
            transform(pair["input"], {"gravity_policy": candidate}) == pair["output"]
            for pair in demos
        )
    ]
    rivals = [
        name
        for name in RIVALS
        if not (policy == "all_up" and name == "canonical_all_up")
    ]
    surviving_rivals = [
        name
        for name in rivals
        if all(_rival_output(pair["input"], name) == pair["output"] for pair in demos)
    ]
    return {
        "survivors": survivors,
        "surviving_rivals": surviving_rivals,
        "rivals_tested": rivals,
        "basis": "demonstrations_only",
        "scope": "two declared settings and twelve named shortcut families",
    }


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)
    policy = _policy(settings)
    normalized = {"gravity_policy": policy}
    episode = {
        "train": _profile_pairs(seed, "train", _TRAIN_PROFILES, demos, normalized),
        "test": _profile_pairs(seed, "test", _QUERY_PROFILES, queries, normalized),
        "program_solution": program(normalized),
        "seed": seed,
        "settings": copy.deepcopy(normalized),
    }
    inputs = [repr(pair["input"]) for split in ("train", "test") for pair in episode[split]]
    if len(inputs) != len(set(inputs)):
        raise ValueError("all demonstration and query inputs must be distinct")
    check = teaching_check(episode, normalized)
    if check["survivors"] != [normalized] or check["surviving_rivals"]:
        raise ValueError(f"constructive demonstrations failed teaching contrasts: {check}")
    return episode


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    if (
        type(episode) is not dict
        or type(episode.get("train")) is not list
        or type(episode.get("test")) is not list
    ):
        raise ValueError("episode must contain train and test lists")
    _exact_int(query_index, "query_index", 0, len(episode["test"]) - 1)
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
