"""Fresh input sampler for extrapolated additive shapes and a marked crop.

The five constructive grammars share one inference law: align the spatial
sequence, undo its palette permutation, continue periodic translated support
additions, then crop the requested future member.  These builders are also
retained in the native resource closure; focused tests compare every input.
Ordinary generate returns only the input. Its authoritative label is Racket.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "public_eval_20a9e565"
TASK_ID = "public_eval_20a9e565"
RULE_TASK_ID = "ee_20a9e565"
VERSION = "1.0.0"
RULE_HASH = "874ebadbdaacd8d477d4b5230651677eb1a22346d0c25393b075267cc6b71fcb"
SUMMARY = "Infer repeating additive growth and palette changes, then reconstruct the gray-marked future crop."
FAMILIES = ("stems", "ladders", "lobes", "waves", "arches")
AXES = {
    "shape_family": {"type":"enum", "default":"private profile", "valid":"stems|ladders|lobes|waves|arches",
                     "doc":"Constructive geometry; every profile obeys the same additive-shell rule."},
    "sequence_axis": {"type":"enum", "default":"rng", "valid":"rows|columns",
                      "doc":"Axis carrying the sequence, with either increasing or decreasing spatial direction."},
}
INVARIANTS = [
    "Zero background and exactly two opposite gray L crop markers.",
    "At least three complete objects, separated by one constant positive projection gap.",
    "Object support strictly grows after alignment; retained cells determine a full palette permutation.",
    "Every added-support component track repeats a geometry with a fixed displacement.",
    "Whole and new-shell labels are derived independently from constructive future coordinates.",
    "The marked crop contains inherited cells and genuinely new cells; missing sequence steps are allowed.",
]


def validate_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid needs 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid needs 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid needs rectangular exact integer colors 0..9")


def _box(cells):
    return (min(r for r,c in cells), min(c for r,c in cells),
            max(r for r,c in cells), max(c for r,c in cells))


def _inside(point, box):
    r,c = point
    top,left,bottom,right = box
    return top <= r <= bottom and left <= c <= right


def _transform(grid, turns, mirror):
    grid = [row[::-1] if mirror else row[:] for row in grid]
    for _ in range(turns):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def _transform_box(box, height, width, turns, mirror):
    points = [(box[0],box[1]),(box[0],box[3]),(box[2],box[1]),(box[2],box[3])]
    if mirror:
        points = [(r,width-1-c) for r,c in points]
    for _ in range(turns):
        points = [(c,height-1-r) for r,c in points]
        height,width = width,height
    return _box(points)


def _default_family(seed, index):
    if index < 6:
        return ("lobes","waves","arches","ladders","stems","lobes")[index]
    if 100 <= index <= 103:
        return ("stems","arches","waves", "lobes" if seed % 2 == 0 else "ladders")[index-100]
    return FAMILIES[index % len(FAMILIES)]


def _grammar(ctx, family, index, stress):
    """Return a direct nth-object constructor, without solving its input."""
    palette = tuple(ctx.draw_distinct_colors("palette", n=3, exclude={0,5}))
    if family == "stems":
        width = 2 if index == 4 else 3 if index == 100 else ctx.draw_int("initial_width",2,3)
        gap = ctx.draw_int("object_gap",1,2 if width == 2 else 1)
        bar_gap = ctx.draw_int("bar_separation",2,4)
        extra = ctx.draw_int("stem_extension",1,3)
        increment = ctx.draw_int("stem_increment",1,2)
        period = ctx.draw_int("palette_period",2,3)
        def shape(n):
            color = palette[n % period]
            result = {(r,0):color for r in range(-(bar_gap+extra+n*increment),1)}
            result.update({(r,c):color for r in (0,-bar_gap) for c in range(width+n)})
            return result
        return shape, 1, 4, 0, gap, period, dict(initial_width=width,bar_gap=bar_gap,
            stem_extension=extra,stem_increment=increment)
    if family == "ladders":
        if stress:
            width, gap, skip, first_height, increment = 5,1,0,7,4
        else:
            width = 3 if index == 3 else ctx.draw_int("ladder_width",3,5)
            feasible = [(gap,skip) for gap in (1,2) for skip in (0,1)
                        if (5+skip)*width+(4+skip)*gap <= 30]
            gap,skip = ctx.draw_choice("ladder_layout",feasible)
            first_height = ctx.draw_choice("first_ladder_height",(3,5,7))
            increment = ctx.draw_choice("ladder_height_increment",(2,4))
        period = ctx.draw_int("palette_period",2,3)
        def shape(n):
            return {(r,c):palette[n % period]
                    for r in range(first_height+n*increment) for c in range(width)
                    if r % 2 == 0 or c in (0,width-1)}
        return shape,1,4,skip,gap,period,dict(width=width,initial_height=first_height,
            height_increment=increment)
    if family == "lobes":
        width = 2 if index == 0 else 3 if index in (5,103) else ctx.draw_int("lobe_width",2,3)
        gap = ctx.draw_int("object_gap",1,2 if width == 2 else 1)
        asymmetric = True if index == 0 else ctx.draw_choice("offset_lower_colors",(False,True))
        def shape(n):
            result = {}
            for layer in range(n+1):
                side = width-1 if layer % 2 == 0 else 0
                centers = (0,) if layer == 0 else (-2*layer,2*layer)
                for center in centers:
                    offset = int(asymmetric and center > 0)
                    color = palette[(layer+offset) % 3]
                    result.update({(center,c):color for c in range(width)})
                    result[center-1,side] = color
                    result[center+1,side] = color
            return result
        # Different observed counts separate demo5 from the even-seed lobe
        # stress query independently of palette, placement and orientation.
        count = 5 if index == 5 else 6
        return shape,1,count,0,gap,1,dict(width=width,layer_color_period=3,
            lower_color_offset=int(asymmetric))
    if family == "waves":
        amplitude = 2 if index == 1 else 1 if index == 102 else ctx.draw_int("wave_amplitude",1,2)
        skip = 1 if index == 1 else ctx.draw_int("skipped_steps",0,1)
        gap = ctx.draw_int("object_gap",1,2)
        period = 2*amplitude+1
        def shape(n):
            extent = (n//2)*period + (n%2)*amplitude
            left,right = -extent,2*amplitude+1+extent
            color = palette[n % 2]
            result = {}
            for row in range(amplitude+1):
                phases = {(amplitude-row)%period,(amplitude-row+1)%period,
                          (amplitude+row)%period,(amplitude+row+1)%period}
                result.update({(row,col):color for col in range(left,right+1)
                               if col % period in phases})
            return result
        return shape,0,4,skip,gap,2,dict(amplitude=amplitude,texture_period=period,
            alternating_side_growth=[amplitude,amplitude+1])
    if family == "arches":
        arm = 2 if index == 2 else 3 if index == 101 else ctx.draw_int("arch_arm",2,3)
        gap = ctx.draw_int("object_gap",1,2)
        def shape(n):
            color = palette[n % 2]
            result = {(0,c):color for c in range(-arm,arm+1)}
            result[1,-arm] = color
            result[1,arm] = color
            for layer in range(1,n+1):
                outer = (layer+1)*arm
                inner = layer*arm
                outer_color = palette[(n+layer) % 2]
                inner_color = palette[(n+layer+1) % 2]
                for side in (-1,1):
                    for distance in range(inner,outer+1):
                        result[2*layer,side*distance] = outer_color
                    result[2*layer+1,side*outer] = outer_color
                    result[2*layer+1,side*inner] = inner_color
            return result
        return shape,0,3,0,gap,2,dict(arm=arm,vertical_layer_step=2)
    raise ValueError("unknown constructive family")


def _crop_options(target, shell, full_box):
    top,left,bottom,right = full_box
    candidates = [full_box]
    for trim in (1,2):
        candidates.extend(((top+trim,left,bottom,right),(top,left+trim,bottom,right),
                           (top,left,bottom-trim,right),(top,left,bottom,right-trim)))
    if bottom-top >= 6:
        candidates.extend((((top+bottom)//2,left,bottom,right),
                           (top,left,(top+bottom)//2,right)))
    inherited = target.keys()-shell.keys()
    return [box for box in candidates if box[2]-box[0]+1 >= 2 and box[3]-box[1]+1 >= 2
            and (box[2]-box[0]+1,box[3]-box[1]+1) != (2,2)
            and any(_inside(p,box) for p in shell) and any(_inside(p,box) for p in inherited)]


def scene_record(seed, index, stress=False, *, shape_family=None, sequence_axis=None, difficulty=None):
    """Construct future coordinates first; the input contains only old objects and markers."""
    if type(seed) is not int or not 0 <= seed <= 2**63-1:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")
    if type(stress) is not bool:
        raise TypeError("stress must be boolean")
    if shape_family is not None and (type(shape_family) is not str or shape_family not in FAMILIES):
        raise ValueError("invalid shape_family")
    if sequence_axis is not None and (type(sequence_axis) is not str or sequence_axis not in ("rows","columns")):
        raise ValueError("invalid sequence_axis")
    ctx = gen_ctx(seed=seed,sample_index=index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,
                  overrides={"shape_family":shape_family,"sequence_axis":sequence_axis})
    family = ctx.draw_choice("shape_family", FAMILIES if shape_family is not None
                             else (_default_family(seed,index),))
    stress = stress or index == 103
    shape,axis,count,skip,gap,palette_period,parameters = _grammar(ctx,family,index,stress)
    target_index = count+skip
    objects = [shape(n) for n in range(target_index+1)]
    positions = []
    cursor = 0
    observed = {}
    for n,obj in enumerate(objects):
        low,high = min(p[axis] for p in obj),max(p[axis] for p in obj)
        origin = cursor-low
        positions.append(origin)
        if n < count:
            for point,color in obj.items():
                point = list(point)
                point[axis] += origin
                if tuple(point) in observed:
                    raise AssertionError("complete object footprints overlap")
                observed[tuple(point)] = color
        cursor += high-low+1+gap
    target = {}
    shell = {}
    for point,color in objects[-1].items():
        absolute = list(point)
        absolute[axis] += positions[-1]
        target[tuple(absolute)] = color
        if point not in objects[-2]:
            shell[tuple(absolute)] = color
    full_box = _box(target)
    if index == 0 or stress:
        crop_box = full_box
    elif index == 1 and family == "waves":
        crop_box = (full_box[0]+1,full_box[1],full_box[2],full_box[3])
    else:
        crop_box = ctx.draw_choice("crop_window",_crop_options(target,shell,full_box))
    top,left,bottom,right = crop_box
    extent = _box(list(observed)+[(top,left),(bottom,right)])
    height0,width0 = extent[2]-extent[0]+1,extent[3]-extent[1]+1
    if height0 > 30 or width0 > 30:
        raise ValueError("unchanged geometric profile does not fit a 30x30 input")
    height = 30 if stress else ctx.draw_int("canvas_rows",height0,min(30,height0+4))
    width = 30 if stress else ctx.draw_int("canvas_columns",width0,min(30,width0+4))
    row_shift = ctx.draw_int("row_offset",0,height-height0)-extent[0]
    col_shift = ctx.draw_int("column_offset",0,width-width0)-extent[1]
    grid = [[0]*width for _ in range(height)]
    for (r,c),color in observed.items():
        grid[r+row_shift][c+col_shift] = color
    crop_box = (top+row_shift,left+col_shift,bottom+row_shift,right+col_shift)
    top,left,bottom,right = crop_box
    for r,c in ((top,left),(top,left+1),(top+1,left),
                (bottom,right),(bottom,right-1),(bottom-1,right)):
        if grid[r][c]:
            raise AssertionError("crop marker intersects an observed object")
        grid[r][c] = 5
    def crop(cells):
        return [[cells.get((r-row_shift,c-col_shift),0) for c in range(left,right+1)]
                for r in range(top,bottom+1)]
    whole,new_shell = crop(target),crop(shell)
    target_axis = ctx.draw_choice("sequence_axis",("rows","columns"))
    choices = tuple(turns for turns in range(4) if (axis+turns)%2 == (0 if target_axis == "rows" else 1))
    turns = ctx.draw_choice("turns",choices)
    mirror = ctx.draw_choice("mirror_columns",(False,True))
    grid = _transform(grid,turns,mirror)
    whole = _transform(whole,turns,mirror)
    new_shell = _transform(new_shell,turns,mirror)
    crop_box = _transform_box(crop_box,height,width,turns,mirror)
    validate_grid(grid)
    if whole == new_shell or not any(any(row) for row in new_shell):
        raise AssertionError("the crop must retain both inherited and new support")
    return {"input":grid,"whole":whole,"new_shell":new_shell,"metadata":{
        "shape_family":family,"sequence_axis":target_axis,"observed_count":count,
        "target_index":target_index,"skipped_steps":skip,"gap":gap,
        "palette_period":palette_period,"shell_colors":sorted({c for row in new_shell for c in row if c}),
        "crop":list(crop_box),"geometry":parameters,"stress":stress,
        "turns":turns,"mirror":mirror}}


def scene(seed,index,stress=False):
    return scene_record(seed,index,stress)["input"]


def generate(seed,sample_index,*,difficulty=None,**overrides):
    unknown = set(overrides)-set(AXES)
    if unknown:
        raise ValueError(f"unknown generator overrides: {sorted(unknown)}")
    return scene_record(seed,sample_index,difficulty=difficulty,**overrides)["input"]


def _runs(values):
    result = []
    for value in sorted(set(values)):
        if result and value == result[-1][-1]+1:
            result[-1].append(value)
        else:
            result.append([value])
    return [(part[0],part[-1]) for part in result]


def _sequence(grid):
    points = [(r,c) for r,row in enumerate(grid) for c,color in enumerate(row) if color not in (0,5)]
    candidates = []
    for axis in (0,1):
        intervals = _runs(p[axis] for p in points)
        masses = [sum(low <= p[axis] <= high for p in points) for low,high in intervals]
        if len(intervals) >= 3 and (all(a < b for a,b in zip(masses,masses[1:])) or
                                   all(a > b for a,b in zip(masses,masses[1:]))):
            candidates.append((axis,intervals,masses))
    if len(candidates) != 1:
        raise ValueError("one mass-monotone spatial sequence is required")
    return candidates[0]


def observe_overrides(grid):
    validate_grid(grid)
    axis,intervals,masses = _sequence(grid)
    direction = 1 if masses[0] < masses[-1] else -1
    low,high = intervals[0] if direction == 1 else intervals[-1]
    first = [(r,c) for r,row in enumerate(grid) for c,color in enumerate(row)
             if color not in (0,5) and low <= (r,c)[axis] <= high]
    span = max(p[1-axis] for p in first)-min(p[1-axis] for p in first)+1
    slices = [sum(p[axis] == v for p in first)
              for v in (range(low,high+1) if direction == 1 else range(high,low-1,-1))]
    length = high-low+1
    far_slice = {p[1-axis] for p in first if p[axis] == (high if direction == 1 else low)}
    extrema = {min(p[1-axis] for p in first),max(p[1-axis] for p in first)}
    if span == 3 and len(first) == length+2:
        family = "lobes"
    elif length == 2 and span in (5,7) and len(first) == span+2 and far_slice == extrema:
        family = "arches"
    elif slices[0] == 2 and span == 2*length and len(first) == 4*length-2:
        family = "waves"
    elif slices[0] == span and all(value == 2 for value in slices[1:]):
        family = "stems"
    else:
        family = "ladders"
    return {"shape_family":family,"sequence_axis":"rows" if axis == 0 else "columns"}


def self_check(grid,*,difficulty=None,meta=None):
    try:
        validate_grid(grid)
        axis,intervals,masses = _sequence(grid)
        gray = {(r,c) for r,row in enumerate(grid) for c,color in enumerate(row) if color == 5}
        top,left,bottom,right = _box(gray)
        diagonals = ({(top,left),(top,left+1),(top+1,left),(bottom,right),(bottom,right-1),(bottom-1,right)},
                     {(top,right),(top,right-1),(top+1,right),(bottom,left),(bottom,left+1),(bottom-1,left)})
        if gray not in diagonals:
            return ["gray cells must form one pair of opposite L corners"]
        gaps = {b[0]-a[1]-1 for a,b in zip(intervals,intervals[1:])}
        if len(gaps) != 1 or min(gaps) < 1:
            return ["sequence objects need a constant positive gap"]
        crop_low,crop_high = (top,bottom) if axis == 0 else (left,right)
        if ((masses[0] < masses[-1] and crop_low <= intervals[-1][1]) or
                (masses[0] > masses[-1] and crop_high >= intervals[0][0])):
            return ["the crop must refer to a later member of the sequence"]
    except (ValueError,TypeError) as error:
        return [str(error)]
    return []
