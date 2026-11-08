"""Opt-in marginal feature-support warnings; never a label-correctness gate.

compare_support is reusable. The CLI's input-only extractor is task-specific.
A missing sampled value is not proof of impossibility; finite draws are retained.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys


def compare_support(canonical, generated):
    """Count type-sensitive scalar categories, preserving every row and band.

    Rows must be nonempty dicts with identical fields. JSON scalar values may
    mix types; e.g. True and 1 are separate values. Empty datasets are explicit.
    """
    if not isinstance(canonical, list) or not isinstance(generated, dict):
        raise ValueError('expected canonical list and generated band dict')
    if any(not isinstance(b, str) or not b for b in generated):
        raise ValueError('band names must be nonempty strings')
    groups = {'canonical': canonical, **{f'band:{b}': rows for b, rows in generated.items()}}
    fields = None
    counts = {}
    for name, rows in groups.items():
        if not isinstance(rows, list):
            raise ValueError(f'{name}: rows must be a list')
        counts[name] = {}
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or not row or any(type(k) is not str or not k for k in row):
                raise ValueError(f'{name} row {index}: expected nonempty feature dict')
            if fields is None:
                fields = set(row)
            if set(row) != fields:
                raise ValueError(f'{name} row {index}: inconsistent extractor fields')
            for field, value in row.items():
                if type(value) not in (type(None), bool, int, float, str):
                    raise ValueError(f'{name} row {index} {field}: expected JSON scalar')
                if type(value) is float and not math.isfinite(value):
                    raise ValueError(f'{name} row {index} {field}: nonfinite number')
                key = (type(value).__name__, json.dumps(value, ensure_ascii=False))
                counts[name].setdefault(field, Counter())[key] += 1
    def entries(counter, with_count=True):
        return [dict(type=kind, value=json.loads(value), **({'count': n} if with_count else {}))
                for (kind, value), n in sorted(counter.items())]
    result = {'canonical_rows': len(canonical),
              'generated_rows_by_band': {b: len(rows) for b, rows in generated.items()},
              'features': {}, 'warnings': []}
    for field in sorted(fields or ()):
        reference = counts['canonical'].get(field, Counter())
        feature = {'canonical': entries(reference), 'generated': {}, 'missing': {}}
        for band in generated:
            sampled = counts[f'band:{band}'].get(field, Counter())
            missing = Counter({key: n for key, n in reference.items() if key not in sampled})
            feature['generated'][band] = entries(sampled)
            feature['missing'][band] = entries(missing, False)
            if missing:
                result['warnings'].append({'band': band, 'feature': field,
                                           'missing_values': entries(missing, False)})
        result['features'][field] = feature
    return result


def extract_features(grid):
    """Measure fixed-color shape sizes and blank axes, using input pixels only."""
    if (not isinstance(grid, list) or not grid or any(not isinstance(row, list) or not row for row in grid)
            or len({len(row) for row in grid}) != 1
            or any(type(v) is not int or v not in (0, 1, 2, 3) for row in grid for v in row)):
        raise ValueError('expected nonempty rectangular grid of colors 0,1,2,3')
    cells = [{(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
             for color in (1, 2, 3)]
    if any(not shape for shape in cells):
        raise ValueError('each fixed color 1,2,3 must be present')
    boxes = [(min(r for r, c in s), max(r for r, c in s),
              min(c for r, c in s), max(c for r, c in s)) for s in cells]
    sizes = {(bottom-top+1, right-left+1) for top, bottom, left, right in boxes}
    top, bottom = min(b[0] for b in boxes), max(b[1] for b in boxes)
    left, right = min(b[2] for b in boxes), max(b[3] for b in boxes)
    blank_r = any(all(v == 0 for v in grid[r]) for r in range(top+1, bottom))
    blank_c = any(all(row[c] == 0 for row in grid) for c in range(left+1, right))
    return {'equal_normalized_bboxes': len(sizes) == 1,
            'blank_internal_row': blank_r, 'blank_internal_column': blank_c,
            'blank_internal_cross': blank_r and blank_c,
            'all_shapes_five_cells': all(len(s) == 5 for s in cells)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generator', type=Path, required=True)
    parser.add_argument('--per-band', type=int, default=100)
    parser.add_argument('--out', type=Path, required=True, help='new JSON output path')
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error('--per-band must be positive')
    if args.out.exists():
        parser.error('--out must be a new path')
    source = args.generator.resolve(strict=True)
    try:
        from reviewer_support import canonical_pairs, canonical_path, find_root
    except ModuleNotFoundError as error:
        if error.name != 'reviewer_support':
            raise
        for ancestor in Path(__file__).resolve().parents:
            runtime = ancestor / 'shared/runtime'
            if (runtime / 'reviewer_support.py').is_file():
                sys.path.insert(0, str(runtime))
                break
        else:
            raise RuntimeError('cannot locate reviewer_support in an ancestor shared/runtime') from error
        from reviewer_support import canonical_pairs, canonical_path, find_root
    root = find_root(__file__)
    pairs = canonical_pairs('2a1d414bfe10', root=root)
    canonical_rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()
                      if line.strip() and json.loads(line).get('task_id') == '2a1d414bfe10']
    spec = importlib.util.spec_from_file_location('support_probe_generator', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    seed = 160999
    sampled = {band: [extract_features(module.generate(seed, i, difficulty=band))
                      for i in range(args.per_band)] for band in ('easy', 'medium', 'hard')}
    report = compare_support([extract_features(pair['input']) for pair in pairs], sampled)
    sha = lambda data: hashlib.sha256(data).hexdigest()
    report.update(schema='canonical-feature-support-proposal-v1', task_id='2a1d414bfe10',
                  generator_source=str(source), generator_sha256=sha(source.read_bytes()),
                  generator_version=getattr(module, 'VERSION', None),
                  extractor_sha256=sha(Path(__file__).read_bytes()),
                  canonical_rows_sha256=sha(json.dumps(canonical_rows, sort_keys=True,
                                                       separators=(',', ':')).encode()),
                  canonical_pair_ids=[{k: pair[k] for k in ('variant', 'split', 'pair_index')} for pair in pairs],
                  replay={'seed': seed, 'sample_indices': list(range(args.per_band)),
                          'difficulty_bands': list(sampled), 'overrides': {}},
                  limits='Input-only marginal support; warnings are finite-sample observations, '
                         'not incorrect labels, joint coverage, or mathematical impossibility.')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps({'out': str(args.out), 'warnings': report['warnings']}, indent=2))


if __name__ == '__main__':
    main()
