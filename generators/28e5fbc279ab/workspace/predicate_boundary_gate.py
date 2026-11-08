#!/usr/bin/env python3
"""Check coverage at b-1, b, b+1 for declared integer predicate boundaries.

This checks coverage, not label correctness or model learning. It consumes an
existing histogram, so rerunning the gate needs neither Racket nor a model.
Threshold semantics and the histogram's provenance remain the caller's contract.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


def check_boundaries(counts: Mapping[int | str, int], thresholds: Sequence[int]) -> dict[str, Any]:
    """Fail closed for missing integer neighbors; reject malformed declarations."""
    if not isinstance(counts, Mapping):
        raise TypeError('counts must be a mapping of integer values to counts')
    if not thresholds or any(type(b) is not int for b in thresholds):
        raise ValueError('thresholds must be a nonempty sequence of integers')
    normalized: dict[int, int] = {}
    for key, count in counts.items():
        if type(key) is int:
            value = key
        elif isinstance(key, str):
            value = int(key)
            if str(value) != key:
                raise ValueError('histogram string keys must be canonical integers')
        else:
            raise TypeError('histogram keys must be integers or integer strings')
        if type(count) is not int or count < 0:
            raise ValueError('histogram counts must be nonnegative integers')
        if value in normalized:
            raise ValueError('duplicate normalized histogram key')
        normalized[value] = count
    required = sorted({b + delta for b in thresholds for delta in (-1, 0, 1)})
    missing = [value for value in required if normalized.get(value, 0) == 0]
    return {
        'schema': 'integer-predicate-boundary-coverage-v1',
        'status': 'FAIL' if missing else 'PASS',
        'thresholds': sorted(set(thresholds)),
        'required_values': required,
        'missing_values': missing,
        'boundary_counts': {str(v): normalized.get(v, 0) for v in required},
        'observations': sum(normalized.values()),
        'semantics_verified': False,
        'interpretation': 'Coverage only; PASS does not establish label correctness or lesson identifiability.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--census', required=True, type=Path)
    parser.add_argument('--histogram-key', default='enclosed_area_counts')
    parser.add_argument('--thresholds', required=True, nargs='+', type=int)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.census.resolve() == args.out.resolve():
        parser.error('output must not overwrite the input census')
    try:
        raw = args.census.read_bytes()
        source = json.loads(raw)
        result = check_boundaries(source[args.histogram_key], args.thresholds)
        result['source'] = {
            'census': str(args.census),
            'census_sha256': hashlib.sha256(raw).hexdigest(),
            'histogram_key': args.histogram_key,
            **{key: source[key] for key in ('task_id', 'generator_sha256', 'rule_hash', 'sampling') if key in source},
        }
        result['command'] = {'cwd': str(Path.cwd()), 'argv': [sys.executable, *sys.argv]}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + '\n')
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
