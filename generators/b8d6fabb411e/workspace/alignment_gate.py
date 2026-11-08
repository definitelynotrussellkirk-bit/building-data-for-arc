#!/usr/bin/env python3
"""Task-local conditional-witness gate, using the actual canonical Racket rule.

From the extracted packet root:
  python3 run_with_racket.py python3 generators/b8d6fabb411e/workspace/alignment_gate.py \
      --per-band 320 --out ../checks/alignment-after.json --html ../checks/alignment-after.html

The default 32 draws/band are cheap; four draws/band are the smallest lesson
probe.  --runtime accepts an already frozen prepare_runtime execution tree,
which makes the exact same gate usable against a before/after source pair.
All exported counterexamples are review-only, never training examples.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from html import escape
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

TASK_ID = 'b8d6fabb411e'
BANDS = ('easy', 'medium', 'hard')
AXES = ('horizontal', 'vertical')
RIVALS = {axis + '_boundary_only': axis for axis in AXES}
Grid = list[list[int]]


def grid_hash(grid: Grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()


def dihedral_images(grid: Grid) -> list[tuple[str, Grid]]:
    """The eight square symmetries also work on rectangular grids."""
    images: list[tuple[str, Grid]] = []
    for reflected in (False, True):
        current = [row[::-1] if reflected else row[:] for row in grid]
        for turns in range(4):
            name = ('mirror_' if reflected else '') + ('identity' if turns == 0 else f'rot{90 * turns}')
            images.append((name, [row[:] for row in current]))
            current = [list(row) for row in zip(*current[::-1])]
    return images


def span_markers(grid: Grid) -> list[dict[str, Any]]:
    """Independent role extraction; does not call the generator's analyzer."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('expected a nonempty rectangular grid')
    square = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    if not square:
        raise ValueError('no color-3 anchor')
    top, bottom = min(r for r, _ in square), max(r for r, _ in square)
    left, right = min(c for _, c in square), max(c for _, c in square)
    result = []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color in (0, 3):
                continue
            if top <= r <= bottom and c < left:
                direction, axis, offset, side = 'left', 'horizontal', r - top, bottom - top + 1
                cells = [(r, cc) for cc in range(c + 1, left)]
            elif top <= r <= bottom and c > right:
                direction, axis, offset, side = 'right', 'horizontal', r - top, bottom - top + 1
                cells = [(r, cc) for cc in range(right + 1, c)]
            elif left <= c <= right and r < top:
                direction, axis, offset, side = 'top', 'vertical', c - left, right - left + 1
                cells = [(rr, c) for rr in range(r + 1, top)]
            elif left <= c <= right and r > bottom:
                direction, axis, offset, side = 'bottom', 'vertical', c - left, right - left + 1
                cells = [(rr, c) for rr in range(bottom + 1, r)]
            else:
                continue
            result.append({'row': r, 'col': c, 'color': color, 'direction': direction,
                           'axis': axis, 'offset': offset, 'side': side,
                           'interior': 0 < offset < side - 1, 'cells': cells})
    return result


def axis_boundary_rival(grid: Grid, axis: str) -> Grid:
    """Independent executable wrong rule: clip ONLY the chosen axis's span."""
    if axis not in AXES:
        raise ValueError(f'unknown axis: {axis}')
    result = [row[:] for row in grid]
    for marker in span_markers(grid):
        if marker['axis'] == axis and marker['interior']:
            continue
        for r, c in marker['cells']:
            result[r][c] = marker['color']
    return result


def inspect_case(grid: Grid, output: Grid) -> dict[str, Any]:
    if len(output) != len(grid) or any(len(row) != len(grid[0]) for row in output):
        raise ValueError('reference output has the wrong shape')
    roles = span_markers(grid)
    changed = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if output[r][c] != value]
    return {
        'input_sha256': grid_hash(grid), 'output_sha256': grid_hash(output),
        'interior_axes': sorted({role['axis'] for role in roles if role['interior']}),
        'rival_agrees': {name: axis_boundary_rival(grid, axis) == output for name, axis in RIVALS.items()},
        'changed_cells': len(changed),
        'changed_colored_cells': sum(grid[r][c] != 0 for r, c in changed),
        'interior_direction_offsets': sorted({f"{m['direction']}:side{m['side']}:offset{m['offset']}"
                                             for m in roles if m['interior']}),
    }


def support_failures(cases: list[dict[str, Any]], bands=BANDS) -> list[str]:
    """Require conditional witnesses per band and per sliding four-demo window."""
    failures = []
    for band in bands:
        rows = sorted((row for row in cases if row['difficulty'] == band), key=lambda row: row['sample_index'])
        if len(rows) < 4:
            failures.append(f'{band}: fewer than four valid examples')
            continue
        for axis in AXES:
            if not any(axis in row['interior_axes'] for row in rows):
                failures.append(f'{band}: no {axis} interior-span witness')
        for name in RIVALS:
            if all(row['rival_agrees'][name] for row in rows):
                failures.append(f'{band}: {name} survives every generated example')
        for index in range(len(rows) - 3):
            window = rows[index:index + 4]
            surviving = [name for name in RIVALS if all(row['rival_agrees'][name] for row in window)]
            if surviving:
                failures.append(f"{band}: window starting {window[0]['sample_index']} leaves {','.join(surviving)} alive")
    return failures


