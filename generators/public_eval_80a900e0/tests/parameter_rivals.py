"""Independent diagonal-lattice rectangle model and predeclared rival bank.

Authored from the official examples and the stated family contract, without
reading the task implementation. Rectangle search enumerates matching corners
and complete perimeters rather than finding connected components.
"""
from collections import defaultdict
from functools import lru_cache


def _inside(point, height, width):
    r, c = point
    return 0 <= r < height and 0 <= c < width


def _rc(u, v):
    return ((u + v) // 2, (u - v) // 2)


@lru_cache(maxsize=4096)
def _rectangles(key, allow_tail=False, filled=False):
    points = defaultdict(set)
    for r, row in enumerate(key):
        for c, value in enumerate(row):
            if value not in (0, 1):
                points[value].add((r + c, r - c))
    found = []
    for color, occupied in sorted(points.items()):
        us, vs = defaultdict(set), defaultdict(set)
        for u, v in occupied:
            us[v].add(u)
            vs[u].add(v)
        for u0, v0 in sorted(occupied):
            for u1 in sorted(u for u in us[v0] if u >= u0 + 4):
                for v1 in sorted(v for v in vs[u0] if v >= v0 + 4):
                    if (u1, v1) not in occupied:
                        continue
                    border = {(u, v) for u in range(u0, u1 + 1, 2)
                              for v in (v0, v1)}
                    border.update((u, v) for v in range(v0, v1 + 1, 2)
                                  for u in (u0, u1))
                    required = ({(u, v) for u in range(u0, u1 + 1, 2)
                                 for v in range(v0, v1 + 1, 2)} if filled else border)
                    if not required <= occupied:
                        continue
                    if not allow_tail and any(
                        neighbor in occupied and neighbor not in required
                        for u, v in required
                        for neighbor in ((u-2, v), (u+2, v), (u, v-2), (u, v+2))
                    ):
                        continue
                    found.append((u0, u1, v0, v1, color))
    return tuple(found)


def features(grid, *, allow_tail=False, filled=False):
    key = tuple(tuple(row) for row in grid)
    height, width = len(key), len(key[0])
    result = []
    for u0, u1, v0, v1, color in _rectangles(key, allow_tail, filled):
        sides = (
            ("NW", (-1, -1), [_rc(u0-2, v) for v in range(v0, v1+1, 2)]),
            ("SE", (1, 1), [_rc(u1+2, v) for v in range(v0, v1+1, 2)]),
            ("NE", (-1, 1), [_rc(u, v0-2) for u in range(u0, u1+1, 2)]),
            ("SW", (1, -1), [_rc(u, v1+2) for u in range(u0, u1+1, 2)]),
        )
        caps = []
        for side, direction, points in sides:
            visible = [p for p in points if _inside(p, height, width)]
            if not visible:
                continue
            colors = {key[r][c] for r, c in visible}
            if len(colors) != 1 or next(iter(colors)) in (0, 1, color):
                continue
            caps.append({"side": side, "direction": direction,
                         "color": next(iter(colors)), "points": points,
                         "visible": visible})
        result.append({"bounds": (u0, u1, v0, v1), "color": color,
                       "size": ((u1-u0)//2+1, (v1-v0)//2+1), "caps": caps})
    return result


def solve(grid, beam="walls", **options):
    """Paint only original carrier cells; conflicting rays are out of scope."""
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    objects = features(grid, allow_tail=options.get("allow_tail", False),
                       filled=options.get("filled_core", False))
    if options.get("fixed_core") is not None:
        objects = [o for o in objects if o["color"] == options["fixed_core"]]
    if options.get("square_only"):
        objects = [o for o in objects if o["size"][0] == o["size"][1]]
    if options.get("three_only"):
        objects = [o for o in objects if o["size"] == (3, 3)]
    if options.get("first_core"):
        objects = objects[:1]
    if options.get("minimum_two") and len(objects) < 2:
        objects = []
    if options.get("largest_core") and objects:
        largest = max(o["size"][0] * o["size"][1] for o in objects)
        objects = [o for o in objects if o["size"][0]*o["size"][1] == largest]
    claims = defaultdict(set)
    for obj in objects:
        caps = obj["caps"][:1] if options.get("first_cap") else obj["caps"]
        for cap in caps:
            if options.get("complete_caps") and len(cap["visible"]) != len(cap["points"]):
                continue
            if options.get("skip_side") == cap["side"]:
                continue
            if options.get("fixed_cap") is not None and cap["color"] != options["fixed_cap"]:
                continue
            dr, dc = cap["direction"]
            if options.get("reverse"):
                dr, dc = -dr, -dc
            if options.get("along_cap"):
                dr, dc = dr, -dc
            if options.get("clockwise"):
                dr, dc = dc, -dr
            if options.get("grid_center"):
                mr = sum(r for r, _ in cap["visible"]) / len(cap["visible"])
                mc = sum(c for _, c in cap["visible"]) / len(cap["visible"])
                dr = -1 if mr < (height-1)/2 else 1
                dc = -1 if mc < (width-1)/2 else 1
            points = cap["points"] if beam == "solid" else [cap["points"][0], cap["points"][-1]]
            if options.get("endpoint") == "first":
                points = cap["points"][:1]
            elif options.get("endpoint") == "last":
                points = cap["points"][-1:]
            elif options.get("endpoint") == "middle":
                points = [cap["points"][len(cap["points"])//2]]
            color = obj["color"] if options.get("core_color") else cap["color"]
            if options.get("constant_color") is not None:
                color = options["constant_color"]
            limit = options.get("distance", max(height, width))
            for r, c in points:
                for distance in range(1, limit + 1):
                    rr, cc = r + dr * distance, c + dc * distance
                    if not _inside((rr, cc), height, width):
                        break
                    if options.get("stop_original") and grid[rr][cc] != 1:
                        break
                    if options.get("stop_drawn") and output[rr][cc] != 1:
                        break
                    if grid[rr][cc] == 1 or options.get("overwrite"):
                        output[rr][cc] = color
                        claims[(rr, cc)].add(color)
    if not options and any(len(colors) > 1 for colors in claims.values()):
        raise ValueError("Conflicting beam colors are outside the independent oracle domain")
    return output


# Freeze these names and mechanisms before comparing with generated lessons.
RIVALS = (
    ("identity", "Leave the input unchanged.", {"identity": True}),
    ("walls_always", "Always extend cap endpoints only.", {"mode": "walls"}),
    ("solid_always", "Always extend every cap cell.", {"mode": "solid"}),
    ("green_core_only", "Only color 3 can identify a core.", {"fixed_core": 3}),
    ("first_core_only", "Process just the first recognized core.", {"first_core": True}),
    ("two_core_gate", "Act only when at least two cores are present.", {"minimum_two": True}),
    ("largest_core_only", "Process only cores with maximal lattice area.", {"largest_core": True}),
    ("square_cores_only", "Ignore nonsquare diagonal rectangles.", {"square_only": True}),
    ("three_by_three_only", "Recognize only the original 3x3 lattice cores.", {"three_only": True}),
    ("complete_caps_only", "Require every cap cell to be inside the canvas.", {"complete_caps": True}),
    ("cyan_caps_only", "Only color 8 caps emit rays.", {"fixed_cap": 8}),
    ("first_cap_only", "Extend just the first colored cap of each core.", {"first_cap": True}),
    ("inward", "Extend toward the core rather than away from it.", {"reverse": True}),
    ("parallel_to_cap", "Extend along the cap instead of perpendicular to it.", {"along_cap": True}),
    ("clockwise_direction", "Rotate each outward direction clockwise.", {"clockwise": True}),
    ("canvas_center_direction", "Choose direction relative to the canvas center.", {"grid_center": True}),
    ("first_endpoint", "Extend only the first full-side endpoint.", {"endpoint": "first"}),
    ("last_endpoint", "Extend only the last full-side endpoint.", {"endpoint": "last"}),
    ("middle_ray", "Extend only the middle cap cell.", {"endpoint": "middle"}),
    ("core_color", "Paint extensions in the associated core color.", {"core_color": True}),
    ("constant_cyan", "Paint every extension cyan.", {"constant_color": 8}),
    ("one_step", "Extend each ray by exactly one cell.", {"distance": 1}),
    ("three_steps", "Extend each ray by at most three cells.", {"distance": 3}),
    ("five_steps", "Extend each ray by at most five cells.", {"distance": 5}),
    ("overwrite_foreground", "Overwrite existing foreground on ray paths.", {"overwrite": True}),
    ("stop_at_original_foreground", "Stop a ray at its first original foreground cell.", {"stop_original": True}),
    ("stop_at_drawn_foreground", "Stop at original or previously drawn foreground.", {"stop_drawn": True}),
    ("perimeter_with_tail", "Allow same-color attachments to the core perimeter.", {"allow_tail": True}),
    ("filled_core", "Require a filled diagonal rectangle instead of a hollow core.", {"filled_core": True}),
    ("omit_NW", "Never extend northwest caps.", {"skip_side": "NW"}),
    ("omit_NE", "Never extend northeast caps.", {"skip_side": "NE"}),
    ("omit_SE", "Never extend southeast caps.", {"skip_side": "SE"}),
    ("omit_SW", "Never extend southwest caps.", {"skip_side": "SW"}),
)


def rival_output(name, grid, beam):
    item = next(item for item in RIVALS if item[0] == name)
    kwargs = dict(item[2])
    if kwargs.pop("identity", False):
        return [row[:] for row in grid]
    return solve(grid, kwargs.pop("mode", beam), **kwargs)
