"""Semantic generator for ARC task 724d5770b986 (source f0df5ff0).

Every blue (1) input cell selects its clipped 3x3 Moore neighbourhood.
Paint selected black (0) cells blue and preserve every originally non-black
cell.  Multiple neighbourhoods form a union; distractors are blockers rather
than targets.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "724d5770b986"
TASK_ID = "724d5770b986"
VERSION = "3.0.0"
RULE_HASH = "e39c8a4e2b02"
SUMMARY = "Expand every blue cell into a clipped 3x3 blue neighbourhood, filling only black cells and preserving all colored blockers."
INVARIANTS = [
    "background is black (0) and trigger cells are blue (1)",
    "each input blue cell selects every in-bounds cell at Chebyshev distance at most one",
    "a selected cell changes to blue exactly when its original value was black",
    "all originally non-black cells retain their color, including non-blue blockers inside selected neighbourhoods",
    "overlapping neighbourhoods form a union and boundary neighbourhoods clip to the canvas",
    "every accepted lesson contains blue triggers, colored blockers, and at least one visible black-to-blue change",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "isolated_sparse",
    "isolated_dense",
    "blocked_dense",
    "edge_clipped",
    "corner_clipped",
    "touching_blues",
    "overlapping_neighbourhoods",
    "mixed_geometry",
    "single_decoy_color",
    "max_palette_dense",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four official dense families and ten boundary/topology/blocker contrasts",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = (
    "006200060000004/000002000260400/630104000006000/004060010000300/603000000322004/420202000060060/000026060040000/060000400046000/000606003340660/460313004002600/003204060043600/040000020004000/000100030300220/600000200010043/000003400200000",
    "300000092302330/222300357000270/032200070500050/000020000900292/800300128200000/300320007020300/003000300560200/010236002302060/028030006070030/023080030100600/703002000000670/002052000700000/090200000200300/002023300010062/029005230000200",
    "390000000839308/000404003027702/033090900002000/000090403033010/010088030293000/090800003007003/007224709000008/040070008033270/033020102330004/000308000703010/080030990073900/443030780407309/701330701700409/300078800809000/007009800483000",
    "000700607000003/204037007070008/000780627010272/010020026000078/600601000200864/004660048008087/876000077448007/300100300007080/008686761660407/087078070800804/440003002003848/008010837678087/000080060300300/060000631030013/460000800022006",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _blue_positions(grid):
    return frozenset(
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 1
    )


def _family_key(grid):
    counts = Counter(value for row in grid for value in row if value != 1)
    return len(grid), len(grid[0]), _blue_positions(grid), tuple(sorted(counts.items()))


_PUBLIC_FAMILIES = {_family_key(grid): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 8 <= len(grid) <= 30:
        return ["input must contain eight through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 8 <= len(grid[0]) <= 30:
        return ["input must contain eight through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _selected_cells(grid, blues=None):
    height, width = len(grid), len(grid[0])
    blues = _blue_positions(grid) if blues is None else blues
    return frozenset(
        (row, col)
        for trigger_row, trigger_col in blues
        for row in range(max(0, trigger_row - 1), min(height, trigger_row + 2))
        for col in range(max(0, trigger_col - 1), min(width, trigger_col + 2))
    )


def rule_mirror(grid):
    """Exact Python mirror of the canonical original-input neighbourhood rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    for row, col in _selected_cells(grid):
        if grid[row][col] == 0:
            output[row][col] = 1
    return output


def _pair_counts(blues):
    adjacent = 0
    overlapping = 0
    ordered = sorted(blues)
    for index, (row, col) in enumerate(ordered):
        for other_row, other_col in ordered[index + 1 :]:
            distance = max(abs(row - other_row), abs(col - other_col))
            adjacent += distance == 1
            overlapping += distance == 2
    return adjacent, overlapping


