"""Single-authority signature registry for ARC-Racket v2 core 0.1.

No compatibility aliases are present here.  Legacy spellings are accepted only
by the offline migrator, which rewrites them before type checking.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, Mapping

from .types import (
    AXIS,
    BOOLEAN,
    BOUNDING_BOX,
    CELL_SET,
    COLOR,
    DIRECTION,
    GRID,
    INTEGER,
    OBJECT,
    OBJECT_LIST,
    POSITION,
    REFLECTION,
    ROTATION,
    V2Type,
)


Tier = Literal["A", "B", "C"]
LoweringKind = Literal["direct", "enum-head", "enum-string", "template"]


@dataclass(frozen=True, slots=True)
class Lowering:
    kind: LoweringKind
    target: str | None = None
    enum_arg: int | None = None
    cases: Mapping[str, str] = MappingProxyType({})


@dataclass(frozen=True, slots=True)
class Signature:
    name: str
    params: tuple[V2Type, ...]
    result: V2Type
    tier: Tier
    lowering: Lowering
    capability: str

    @property
    def arity(self) -> int:
        return len(self.params)


@dataclass(frozen=True, slots=True)
class Constant:
    name: str
    type: V2Type
    runtime_value: str
    capability: str


def _direct(name: str) -> Lowering:
    return Lowering("direct", target=name)


def _cases(**items: str) -> Mapping[str, str]:
    return MappingProxyType(dict(items))


_SIGNATURES = (
    # Tier A: semantic grid operations.
    Signature("transpose", (GRID,), GRID, "A", _direct("transpose"), "swap row and column axes"),
    Signature("mirror", (GRID, REFLECTION), GRID, "A", Lowering("enum-head", enum_arg=1, cases=_cases(LR="flip-lr", UD="flip-ud")), "reflect across one typed axis"),
    Signature("rotate", (GRID, ROTATION), GRID, "A", Lowering("enum-head", enum_arg=1, cases=_cases(CW="rotate-cw", CCW="rotate-ccw", R180="rotate-180")), "rotate by a typed quarter/half turn"),
    Signature("overlay", (GRID, GRID, COLOR), GRID, "A", _direct("overlay"), "place non-background cells of the second grid over the first"),
    Signature("pack", (GRID, DIRECTION, COLOR), GRID, "A", Lowering("enum-string", target="gravity", enum_arg=1, cases=_cases(N="up", E="right", S="down", W="left")), "pack non-background cells toward a direction"),
    Signature("crop-content", (GRID, COLOR), GRID, "A", _direct("crop-to-content"), "crop to the bounding box of non-background cells"),
    Signature("scale-up", (GRID, INTEGER), GRID, "A", _direct("upscale"), "repeat every cell by an integer factor"),
    Signature("scale-down", (GRID, INTEGER), GRID, "A", _direct("downscale"), "sample the top-left cell of fixed-size blocks"),
    Signature("fill-holes", (GRID, COLOR, COLOR), GRID, "A", _direct("fill-all-enclosed"), "fill every enclosed background region"),
    Signature("compress-period", (GRID,), GRID, "A", _direct("compress-grid"), "remove consecutive duplicate rows, then consecutive duplicate columns"),
    Signature("self-tile", (GRID,), GRID, "A", _direct("self-tile"), "use the input as both pattern and stamp"),
    Signature("concat", (AXIS, GRID, GRID), GRID, "A", Lowering("enum-head", enum_arg=0, cases=_cases(H="hconcat", V="vconcat")), "concatenate two grids along a typed axis"),
    Signature("tile", (GRID, INTEGER, INTEGER), GRID, "A", _direct("tile"), "repeat a grid by row and column counts"),
    Signature("recolor", (GRID, COLOR, COLOR), GRID, "A", _direct("recolor"), "replace one color globally"),
    Signature("swap-colors", (GRID, COLOR, COLOR), GRID, "A", _direct("swap-colors"), "swap two colors globally"),
    Signature("rows", (GRID,), INTEGER, "A", _direct("rows"), "grid height"),
    Signature("cols", (GRID,), INTEGER, "A", _direct("cols"), "grid width"),
    Signature("at", (GRID, INTEGER, INTEGER), COLOR, "A", _direct("at"), "read one cell"),
    Signature("set-cell", (GRID, INTEGER, INTEGER, COLOR), GRID, "C", _direct("set-cell"), "pure single-cell update"),
    Signature("empty-grid", (INTEGER, INTEGER, COLOR), GRID, "C", _direct("empty-grid"), "construct a uniform grid"),
    Signature("subgrid", (GRID, INTEGER, INTEGER, INTEGER, INTEGER), GRID, "C", _direct("subgrid"), "extract inclusive rectangular corners"),
    Signature("blank-like", (GRID, COLOR), GRID, "A", Lowering("template", target="blank-like"), "construct a same-size blank canvas"),
    # Tier B: intentionally fixed-arity functional glue.
    Signature("+", (INTEGER, INTEGER), INTEGER, "B", _direct("+"), "integer addition"),
    Signature("-", (INTEGER, INTEGER), INTEGER, "B", _direct("-"), "integer subtraction"),
    Signature("*", (INTEGER, INTEGER), INTEGER, "B", _direct("*"), "integer multiplication"),
    Signature("quotient", (INTEGER, INTEGER), INTEGER, "B", _direct("quotient"), "integer quotient"),
    Signature("mod", (INTEGER, INTEGER), INTEGER, "B", _direct("mod"), "non-negative modulo"),
    Signature("min", (INTEGER, INTEGER), INTEGER, "B", _direct("min"), "integer minimum"),
    Signature("max", (INTEGER, INTEGER), INTEGER, "B", _direct("max"), "integer maximum"),
    Signature("=", (INTEGER, INTEGER), BOOLEAN, "B", _direct("="), "integer equality"),
    Signature("<", (INTEGER, INTEGER), BOOLEAN, "B", _direct("<"), "integer less-than"),
    Signature("<=", (INTEGER, INTEGER), BOOLEAN, "B", _direct("<="), "integer less-than-or-equal"),
    Signature(">", (INTEGER, INTEGER), BOOLEAN, "B", _direct(">"), "integer greater-than"),
    Signature(">=", (INTEGER, INTEGER), BOOLEAN, "B", _direct(">="), "integer greater-than-or-equal"),
    Signature("zero?", (INTEGER,), BOOLEAN, "B", _direct("zero?"), "integer zero predicate"),
    Signature("color=?", (COLOR, COLOR), BOOLEAN, "B", _direct("="), "color equality without overloading integer equality"),
)

SIGNATURES: Mapping[str, Signature] = MappingProxyType({item.name: item for item in _SIGNATURES})

_CONSTANTS = (
    Constant("C0", COLOR, "0", "ARC color 0 (black/background by convention only)"),
    Constant("C1", COLOR, "1", "ARC color 1 (blue)"),
    Constant("C2", COLOR, "2", "ARC color 2 (red)"),
    Constant("C3", COLOR, "3", "ARC color 3 (green)"),
    Constant("C4", COLOR, "4", "ARC color 4 (yellow)"),
    Constant("C5", COLOR, "5", "ARC color 5 (grey)"),
    Constant("C6", COLOR, "6", "ARC color 6 (magenta)"),
    Constant("C7", COLOR, "7", "ARC color 7 (orange)"),
    Constant("C8", COLOR, "8", "ARC color 8 (azure)"),
    Constant("C9", COLOR, "9", "ARC color 9 (maroon)"),
    Constant("N", DIRECTION, '"up"', "north/up direction"),
    Constant("E", DIRECTION, '"right"', "east/right direction"),
    Constant("S", DIRECTION, '"down"', "south/down direction"),
    Constant("W", DIRECTION, '"left"', "west/left direction"),
    Constant("LR", REFLECTION, "flip-lr", "left-right reflection"),
    Constant("UD", REFLECTION, "flip-ud", "up-down reflection"),
    Constant("CW", ROTATION, "rotate-cw", "clockwise quarter-turn"),
    Constant("CCW", ROTATION, "rotate-ccw", "counter-clockwise quarter-turn"),
    Constant("R180", ROTATION, "rotate-180", "half-turn"),
    Constant("H", AXIS, "hconcat", "horizontal concatenation axis"),
    Constant("V", AXIS, "vconcat", "vertical concatenation axis"),
)

# Kept as name -> tuple so expected-type disambiguation remains a first-class
# mechanism if a future release intentionally reuses a compact atom.
_constants_by_name: dict[str, list[Constant]] = {}
for _constant in _CONSTANTS:
    _constants_by_name.setdefault(_constant.name, []).append(_constant)
CONSTANTS: Mapping[str, tuple[Constant, ...]] = MappingProxyType(
    {name: tuple(values) for name, values in _constants_by_name.items()}
)

LEGACY_ALIASES: Mapping[str, str] = MappingProxyType({
    "flip-lr": "mirror ... LR",
    "flip-ud": "mirror ... UD",
    "rotate-cw": "rotate ... CW",
    "rotate-ccw": "rotate ... CCW",
    "rotate-180": "rotate ... R180",
    "gravity": "pack",
    "crop-to-content": "crop-content",
    "upscale": "scale-up",
    "downscale": "scale-down",
    "fill-all-enclosed": "fill-holes",
    "compress-grid": "compress-period",
    "hconcat": "concat H",
    "vconcat": "concat V",
})

RESERVED_BINDERS = frozenset(
    {"rule!", "input", "r", "c", "v"}
    | set(SIGNATURES)
    | set(CONSTANTS)
    | {"let*", "if", "and", "or", "not", "build-grid", "cellmap"}
)


def signature_rows() -> list[dict[str, object]]:
    """Stable JSON-friendly registry dump used by docs and audits."""

    return [
        {
            "name": sig.name,
            "params": [str(item) for item in sig.params],
            "result": str(sig.result),
            "tier": sig.tier,
            "lowering_kind": sig.lowering.kind,
            "runtime_target": sig.lowering.target,
            "capability": sig.capability,
        }
        for sig in sorted(SIGNATURES.values(), key=lambda item: item.name)
    ]


def constant_rows() -> list[dict[str, str]]:
    return [
        {
            "name": item.name,
            "type": str(item.type),
            "runtime_value": item.runtime_value,
            "capability": item.capability,
        }
        for item in sorted(_CONSTANTS, key=lambda item: (item.name, item.type.name))
    ]
