#!/usr/bin/env python3
"""Opt-in containment geometry for bbox dimensions; no puzzle authority imports."""
import argparse
import json
from pathlib import Path

SCHEMA = "rotation-fit-v1"


def _pair(value, name, *, positive=True):
    if (not isinstance(value, list) or len(value) != 2
            or any(type(v) is not int or (positive and v <= 0) for v in value)):
        kind = "positive integers" if positive else "integers"
        raise ValueError(f"{name} must be a two-element list of {kind}")
    return list(value)


def _overflow(shape, origin, bounds):
    h, w = shape
    r, c = origin
    bh, bw = bounds
    return dict(top=max(0, -r), bottom=max(0, r + h - bh),
                left=max(0, -c), right=max(0, c + w - bw))


def check_case(case):
    """Return containment flags/extents; reject malformed inputs with ValueError."""
    required = {"source_shape", "interior_shape", "turns_cw"}
    optional = {"target_origin", "canvas_shape"}
    if not isinstance(case, dict):
        raise ValueError("each case must be an object")
    if required - case.keys() or case.keys() - required - optional:
        raise ValueError("expected source_shape, interior_shape, turns_cw; only target_origin and canvas_shape are optional")
    source = _pair(case["source_shape"], "source_shape")
    target = _pair(case["interior_shape"], "interior_shape")
    turns = case["turns_cw"]
    if type(turns) is not int or not 0 <= turns <= 3:
        raise ValueError("turns_cw must be an integer in 0..3")
    if ("target_origin" in case) != ("canvas_shape" in case):
        raise ValueError("target_origin and canvas_shape must be supplied together")
    transformed = source[::-1] if turns % 2 else list(source)
    interior_overflow = _overflow(transformed, [0, 0], target)
    origin = canvas = canvas_overflow = fits_canvas = None
    if "target_origin" in case:
        origin = _pair(case["target_origin"], "target_origin", positive=False)
        canvas = _pair(case["canvas_shape"], "canvas_shape")
        canvas_overflow = _overflow(transformed, origin, canvas)
        fits_canvas = not any(canvas_overflow.values())
    fits_interior = not any(interior_overflow.values())
    return dict(source_shape=source, turns_cw=turns, transformed_shape=transformed,
                interior_shape=target, interior_overflow=interior_overflow,
                fits_interior=fits_interior, target_origin=origin, canvas_shape=canvas,
                canvas_overflow=canvas_overflow, fits_canvas=fits_canvas,
                fits_all_checked=fits_interior and fits_canvas is not False)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"nonfinite JSON constant is not allowed: {value}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON case object or nonempty list of cases")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"),
                          object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        cases = [data] if isinstance(data, dict) else data
        if not isinstance(cases, list) or not cases:
            raise ValueError("input must be a case object or nonempty list of cases")
        results = []
        for index, case in enumerate(cases):
            try:
                results.append(check_case(case))
            except ValueError as exc:
                raise ValueError(f"case {index}: {exc}") from exc
        fits = all(result["fits_all_checked"] for result in results)
        print(json.dumps(dict(schema=SCHEMA, results=results, fits_all_checked=fits), sort_keys=True))
        return 0 if fits else 1
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps(dict(schema=SCHEMA, error=str(exc)), sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
