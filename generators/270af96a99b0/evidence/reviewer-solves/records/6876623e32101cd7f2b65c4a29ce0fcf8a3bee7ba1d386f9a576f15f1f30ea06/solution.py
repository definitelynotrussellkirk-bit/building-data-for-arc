def solve(grid):
    """Extract the nonzero objects, move the leftmost object to the end,
    and order the other objects by height before top-aligning them.
    """
    if not grid or not grid[0]:
        return []

    by_color = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                by_color.setdefault(value, []).append((r, c))

    objects = []
    for color, cells in by_color.items():
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        h = r1 - r0 + 1
        w = c1 - c0 + 1
        crop = [[0] * w for _ in range(h)]
        for r, c in cells:
            crop[r - r0][c - c0] = color
        solid = len(cells) == h * w
        objects.append({
            "color": color,
            "crop": crop,
            "height": h,
            "width": w,
            "solid": solid,
            "left": c0,
        })

    anchor = min(objects, key=lambda obj: obj["left"])
    ordered = sorted(
        (obj for obj in objects if obj is not anchor),
        key=lambda obj: (obj["height"], obj["left"]),
    ) + [anchor]

    out_h = max(obj["height"] for obj in ordered)
    out_w = sum(obj["width"] for obj in ordered) + max(0, len(ordered) - 1)
    out = [[0] * out_w for _ in range(out_h)]

    offset = 0
    for obj in ordered:
        for r, row in enumerate(obj["crop"]):
            for c, value in enumerate(row):
                out[r][offset + c] = value
        offset += obj["width"] + 1
    return out
