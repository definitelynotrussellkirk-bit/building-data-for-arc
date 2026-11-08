"""Generator for bank task 4a5e76e7a1af.

The input is a 3-row library of 3x3 monochrome prototypes, a blank divider
row, and three (prototype index, transform code, output color) triples.  The
output contains the three selected prototypes after code-directed transforms
and recoloring, packed into a fixed 3x11 gallery.
"""
from __future__ import annotations

from itertools import permutations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "4a5e76e7a1af"
TASK_ID = "4a5e76e7a1af"
VERSION = "4.0.0"  # exact axes, branch-complete lessons, shortcut-resistant prototypes
RULE_HASH = "d4a2e13aeda3"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Rows 0-2 hold 3..5 separated 3x3 prototype panels. Row 3 is blank. "
    "Row 4 holds exactly three triples at columns 0, 4, and 8. Each triple "
    "selects a prototype by 1-based index, applies code 1=identity, "
    "2=rotate clockwise, 3=flip left-right, or 4=flip up-down, then "
    "recolors every nonzero cell to the triple's output color. The three "
    "results are packed at columns 0, 4, and 8 of a 3x11 output."
)

INVARIANTS = [
    "the input has five rows and width 4*n_proto-1 for 3..5 prototypes",
    "every prototype is a nonempty monochrome 3x3 4-connected shape",
    "prototype separator columns and the divider row are blank",
    "the program row contains exactly three valid triples at columns 0, 4, 8",
    "the three transform codes are distinct and the three output colors are distinct",
    "at least two prototype indices are used and at least one transform is visibly load-bearing",
    "ordinary generated libraries use pairwise D4-inequivalent asymmetric prototypes",
]

PALETTE_KINDS = ("canonical", "disjoint", "one_overlap")
PROGRAM_PROFILES = ("codes_123", "codes_124", "codes_134", "codes_234")
INDEX_PROFILES = ("distinct", "one_repeat")
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "n_proto": {
        "type": "int",
        "default": "difficulty/sample schedule",
        "valid": "3..5",
        "doc": "Number of 3x3 library prototypes; input width is 4*n_proto-1.",
    },
    "palette_kind": {
        "type": "enum",
        "default": "sample schedule",
        "valid": "canonical|disjoint|one_overlap",
        "doc": "Observable relation between prototype colors and program output colors.",
    },
    "program_profile": {
        "type": "enum",
        "default": "sample schedule",
        "valid": "codes_123|codes_124|codes_134|codes_234",
        "doc": "The exact three-element set of transform codes used in the program row.",
    },
    "index_profile": {
        "type": "enum",
        "default": "sample schedule",
        "valid": "distinct|one_repeat",
        "doc": "Whether the three triples use three indices or exactly two indices.",
    },
}

_PROFILE_CODES = {
    "codes_123": (1, 2, 3),
    "codes_124": (1, 2, 4),
    "codes_134": (1, 3, 4),
    "codes_234": (2, 3, 4),
}
_CODES_TO_PROFILE = {tuple(sorted(codes)): name for name, codes in _PROFILE_CODES.items()}

# Consecutive sample indices form one lesson: four demos and one query.  The
# demos collectively expose all four transform codes, both index modes, and
# all palette relations.  The query uses only already-demonstrated semantics.
_PROGRAM_SCHEDULE = ("codes_123", "codes_124", "codes_134", "codes_234", "codes_234")
_PALETTE_SCHEDULE = ("canonical", "disjoint", "one_overlap", "disjoint", "one_overlap")
_INDEX_SCHEDULE = ("distinct", "distinct", "distinct", "one_repeat", "distinct")
_NPROTO_SCHEDULE = {
    "easy": (3, 3, 4, 3, 4),
    "medium": (3, 4, 4, 5, 3),
    "hard": (4, 5, 5, 3, 5),
    None: (3, 4, 5, 4, 5),
}

_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _as_tuple(grid):
    return tuple(tuple(row) for row in grid)


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return _rotate_cw(_rotate_cw(grid))


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [list(row) for row in reversed(grid)]


def _transform(grid, code):
    if code == 1:
        return [list(row) for row in grid]
    if code == 2:
        return _rotate_cw(grid)
    if code == 3:
        return _flip_lr(grid)
    if code == 4:
        return _flip_ud(grid)
    raise ValueError(f"unsupported transform code {code!r}")


def _binary(grid):
    return tuple(tuple(1 if value else 0 for value in row) for row in grid)


