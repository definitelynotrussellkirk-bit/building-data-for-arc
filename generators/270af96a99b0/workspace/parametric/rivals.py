"""Finite wrong-rule bank for visible-demo/query learnability checks."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent


def _oracle():
    path = _HERE / "oracle.py"
    name = "_rivals_270af96a99b0_oracle_" + hashlib.sha256(str(path).encode()).hexdigest()
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load adjacent oracle")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _ordered(grid, key):
    return sorted(_oracle().components(grid), key=key)


def source_position(grid):
    return _oracle().solve(grid, "source_position")


def smaller_area(grid):
    return _oracle().solve(grid, "smaller_area")


def larger_area_tie(grid):
    return _oracle().pack(_ordered(grid, lambda x: (x.perimeter, -x.area, x.r1, x.c1)))


def global_area(grid):
    return _oracle().pack(_ordered(grid, lambda x: (x.area, x.r1, x.c1)))


def bbox_perimeter(grid):
    return _oracle().pack(_ordered(grid, lambda x: (x.bbox_perimeter, x.r1, x.c1)))


def source_order(grid):
    return _oracle().pack(_oracle().components(grid))


def color_order(grid):
    return _oracle().pack(_ordered(grid, lambda x: (x.color, x.r1, x.c1)))


def descending_perimeter(grid):
    return _oracle().pack(_ordered(grid, lambda x: (-x.perimeter, x.r1, x.c1)))


def bottom_aligned(grid):
    return _oracle().pack(_ordered(grid, lambda x: (x.perimeter, x.r1, x.c1)), alignment="bottom")


def no_gap(grid):
    return _oracle().pack(_ordered(grid, lambda x: (x.perimeter, x.r1, x.c1)), gap=0)


def fill_bbox(grid):
    return _oracle().pack(_ordered(grid, lambda x: (x.perimeter, x.r1, x.c1)), fill_bbox=True)


RIVALS = {
    "source_position": source_position,
    "smaller_area": smaller_area,
    "larger_area_tie": larger_area_tie,
    "global_area": global_area,
    "bbox_perimeter": bbox_perimeter,
    "source_order": source_order,
    "color_order": color_order,
    "descending_perimeter": descending_perimeter,
    "bottom_aligned": bottom_aligned,
    "no_gap": no_gap,
    "fill_bbox": fill_bbox,
}