def _general_profile(facts):
    adjacent = facts["adjacent_pairs"]
    overlapping = facts["overlap_pairs"]
    if adjacent and overlapping:
        return "mixed_geometry"
    if adjacent:
        return "touching_blues"
    if overlapping:
        return "overlapping_neighbourhoods"
    if facts["corner_blues"]:
        return "corner_clipped"
    if facts["edge_blues"]:
        return "edge_clipped"
    if facts["decoy_color_count"] == 1:
        return "single_decoy_color"
    if facts["decoy_colors"] == frozenset(range(2, 10)) and facts["decoy_density"] > 0.25:
        return "max_palette_dense"
    if facts["decoy_density"] <= 0.22:
        return "isolated_sparse"
    if facts["decoy_density"] > 0.25 and facts["blocked_ratio"] >= 0.34:
        return "blocked_dense"
    if facts["decoy_density"] > 0.25 and facts["blocked_ratio"] < 0.34:
        return "isolated_dense"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    height, width = len(grid), len(grid[0])
    blues = _blue_positions(grid)
    decoys = frozenset(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 1)
    )
    selected = _selected_cells(grid, blues)
    blocked = selected & decoys
    paintable = frozenset(cell for cell in selected if grid[cell[0]][cell[1]] == 0)
    adjacent, overlapping = _pair_counts(blues)
    decoy_colors = frozenset(grid[row][col] for row, col in decoys)
    facts = {
        "height": height,
        "width": width,
        "blue_count": len(blues),
        "blues": blues,
        "decoy_count": len(decoys),
        "decoy_colors": decoy_colors,
        "decoy_color_count": len(decoy_colors),
        "decoy_density": len(decoys) / (height * width),
        "selected_count": len(selected),
        "blocked_count": len(blocked),
        "blocked_ratio": len(blocked) / len(selected) if selected else 0.0,
        "paintable_count": len(paintable),
        "adjacent_pairs": adjacent,
        "overlap_pairs": overlapping,
        "edge_blues": sum(row in (0, height - 1) or col in (0, width - 1) for row, col in blues),
        "corner_blues": sum(row in (0, height - 1) and col in (0, width - 1) for row, col in blues),
    }
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if profile is None:
        profile = _PUBLIC_FAMILIES.get(_family_key(grid))
    if profile is None:
        profile = _general_profile(facts)
    if not blues:
        errors.append("at least one blue trigger is required")
    if not decoys:
        errors.append("at least one non-blue colored blocker is required")
    if not paintable:
        errors.append("at least one selected black cell must visibly change")
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared density, boundary, or blue-topology profile")
    output = None if errors else rule_mirror(grid)
    if output is not None:
        changed = frozenset(
            (row, col)
            for row in range(height)
            for col in range(width)
            if output[row][col] != grid[row][col]
        )
        if changed != paintable:
            errors.append("changed cells must exactly equal selected original-black cells")
        if any(output[row][col] != grid[row][col] for row, col in decoys):
            errors.append("colored blockers must be preserved")
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def canonical_family_signature(grid):
    return _PUBLIC_FAMILIES.get(_family_key(grid)) if not _valid_grid(grid) else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _limits(difficulty):
    if difficulty == "easy":
        return 9, 13
    if difficulty == "medium":
        return 13, 18
    if difficulty == "hard":
        return 17, 24
    return 11, 20


def _far_enough(candidate, positions, minimum=3):
    row, col = candidate
    return all(max(abs(row - other_row), abs(col - other_col)) >= minimum for other_row, other_col in positions)


def _add_isolated(positions, candidates, count, rng):
    candidates = list(candidates)
    rng.shuffle(candidates)
    for candidate in candidates:
        if _far_enough(candidate, positions):
            positions.add(candidate)
        if len(positions) >= count:
            return
    raise AssertionError("could not place requested isolated blue triggers")


def _blue_layout(profile, height, width, count, rng):
    interior = [(row, col) for row in range(1, height - 1) for col in range(1, width - 1)]
    if profile == "corner_clipped":
        positions = {rng.choice(((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)))}
        _add_isolated(positions, interior, count, rng)
        return positions
    if profile == "edge_clipped":
        edge = (
            [(0, col) for col in range(1, width - 1)]
            + [(height - 1, col) for col in range(1, width - 1)]
            + [(row, 0) for row in range(1, height - 1)]
            + [(row, width - 1) for row in range(1, height - 1)]
        )
        positions = {rng.choice(edge)}
        _add_isolated(positions, interior, count, rng)
        return positions
    center_row, center_col = height // 2, width // 2
    if profile == "touching_blues":
        positions = {(center_row, center_col), (center_row, center_col + 1)}
        _add_isolated(positions, interior, count, rng)
        return positions
    if profile == "overlapping_neighbourhoods":
        positions = {(center_row, center_col - 1), (center_row, center_col + 1)}
        _add_isolated(positions, interior, count, rng)
        return positions
    if profile == "mixed_geometry":
        positions = {(center_row, center_col - 1), (center_row, center_col), (center_row, center_col + 1)}
        _add_isolated(positions, interior, count, rng)
        return positions
    positions = set()
    _add_isolated(positions, interior, count, rng)
    return positions