def _d4_variants(grid):
    base = [list(row) for row in grid]
    variants = []
    current = base
    for _ in range(4):
        variants.append(_as_tuple(current))
        variants.append(_as_tuple(_flip_lr(current)))
        current = _rotate_cw(current)
    return tuple(dict.fromkeys(variants))


def _d4_signature(grid):
    return min(_d4_variants(_binary(grid)))


def _connected_nonzero(grid):
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARDINALS:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _shape_catalog():
    """One connected, fully asymmetric representative per D4 orbit."""
    representatives = {}
    for mask in range(1, 1 << 9):
        count = mask.bit_count()
        if not 3 <= count <= 8:
            continue
        shape = [
            [1 if mask & (1 << (3 * r + c)) else 0 for c in range(3)]
            for r in range(3)
        ]
        if not _connected_nonzero(shape):
            continue
        if len({_as_tuple(_transform(shape, code)) for code in (1, 2, 3, 4)}) != 4:
            continue
        signature = _d4_signature(shape)
        representatives.setdefault(signature, shape)
    return tuple(representatives[key] for key in sorted(representatives))


_SHAPE_CATALOG = _shape_catalog()
if len(_SHAPE_CATALOG) < 5:  # import-time invariant, never data-dependent
    raise RuntimeError("insufficient asymmetric 3x3 shape orbits")


def _paint(shape, color):
    return [[color if value else 0 for value in row] for row in shape]


def _paste(grid, panel, top, left):
    for r, row in enumerate(panel):
        for c, value in enumerate(row):
            grid[top + r][left + c] = value


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if overrides.get("n_proto") is not None and type(overrides["n_proto"]) is not int:
        raise ValueError("n_proto must be an integer")
    for name, options in (
        ("palette_kind", PALETTE_KINDS),
        ("program_profile", PROGRAM_PROFILES),
        ("index_profile", INDEX_PROFILES),
    ):
        value = overrides.get(name)
        if value is not None and value not in options:
            raise ValueError(f"{name} must be one of {options!r}")


def _draw_scheduled_choice(ctx, label, all_values, scheduled, overrides):
    if overrides.get(label) is not None:
        return ctx.draw_choice(label, all_values)
    return ctx.draw_choice(label, (scheduled,))


def _draw_n_proto(ctx, slot, difficulty, overrides):
    if overrides.get("n_proto") is not None:
        return ctx.draw_int("n_proto", 3, 5)
    scheduled = _NPROTO_SCHEDULE[difficulty][slot]
    return ctx.draw_int("n_proto", scheduled, scheduled)


def _prototype_colors(kind, n_proto, rng):
    if kind == "canonical":
        return [1] * n_proto
    return rng.sample(list(range(1, 10)), n_proto)


def _program_indices(n_proto, profile, slot, rng, explicit):
    if explicit:
        if profile == "distinct":
            return rng.sample(list(range(1, n_proto + 1)), 3)
        first, second = rng.sample(list(range(1, n_proto + 1)), 2)
        values = [first, first, second]
        rng.shuffle(values)
        return values

    if profile == "one_repeat":
        return [n_proto, 1, n_proto]
    patterns = (
        (2, 3, 1),
        (3, 1, 2),
        (1, 2, 3),
        (2, 3, 1),
        (n_proto, 2, 1),
    )
    return list(patterns[slot])


def _program_codes(profile, slot, rng, explicit):
    codes = list(_PROFILE_CODES[profile])
    if explicit:
        rng.shuffle(codes)
        return codes
    fixed = (
        (1, 2, 3),
        (4, 1, 2),
        (3, 4, 1),
        (2, 3, 4),
        (4, 2, 3),
    )
    return list(fixed[slot])


def _output_colors(kind, proto_colors, indices, codes, rng):
    prototype_set = set(proto_colors)
    required_overlap = {
        "canonical": 0,
        "disjoint": 0,
        "one_overlap": 1,
    }[kind]
    candidates = []
    for colors in permutations(range(1, 10), 3):
        if len(set(colors) & prototype_set) != required_overlap:
            continue
        if any(
            color in (index, code, proto_colors[index - 1])
            for color, index, code in zip(colors, indices, codes)
        ):
            continue
        candidates.append(colors)
    if not candidates:
        raise ValueError(
            "incompatible palette/index/code request leaves no shortcut-resistant colors"
        )
    return list(rng.choice(candidates))


def _extract_prototypes(grid):
    width = len(grid[0])
    return [
        [row[left:left + 3] for row in grid[:3]]
        for left in range(0, width - 2, 4)
    ]


def _extract_triples(grid):
    return [tuple(grid[4][left:left + 3]) for left in (0, 4, 8)]


