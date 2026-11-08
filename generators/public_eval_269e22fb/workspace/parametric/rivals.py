"""Executable Racket and Python rival rules for the 269e22fb family audit."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_crop_rival_sampler", HERE / "sampler.py")
BASE = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(BASE)


def _replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"expected one replacement target, found {source.count(old)}")
    return source.replace(old, new, 1)


def racket_programs() -> dict[str, str]:
    canonical = (HERE / "canonical.rkt").read_text()
    marked = (HERE / "mark_enclosed.rkt").read_text()
    poses_block = """   (define poses
    (list base (rotate-cw base) (rotate-180 base) (rotate-ccw base)
          (flip-lr base) (flip-ud base) (transpose base)
          (rotate-180 (transpose base))))"""
    rotations_block = """   (define poses
    (list base (rotate-cw base) (rotate-180 base) (rotate-ccw base)))"""
    fits_block = """   (define (fits? full)
    (for*/or ((r (in-range (+ 1 (- 20 h))))
              (c (in-range (+ 1 (- 20 w)))))
     (equal? crop (subgrid full r c (+ r h -1) (+ c w -1)))))"""
    top_left_block = """   (define (fits? full)
    (equal? crop (subgrid full 0 0 (- h 1) (- w 1))))"""
    matched = "   (define matched (or (for/first ((full poses) #:when (fits? full)) full) base))"
    return {
        "preserve": canonical,
        "mark_enclosed": marked,
        "fixed_base": _replace_once(canonical, matched, "   (define matched base)"),
        "top_left": _replace_once(canonical, fits_block, top_left_block),
        "rotations_only": _replace_once(canonical, poses_block, rotations_block),
        "mark_all_background": _replace_once(marked, "(fill-all-enclosed completed 2 bg)", "(recolor completed bg 2)"),
        "wrong_base_mark": _replace_once(marked, matched, "   (define matched base)"),
    }


def _colors(grid):
    parsed, _h, _w, foreground, background = BASE._parse(grid)
    return parsed, foreground, background


def _render(pose: int, foreground: int, background: int):
    return [[foreground if value else background for value in row] for row in BASE._pose_bank()[pose]]


def _find_restricted(binary, poses, top_left_only=False):
    h, w = len(binary), len(binary[0])
    found = []
    for pose in poses:
        full = BASE._pose_bank()[pose]
        rows = (0,) if top_left_only else range(21 - h)
        cols = (0,) if top_left_only else range(21 - w)
        for r in rows:
            for c in cols:
                crop = [list(line[c:c+w]) for line in full[r:r+h]]
                if crop == binary:
                    found.append((pose, r, c))
    return found


def _background_components(grid, background):
    h, w = len(grid), len(grid[0]); unseen={(r,c) for r in range(h) for c in range(w) if grid[r][c]==background}; out=[]
    while unseen:
        start=min(unseen); unseen.remove(start); todo=[start]; cells=[]; boundary=False
        while todo:
            r,c=todo.pop(); cells.append((r,c)); boundary |= r in (0,h-1) or c in (0,w-1)
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in unseen: unseen.remove(q); todo.append(q)
        out.append((boundary,cells))
    return out


def predict(grid, name: str):
    parsed, foreground, background = _colors(grid)
    binary = BASE._binary(parsed, foreground)
    if name == "preserve":
        return BASE.solve(parsed, "preserve")
    if name == "mark_enclosed":
        return BASE.solve(parsed, "mark_enclosed")
    if name == "fixed_base":
        return _render(0, foreground, background)
    if name == "top_left":
        found = _find_restricted(binary, range(8), True)
        pose = found[0][0] if found else 0
        return _render(pose, foreground, background)
    if name == "rotations_only":
        found = _find_restricted(binary, range(4), False)
        pose = found[0][0] if found else 0
        return _render(pose, foreground, background)
    completion = BASE.solve(parsed, "preserve")
    if name == "mark_all_background":
        return [[2 if value == background else value for value in row] for row in completion]
    if name == "mark_largest_pocket":
        enclosed = [cells for boundary, cells in _background_components(completion, background) if not boundary]
        chosen = max(enclosed, key=len)
        output = deepcopy(completion)
        for r,c in chosen: output[r][c]=2
        return output
    if name == "wrong_base_mark":
        base = _render(0, foreground, background)
        return BASE.fill_enclosed(base, background)[0]
    raise ValueError(f"unknown rival {name}")


def python_names():
    return (
        "preserve", "mark_enclosed", "fixed_base", "top_left",
        "rotations_only", "mark_all_background", "mark_largest_pocket",
        "wrong_base_mark",
    )