def _put_decoys(grid, blues, palette, target, blockers_per_blue, rng):
    height, width = len(grid), len(grid[0])
    selected = _selected_cells(grid, blues)
    blocked_candidates = list(selected - blues)
    rng.shuffle(blocked_candidates)
    chosen = set()
    for blue in sorted(blues):
        local = [cell for cell in blocked_candidates if max(abs(cell[0] - blue[0]), abs(cell[1] - blue[1])) <= 1 and cell not in chosen]
        rng.shuffle(local)
        chosen.update(local[:blockers_per_blue])
    outside = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in blues and (row, col) not in selected
    ]
    rng.shuffle(outside)
    candidates = outside + [cell for cell in blocked_candidates if cell not in chosen]
    for color, cell in zip(palette, candidates):
        chosen.add(cell)
        grid[cell[0]][cell[1]] = color
    for cell in candidates:
        if len(chosen) >= target:
            break
        if cell in chosen:
            continue
        chosen.add(cell)
        grid[cell[0]][cell[1]] = rng.choice(palette)
    for cell in chosen:
        if grid[cell[0]][cell[1]] == 0:
            grid[cell[0]][cell[1]] = rng.choice(palette)
    if len(chosen) < target:
        raise AssertionError("could not place requested distractor field")


def _public_nuisance(profile, rng):
    source = _PUBLIC_INPUTS[profile]
    grid = [row[:] for row in source]
    positions = [(row, col) for row in range(15) for col in range(15) if grid[row][col] != 1]
    values = [grid[row][col] for row, col in positions]
    rng.shuffle(values)
    for (row, col), value in zip(positions, values):
        grid[row][col] = value
    return grid


def _general_scene_once(profile, difficulty, rng):
    lo, hi = _limits(difficulty)
    height, width = rng.randint(lo, hi), rng.randint(lo, hi)
    count = rng.randint(3, min(8, max(3, (height * width) // 38)))
    if profile == "mixed_geometry":
        count = max(count, 3)
    grid = [[0] * width for _ in range(height)]
    blues = _blue_layout(profile, height, width, count, rng)
    for row, col in blues:
        grid[row][col] = 1

    if profile == "single_decoy_color":
        palette = [rng.choice(range(2, 10))]
    elif profile == "max_palette_dense":
        palette = list(range(2, 10))
    else:
        palette = list(range(2, 10))
        rng.shuffle(palette)
        palette = palette[: rng.randint(3, 7)]
    cells = height * width
    if profile == "isolated_sparse":
        target = rng.randint(max(len(palette), 8), max(len(palette), int(cells * 0.18)))
        blockers = 1
    elif profile == "blocked_dense":
        target = max(len(palette), int(cells * rng.uniform(0.34, 0.44)))
        blockers = 4
    elif profile == "single_decoy_color":
        target = max(8, int(cells * rng.uniform(0.14, 0.21)))
        blockers = 1
    else:
        target = max(len(palette), int(cells * rng.uniform(0.29, 0.44)))
        blockers = 1
    _put_decoys(grid, blues, palette, target, blockers, rng)
    return grid


def _general_scene(profile, difficulty, rng):
    for _ in range(80):
        try:
            grid = _general_scene_once(profile, difficulty, rng)
        except AssertionError:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct valid scene profile {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES * 5 + GENERAL_PROFILES * 3)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        if overrides.get("scene_profile") is not None:
            return [row[:] for row in _PUBLIC_INPUTS[profile]]
        grid = _public_nuisance(profile, ctx.draw_rng("public_nuisance"))
    else:
        grid = _general_scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid blue-neighbourhood lesson: " + "; ".join(errors))
    return grid