def render_html(report: dict[str, Any]) -> str:
    """A self-contained, escaped review gallery; no CDN or external requests."""
    colors = ('#000000', '#0074d9', '#ff4136', '#2ecc40', '#ffdc00',
              '#aaaaaa', '#f012be', '#ff851b', '#7fdbff', '#870c25')
    def grid_table(grid: Grid) -> str:
        return '<table class="grid">' + ''.join('<tr>' + ''.join(
            f'<td style="background:{colors[value]}"><span>{value}</span></td>'
            for value in row) + '</tr>' for row in grid) + '</table>'
    cards = []
    for row in report.get('witnesses', []):
        title = escape(f"{row['difficulty']} / {row['scope']} / {row['rival']} / seed {row['seed']} index {row['sample_index']}")
        panels = ''.join(f'<div><h3>{label}</h3>{grid_table(row[key])}</div>' for label, key in
                         [('Input', 'input'), ('Racket reference', 'racket_output'), ('Wrong rival', 'rival_output')])
        cards.append(f'<section><h2>{title}</h2><div class="panels">{panels}</div></section>')
    failures = ''.join(f'<li>{escape(str(item))}</li>' for item in report.get('failures', []))
    summary = escape(json.dumps(report.get('bands', {}), indent=2))
    return ('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Alignment coverage review</title><style>
body{font:16px system-ui,sans-serif;max-width:1200px;margin:32px auto;padding:0 24px;color:#17212b;background:#f5f7f9}
section{background:white;padding:18px;margin:20px 0;border:1px solid #ccd2d8;border-radius:10px}h2{font-size:18px}
.panels{display:flex;gap:24px;flex-wrap:wrap}.grid{border-collapse:collapse}.grid td{width:20px;height:20px;border:1px solid #555;text-align:center}
.grid span{font-size:9px;color:white;text-shadow:0 0 2px black}pre{white-space:pre-wrap}li{margin:4px 0}
</style>''' + f'<h1>{escape(str(report.get("task_id", TASK_ID)))} — {escape(str(report.get("status", "UNKNOWN")))}</h1>'
            + '<p>Review-only counterexamples. Do not use this gallery as model-visible training or evaluation challenges.</p>'
            + f'<ul>{failures}</ul><pre>{summary}</pre>' + ''.join(cards) + '</html>')


def run_gate(runtime: Path, *, per_band: int, orbit_samples: int) -> dict[str, Any]:
    # Legacy modules resolve their source and data inside the copied runtime.
    # main() invokes this once per process; never mix before/after imports.
    sys.path.insert(0, str(runtime))
    previous_cwd = Path.cwd()
    os.chdir(runtime)
    oracle = None
    try:
        gen = importlib.import_module(f'puzzle_generators.per_puzzle.{TASK_ID}.generator')
        from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash
        from scripts.generator_semantic_gate import _RuleOracle
        oracle = _RuleOracle(TASK_ID)
        if not oracle.ready:
            raise RuntimeError(oracle.error or 'canonical Racket oracle unavailable')
        report: dict[str, Any] = {
            'schema': 'arcpuzzles-conditional-alignment-gate-v1', 'task_id': TASK_ID,
            'data_use': 'review-only-never-train', 'generator_version': gen.VERSION,
            'generator_sha256': hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
            'rule_hash': canonical_rule_hash(TASK_ID),
            'config': {'per_band': per_band, 'seed': '100000 + sample_index',
                       'bands': list(BANDS), 'orbit_samples_per_band': orbit_samples},
            'reference_calls': 0, 'canonical_pairs_checked': 0, 'cases': [],
            'bands': {}, 'witnesses': [], 'failures': [], 'orbit_cases_checked': 0,
        }
        def reference(grid):
            output, error = oracle.apply(grid)
            report['reference_calls'] += 1
            if error is not None:
                raise RuntimeError(error)
            return output
        pairs = canonical_pairs(TASK_ID)
        if not pairs:
            report['failures'].append('canonical pairs are missing')
        for index, pair in enumerate(pairs):
            output = reference(pair['input'])
            if output != pair['output'] or gen.self_check(pair['input']):
                report['failures'].append(f'canonical pair {index}: reference or input validation mismatch')
            report['canonical_pairs_checked'] += 1
        seen_witnesses = set()
        def retain_witness(grid, output, *, band, scope, seed, index):
            for name, axis in RIVALS.items():
                key = band, scope, name
                rival_output = axis_boundary_rival(grid, axis)
                if rival_output != output and key not in seen_witnesses:
                    seen_witnesses.add(key)
                    report['witnesses'].append({'difficulty': band, 'scope': scope,
                        'seed': seed, 'sample_index': index, 'rival': name,
                        'input': grid, 'racket_output': output, 'rival_output': rival_output})
        for band in BANDS:
            offsets: Counter[str] = Counter()
            for index in range(per_band):
                seed = 100_000 + index
                try:
                    grid = gen.generate(seed, index, difficulty=band)
                    output = reference(grid)
                    reasons = gen.self_check(grid, difficulty=band)
                    if reasons:
                        raise ValueError('; '.join(reasons))
                    row = {'difficulty': band, 'seed': seed, 'sample_index': index,
                           **inspect_case(grid, output)}
                    report['cases'].append(row)
                    offsets.update(row['interior_direction_offsets'])
                    if row['changed_colored_cells'] or not row['changed_cells']:
                        report['failures'].append(f'{band}/{index}: marker preservation or visible-change contract failed')
                    if gen._expected_output(grid) != output:
                        report['failures'].append(f'{band}/{index}: Python mirror differs from Racket')
                    retain_witness(grid, output, band=band, scope='generated', seed=seed, index=index)
                    if index < orbit_samples:
                        for (name, transformed), (_, expected) in zip(dihedral_images(grid), dihedral_images(output)):
                            actual = reference(transformed)
                            report['orbit_cases_checked'] += 1
                            if gen.self_check(transformed) or actual != expected:
                                report['failures'].append(f'{band}/{index}/{name}: symmetry or validation disagreement')
                            retain_witness(transformed, actual, band=band, scope='counterfactual', seed=seed, index=index)
                except Exception as exc:
                    report['failures'].append(f'{band}/{index}: {type(exc).__name__}: {exc}')
            rows = [row for row in report['cases'] if row['difficulty'] == band]
            report['bands'][band] = {
                'attempted': per_band, 'validated': len(rows),
                'horizontal_interior': sum('horizontal' in row['interior_axes'] for row in rows),
                'vertical_interior': sum('vertical' in row['interior_axes'] for row in rows),
                'rival_agreement': {name: sum(row['rival_agrees'][name] for row in rows) for name in RIVALS},
                'interior_direction_offsets': dict(sorted(offsets.items())),
            }
        report['failures'].extend(support_failures(report['cases']))
        report['status'] = 'FAIL' if report['failures'] else 'PASS'
        return report
    finally:
        if oracle is not None:
            oracle.close()
        os.chdir(previous_cwd)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--runtime', type=Path, help='Existing frozen prepare_runtime tree; otherwise copy current local source')
    parser.add_argument('--per-band', type=int, default=32, help='Positive multiple of four, at least four')
    parser.add_argument('--orbit-samples', type=int, default=4, help='Number of first cases per band checked in all eight symmetries')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--html', type=Path)
    args = parser.parse_args(argv)
    if args.per_band < 4 or args.per_band % 4:
        parser.error('--per-band must be a multiple of four and at least four')
    if not 1 <= args.orbit_samples <= args.per_band:
        parser.error('--orbit-samples must be between one and --per-band')
    paths = [path.resolve() for path in (args.out, args.html) if path is not None]
    if len(paths) != len(set(paths)) or any(path.exists() for path in paths):
        parser.error('output paths must be distinct and new')
    temporary = None
    try:
        if args.runtime:
            runtime = args.runtime.resolve()
            if not (runtime / 'RUNTIME_MANIFEST.json').is_file():
                raise ValueError('--runtime must be a prepared execution tree')
        else:
            library = next((parent for parent in Path(__file__).resolve().parents
                            if (parent / 'src/arcpuzzles/runtime.py').is_file()), None)
            if library is None:
                raise ValueError('No local library found: pass --runtime for a standalone probe')
            sys.path.insert(0, str(library / 'src'))
            from arcpuzzles.catalog import Catalog
            from arcpuzzles.runtime import prepare_runtime
            temporary = tempfile.TemporaryDirectory(prefix='arcpuzzles-alignment-review-')
            runtime = Path(temporary.name)
            prepare_runtime(Catalog(library), runtime, TASK_ID)
        report = run_gate(runtime, per_band=args.per_band, orbit_samples=args.orbit_samples)
        code = 0 if report['status'] == 'PASS' else 1
    except Exception as exc:
        report = {'schema': 'arcpuzzles-conditional-alignment-gate-v1', 'task_id': TASK_ID,
                  'status': 'ERROR', 'failures': [f'{type(exc).__name__}: {exc}']}
        code = 2
    finally:
        if temporary is not None:
            temporary.cleanup()
    paths[0].parent.mkdir(parents=True, exist_ok=True)
    paths[0].write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if args.html:
        paths[1].parent.mkdir(parents=True, exist_ok=True)
        paths[1].write_text(render_html(report), encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('status', 'bands', 'reference_calls') if key in report}, indent=2))
    print(f'Report: {paths[0]}')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
