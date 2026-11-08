"""Small independently constructed grids on the diagonal checkerboard lattice."""


def board(height, width, phase=0):
    return [[int((r+c) % 2 == phase) for c in range(width)] for r in range(height)]


def rectangle(grid, top, size, color, caps=None, *, fill=False):
    r0, c0 = top
    nu, nv = size
    u0, v0 = r0+c0, r0-c0
    u1, v1 = u0+2*(nu-1), v0+2*(nv-1)
    def put(u, v, value):
        r, c = (u+v)//2, (u-v)//2
        if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
            assert grid[r][c] in (1, value), (r, c, grid[r][c], value)
            grid[r][c] = value
    for u in range(u0, u1+1, 2):
        for v in range(v0, v1+1, 2):
            if fill or u in (u0, u1) or v in (v0, v1):
                put(u, v, color)
    for side, value in (caps or {}).items():
        if side in ("NW", "SE"):
            u = u0-2 if side == "NW" else u1+2
            for v in range(v0, v1+1, 2):
                put(u, v, value)
        else:
            v = v0-2 if side == "NE" else v1+2
            for u in range(u0, u1+1, 2):
                put(u, v, value)
    return grid


def cases():
    result = []
    def add(name, h, w, top, size, color, caps, **kw):
        g = board(h, w, sum(top) % 2)
        rectangle(g, top, size, color, caps, **kw)
        result.append((name, g))
        return g
    add("minimum_no_extension", 5, 5, (0,2), (3,3), 3, {})
    add("minimum_clipped_NE", 5, 7, (0,2), (3,3), 6, {"NE":8})
    add("all_sides_distinct", 13, 14, (4,6), (3,3), 9,
        {"NW":2,"NE":4,"SE":5,"SW":6})
    add("nonsquare_3x6", 19, 23, (5,11), (3,6), 7,
        {"NW":3,"NE":8,"SE":2,"SW":9})
    add("nonsquare_6x3_phase1", 23, 19, (5,10), (6,3), 4,
        {"NW":9,"NE":3,"SE":8,"SW":2})
    add("maximum_6x5", 30, 30, (8,14), (6,5), 8,
        {"NW":2,"NE":4,"SE":6,"SW":9})
    for side,top in (("NW",(0,4)),("NE",(0,2)),("SW",(0,4)),("SE",(0,2))):
        add("clipped_"+side,5,7,top,(3,3),5,{side:7})
    g = board(30,30)
    rectangle(g,(4,6),(3,3),3,{"NE":6})
    rectangle(g,(18,22),(3,3),6,{"NE":3})
    result.append(("two_cores_color_role_swap",g))
    g = board(30,30)
    rectangle(g,(4,6),(3,3),3,{"NE":5})
    rectangle(g,(15,17),(4,5),3,{"NE":5})
    result.append(("two_cores_unequal_sizes",g))
    g=add("foreground_on_ray",25,25,(10,12),(3,3),3,{"NE":8})
    g[7][15]=9
    g=add("attached_core_tail",19,19,(7,9),(3,3),3,{"NE":8})
    g[6][8]=3
    g=add("notched_core",19,19,(7,9),(3,3),3,{"NE":8})
    g[8][8]=1
    add("filled_core_distractor",19,19,(7,9),(3,3),3,{"NE":8},fill=True)
    g=add("disconnected_same_color_interior",25,25,(8,12),(5,5),3,{"NE":8})
    g[12][12]=3
    g=add("unanchored_stroke",23,23,(12,12),(3,3),4,{"NE":8})
    for r,c in ((3,3),(4,4),(5,5)):
        g[r][c]=7
    return result
