"""
ARC REPL specification — source of truth for macros, artifact types, and cost guards.

Adapted from rack/core pattern. The model issues macro commands, the executor
runs them, and returns structured artifacts the model can reference.

PHASES:
  OBSERVE  — analyze training pairs, compute features, form hypotheses
  SOLVE    — build and test transformation rules
  SUBMIT   — apply rule to test input, verify, commit answer
"""

# ============================================================
# Macro vocabulary
# ============================================================

# OBSERVE phase: analyze grids, compute features, explore
OBSERVE_MACROS = frozenset({
    "load!",        # load a training pair into env
    "feature!",     # compute a named feature (diff, enclosure, lattice, etc.)
    "inspect!",     # examine a grid region / object / cell
    "objects!",     # extract objects from a grid
    "compare!",     # compare two grids or two features
    "observe!",     # free-form note (model reasoning trace)
})

# SOLVE phase: build and test rules
SOLVE_MACROS = frozenset({
    "transform!",   # apply a grid transform (rotate, flip, recolor, etc.)
    "compose!",     # chain multiple transforms
    "test!",        # apply current rule to a train pair, compare to expected
    "verify!",      # check if a condition holds
    "rewrite!",     # modify current rule
    "undo!",        # revert last transform
})

# SUBMIT phase: finalize
SUBMIT_MACROS = frozenset({
    "apply!",       # apply rule to test input
    "submit!",      # commit answer
})

ALL_MACROS = OBSERVE_MACROS | SOLVE_MACROS | SUBMIT_MACROS

# ============================================================
# Artifact type system
# ============================================================

ARTIFACT_PREFIXES = {
    "@": "grid",        # loaded grids (@1 = train_0_input, @2 = train_0_output, ...)
    "#": "feature",     # computed features (#1 = diff of pair 0, ...)
    "_": "result",      # transform results (_1 = rotated grid, ...)
    "!": "check",       # verification results (!1 = True/False, ...)
    "~": "objects",     # extracted objects (~1 = [obj1, obj2, ...])
    "◊": "note",        # observations (◊1 = "lattice detected, 4x6 tiles")
}

# ============================================================
# Cost guards — prevent runaway computation
# ============================================================

COST_GUARDS = {
    "max_grid_size": 30 * 30,       # max cells in a grid
    "max_objects": 200,              # max objects to extract
    "max_transforms": 50,            # max transforms in a compose chain
    "max_test_pairs": 20,            # max test! calls per session
    "max_turns": 100,                # max total REPL turns
    "max_flood_fill": 30 * 30,      # max cells in flood fill
}

# ============================================================
# Grid transform registry (what transform! can call)
# ============================================================

TRANSFORMS = {
    # Geometric
    "rotate_cw",        # 90° clockwise
    "rotate_ccw",       # 90° counter-clockwise
    "rotate_180",       # 180°
    "flip_lr",          # mirror left-right
    "flip_ud",          # mirror up-down
    "transpose",        # swap rows/cols

    # Color
    "recolor",          # map one color to another
    "swap_colors",      # swap two colors
    "fill_color",       # fill region with color

    # Spatial
    "crop",             # extract subgrid by bbox
    "pad",              # add border
    "tile",             # repeat grid NxM
    "shift",            # translate by (dr, dc)
    "overlay",          # place one grid on top of another

    # Object-level
    "move_object",      # translate an object
    "remove_object",    # delete an object (fill with bg)
    "copy_object",      # duplicate to new position
    "recolor_object",   # change an object's color

    # Structural
    "fill_enclosed",    # flood-fill enclosed regions
    "fill_region",      # flood-fill from a seed point
    "draw_line",        # draw a line between two points
    "mirror_region",    # mirror a subregion across an axis
}

# ============================================================
# Feature registry (what feature! can compute)
# ============================================================

FEATURES = {
    "diff",             # cell-level delta between input/output
    "change_type",      # vanished / appeared / recolored per cell
    "change_mask",      # binary: changed or not
    "enclosure",        # enclosed regions in grid
    "lattice",          # lattice/tile structure detection
    "objects",          # connected components
    "symmetry",         # mirror/rotation symmetries
    "color_map",        # color-to-color mapping
    "color_roles",      # invariant/source/target/mixed
    "transitions",      # from→to color counts
    "input_invariant",  # what's same across all inputs
    "output_invariant", # what's same across all outputs
}