def _prototype_color(proto):
    colors = {value for row in proto for value in row if value != 0}
    if len(colors) != 1:
        raise ValueError(f"prototype must be monochrome, found {sorted(colors)}")
    return next(iter(colors))


def _infer_palette_kind(proto_colors, output_colors):
    proto_set = set(proto_colors)
    overlap = len(proto_set & set(output_colors))
    if proto_set == {1} and overlap == 0:
        return "canonical"
    if len(proto_set) == len(proto_colors) and overlap == 0:
        return "disjoint"
    if len(proto_set) == len(proto_colors) and overlap == 1:
        return "one_overlap"
    raise ValueError(
        "palette is not canonical, disjoint, or exactly-one-overlap"
    )


def _analysis(grid):
    result = {
        "grid": grid,
        "errors": [],
        "n_proto": 0,
        "prototypes": [],
        "triples": [],
        "palette_kind": None,
        "program_profile": None,
        "index_profile": None,
        "visible_nonidentity": 0,
    }
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        result["errors"].append("grid must be a nonempty list of rows")
        return result
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        result["errors"].append("grid must be rectangular and nonempty")
        return result
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        result["errors"].append("grid values must be integer ARC colors 0..9")
        return result
    if len(grid) != 5:
        result["errors"].append(f"expected 5 input rows, got {len(grid)}")
        return result
    if width not in (11, 15, 19):
        result["errors"].append(f"expected width 11, 15, or 19, got {width}")
        return result

    n_proto = (width + 1) // 4
    prototypes = _extract_prototypes(grid)
    triples = _extract_triples(grid)
    result.update(n_proto=n_proto, prototypes=prototypes, triples=triples)

    for sep in range(3, width, 4):
        if any(grid[r][sep] != 0 for r in range(3)):
            result["errors"].append(f"prototype separator column {sep} must be blank")
    if any(grid[3][c] != 0 for c in range(width)):
        result["errors"].append("row 3 must be entirely blank")
    for sep in (3, 7):
        if grid[4][sep] != 0:
            result["errors"].append(f"program separator column {sep} must be blank")
    if any(grid[4][c] != 0 for c in range(11, width)):
        result["errors"].append("cells after the three program triples must be blank")

    proto_colors = []
    signatures = []
    for position, proto in enumerate(prototypes, start=1):
        count = sum(value != 0 for row in proto for value in row)
        if not 3 <= count <= 8:
            result["errors"].append(
                f"prototype {position} must contain 3..8 nonzero cells, got {count}"
            )
        if not _connected_nonzero(proto):
            result["errors"].append(f"prototype {position} must be 4-connected")
        try:
            proto_colors.append(_prototype_color(proto))
        except ValueError as exc:
            result["errors"].append(f"prototype {position}: {exc}")
        signatures.append(_d4_signature(proto))
    if len(signatures) != len(set(signatures)):
        result["errors"].append("prototype shapes must be pairwise D4-inequivalent")

    indices = [triple[0] for triple in triples]
    codes = [triple[1] for triple in triples]
    output_colors = [triple[2] for triple in triples]
    for position, (index, code, color) in enumerate(triples, start=1):
        if not 1 <= index <= n_proto:
            result["errors"].append(
                f"triple {position} index {index} is outside 1..{n_proto}"
            )
        if code not in (1, 2, 3, 4):
            result["errors"].append(f"triple {position} transform code {code} is outside 1..4")
        if not 1 <= color <= 9:
            result["errors"].append(f"triple {position} output color {color} is outside 1..9")
    if len(set(indices)) not in (2, 3):
        result["errors"].append("the program must use exactly two or three prototype indices")
    else:
        result["index_profile"] = "distinct" if len(set(indices)) == 3 else "one_repeat"
    if len(set(codes)) != 3:
        result["errors"].append("the program must use three distinct transform codes")
    else:
        result["program_profile"] = _CODES_TO_PROFILE.get(tuple(sorted(codes)))
        if result["program_profile"] is None:
            result["errors"].append("transform-code set is not a declared program profile")
    if len(set(output_colors)) != 3:
        result["errors"].append("the three output colors must be distinct")

    if not result["errors"]:
        try:
            result["palette_kind"] = _infer_palette_kind(proto_colors, output_colors)
        except ValueError as exc:
            result["errors"].append(str(exc))

    if all(1 <= index <= n_proto and code in (1, 2, 3, 4) for index, code, _ in triples):
        result["visible_nonidentity"] = sum(
            code != 1 and _transform(prototypes[index - 1], code) != prototypes[index - 1]
            for index, code, _ in triples
        )
        if result["visible_nonidentity"] == 0:
            result["errors"].append(
                "no selected non-identity transform visibly changes its prototype"
            )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural task grammar; accepts every canonical train/test input."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def observe_overrides(grid):
    """Recover every exact declared axis from a valid returned input grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "n_proto": analysis["n_proto"],
        "palette_kind": analysis["palette_kind"],
        "program_profile": analysis["program_profile"],
        "index_profile": analysis["index_profile"],
    }


def semantic_observables(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    indices = [triple[0] for triple in analysis["triples"]]
    codes = [triple[1] for triple in analysis["triples"]]
    colors = [triple[2] for triple in analysis["triples"]]
    return {
        **observe_overrides(grid),
        "indices": indices,
        "codes": codes,
        "output_colors": colors,
        "visible_nonidentity": analysis["visible_nonidentity"],
        "uses_extended_index": any(index > 3 for index in indices),
    }


def rule_mirror(grid):
    """Exact Python mirror for tests; the canonical Racket rule is authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(3, 11, 0)
    for left, (index, code, color) in zip((0, 4, 8), analysis["triples"]):
        transformed = _transform(analysis["prototypes"][index - 1], code)
        recolored = [
            [color if value != 0 else 0 for value in row]
            for row in transformed
        ]
        _paste(output, recolored, 0, left)
    return output


