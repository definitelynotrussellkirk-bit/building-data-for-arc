"""Independent, pure shortcut rivals for task-local regression and review.

These helpers import the independent geometry probe, never production generator
helpers. They expose the observed color, marker-pattern and double-tie shortcuts
without changing the selected canonical rule.
"""
from reference_probe import marker_offsets, project_offsets, scene


def _output_from(facts, source, offsets):
    blank = facts["blank"]
    marker_color = source["colors"].most_common()[1][0]
    blank_color = next(iter(blank["colors"]))
    output = [[blank_color] * blank["w"] for _ in range(blank["h"])]
    projected = project_offsets(
        offsets,
        source_h=source["h"],
        source_w=source["w"],
        output_h=blank["h"],
        output_w=blank["w"],
    )
    for row, col in projected:
        output[row][col] = marker_color
    return output


def multicolumn_source(grid):
    """Choose the first object with markers in several columns, ignoring width."""
    facts = scene(grid)
    candidates = [
        component
        for component in facts["markers"]
        if len({col for _, col in marker_offsets(grid, component)}) > 1
    ]
    source = candidates[0] if candidates else facts["markers"][0]
    return _output_from(facts, source, marker_offsets(grid, source))


def color_coded_pattern(grid):
    """Infer the old source pattern from background/pose; ignore actual markers.

    The v3.0.0 sampler set background = sample_index % 10 and selected one of
    five fixed patterns by sample_index % 5. Its source occupied the upper-left
    template slot before reflections, so the source bbox reveals the pose.
    """
    facts = scene(grid)
    source = facts["source"]
    height, width = source["h"], source["w"]
    patterns = (
        ((1, 1), (height - 2, width - 2)),
        ((height // 2, 1), (1, width - 2), (height - 2, width - 2)),
        ((1, width // 2), (height - 2, 1), (height - 2, width - 2)),
        ((height // 2, width // 2), (1, 1)),
        ((height // 2, width // 2), (1, 1), (height - 2, width - 2)),
    )
    offsets = patterns[grid[0][0] % 5]
    if source["r0"] != 1:
        offsets = tuple((height - 1 - row, col) for row, col in offsets)
    if source["c0"] != 1:
        offsets = tuple((row, width - 1 - col) for row, col in offsets)
    return _output_from(facts, source, offsets)


def diagonal_double_tie(grid):
    """Mirror one-axis ties correctly but zip two-axis anchors diagonally."""
    facts = scene(grid)
    source, blank = facts["source"], facts["blank"]
    marker_color = source["colors"].most_common()[1][0]
    blank_color = next(iter(blank["colors"]))
    output = [[blank_color] * blank["w"] for _ in range(blank["h"])]
    for row, col in marker_offsets(grid, source):
        row_tie = 2 * row == source["h"] - 1
        col_tie = 2 * col == source["w"] - 1
        if row_tie and col_tie:
            positions = (
                (row, col),
                (blank["h"] - 1 - row, blank["w"] - 1 - col),
            )
        else:
            positions = project_offsets(
                ((row, col),),
                source_h=source["h"],
                source_w=source["w"],
                output_h=blank["h"],
                output_w=blank["w"],
            )
        for rr, cc in positions:
            if 0 <= rr < blank["h"] and 0 <= cc < blank["w"]:
                output[rr][cc] = marker_color
    return output