def _teaching_errors(grid):
    """Stronger generated-only gate; canonical inputs may lawfully be weaker."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    errors = []
    prototypes = analysis["prototypes"]
    triples = analysis["triples"]
    if any(
        len({_as_tuple(_transform(proto, code)) for code in (1, 2, 3, 4)}) != 4
        for proto in prototypes
    ):
        errors.append("generated prototypes must distinguish all four transform codes")
    if any(
        code != 1 and _transform(prototypes[index - 1], code) == prototypes[index - 1]
        for index, code, _ in triples
    ):
        errors.append("every selected non-identity transform must be visibly load-bearing")
    proto_colors = [_prototype_color(proto) for proto in prototypes]
    for position, (index, code, color) in enumerate(triples, start=1):
        if color in (index, code, proto_colors[index - 1]):
            errors.append(
                f"triple {position} output color leaks index, code, or selected source color"
            )
    truth = rule_mirror(grid)
    competitors = {
        "identity_only": _apply_variant(grid, transform_map={1: 1, 2: 1, 3: 1, 4: 1}),
        "first_prototype": _apply_variant(grid, force_index=1),
        "source_colors": _apply_variant(grid, use_program_colors=False),
    }
    for name, output in competitors.items():
        if output == truth:
            errors.append(f"generated scene is ambiguous with competitor {name!r}")
    return errors


def _apply_variant(
    grid,
    *,
    transform_map=None,
    positional_lookup=False,
    force_index=None,
    use_program_colors=True,
):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    transform_map = transform_map or {1: 1, 2: 2, 3: 3, 4: 4}
    output = full_grid(3, 11, 0)
    for slot, (left, triple) in enumerate(zip((0, 4, 8), analysis["triples"]), start=1):
        index, code, color = triple
        selected = force_index if force_index is not None else (slot if positional_lookup else index)
        selected = max(1, min(selected, analysis["n_proto"]))
        proto = analysis["prototypes"][selected - 1]
        transformed = _transform(proto, transform_map[code])
        paint_color = color if use_program_colors else _prototype_color(proto)
        panel = [[paint_color if value else 0 for value in row] for row in transformed]
        _paste(output, panel, 0, left)
    return output


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _facts(grid):
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


def _has_code(code):
    return lambda grid: (
        (analysis := _facts(grid)) is not None
        and any(triple[1] == code for triple in analysis["triples"])
    )


def _witness_repeated_index(grid):
    analysis = _facts(grid)
    return analysis is not None and analysis["index_profile"] == "one_repeat"


def _witness_extended_index(grid):
    analysis = _facts(grid)
    return analysis is not None and any(triple[0] > 3 for triple in analysis["triples"])


def _witness_palette(kind):
    return lambda grid: (
        (analysis := _facts(grid)) is not None
        and analysis["palette_kind"] == kind
    )


def _witness_all_nonidentity_visible(grid):
    analysis = _facts(grid)
    if analysis is None:
        return False
    nonidentity = sum(triple[1] != 1 for triple in analysis["triples"])
    return analysis["visible_nonidentity"] == nonidentity


SEMANTIC_WITNESSES = {
    "identity_code": _has_code(1),
    "rotate_cw_code": _has_code(2),
    "flip_lr_code": _has_code(3),
    "flip_ud_code": _has_code(4),
    "repeated_prototype_lookup": _witness_repeated_index,
    "extended_library_lookup": _witness_extended_index,
    "canonical_palette": _witness_palette("canonical"),
    "disjoint_palette": _witness_palette("disjoint"),
    "one_overlap_palette": _witness_palette("one_overlap"),
    "all_selected_transforms_visible": _witness_all_nonidentity_visible,
}


_COMPETING_RULES = {
    "identity_only": lambda grid: _apply_variant(
        grid, transform_map={1: 1, 2: 1, 3: 1, 4: 1}
    ),
    "swap_rotation_and_lr": lambda grid: _apply_variant(
        grid, transform_map={1: 1, 2: 3, 3: 2, 4: 4}
    ),
    "swap_rotation_and_ud": lambda grid: _apply_variant(
        grid, transform_map={1: 1, 2: 4, 3: 3, 4: 2}
    ),
    "swap_reflections": lambda grid: _apply_variant(
        grid, transform_map={1: 1, 2: 2, 3: 4, 4: 3}
    ),
    "positional_lookup": lambda grid: _apply_variant(grid, positional_lookup=True),
    "first_prototype": lambda grid: _apply_variant(grid, force_index=1),
    "keep_source_colors": lambda grid: _apply_variant(grid, use_program_colors=False),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons still compatible with documented shortcut rules."""
    reasons = []
    episodes = list(demos) + [query]
    labels = [f"demo {index}" for index in range(len(demos))] + ["query"]
    for label, episode in zip(labels, episodes):
        grid = episode.get("input")
        errors = self_check(grid)
        if errors:
            reasons.append(f"{label}: malformed input: {'; '.join(errors)}")
            continue
        truth = rule_mirror(grid)
        if episode.get("output") is not None and episode.get("output") != truth:
            reasons.append(f"{label}: output does not match the task rule")
    if reasons:
        return reasons

    demonstrated_codes = {
        triple[1]
        for demo in demos
        for triple in _analysis(demo["input"])["triples"]
    }
    missing = sorted(set((1, 2, 3, 4)) - demonstrated_codes)
    if missing:
        reasons.append(f"demonstrations omit transform code(s) {missing}")

    truth = rule_mirror(query["input"])
    for name, competitor in _COMPETING_RULES.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != truth:
                reasons.append(
                    f"competing rule {name!r} fits every demo but changes the query answer"
                )
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = int(sample_index) % (EXAMPLES_NEEDED + 1)
    n_proto = _draw_n_proto(ctx, slot, difficulty, overrides)
    palette_kind = _draw_scheduled_choice(
        ctx,
        "palette_kind",
        PALETTE_KINDS,
        _PALETTE_SCHEDULE[slot],
        overrides,
    )
    program_profile = _draw_scheduled_choice(
        ctx,
        "program_profile",
        PROGRAM_PROFILES,
        _PROGRAM_SCHEDULE[slot],
        overrides,
    )
    index_profile = _draw_scheduled_choice(
        ctx,
        "index_profile",
        INDEX_PROFILES,
        _INDEX_SCHEDULE[slot],
        overrides,
    )

    shape_rng = ctx.draw_rng("prototype_shapes")
    palette_rng = ctx.draw_rng("palette")
    program_rng = ctx.draw_rng("program")
    bases = shape_rng.sample(list(_SHAPE_CATALOG), n_proto)
    prototypes = []
    proto_colors = _prototype_colors(palette_kind, n_proto, palette_rng)
    for base, color in zip(bases, proto_colors):
        oriented = shape_rng.choice(_d4_variants(base))
        prototypes.append(_paint(oriented, color))

    indices = _program_indices(
        n_proto,
        index_profile,
        slot,
        program_rng,
        overrides.get("index_profile") is not None,
    )
    codes = _program_codes(
        program_profile,
        slot,
        program_rng,
        overrides.get("program_profile") is not None,
    )
    output_colors = _output_colors(
        palette_kind,
        proto_colors,
        indices,
        codes,
        palette_rng,
    )
    triples = list(zip(indices, codes, output_colors))

    width = 4 * n_proto - 1
    grid = full_grid(5, width, 0)
    for position, prototype in enumerate(prototypes):
        _paste(grid, prototype, 0, 4 * position)
    for left, (index, code, color) in zip((0, 4, 8), triples):
        grid[4][left:left + 3] = [index, code, color]

    errors = _teaching_errors(grid)
    if errors:
        raise AssertionError("generated invalid teaching scene: " + "; ".join(errors))
    return grid
