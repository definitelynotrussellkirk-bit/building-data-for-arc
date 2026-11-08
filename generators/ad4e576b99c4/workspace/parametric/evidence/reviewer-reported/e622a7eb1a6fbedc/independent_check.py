"""Independent geometric boundary probe for the proposed shear-start family."""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
from pathlib import Path
import sys


def oracle(grid, onset):
    """Pointwise transport plus a separately derived border endpoint."""
    h, w = len(grid), len(grid[0])
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    bottom = max(r for r, _ in cells)
    width = max(c for _, c in cells) - left + 1
    split = next(r for r, row in enumerate(grid) if 6 in row)
    result = [[1] * w for _ in range(split)] + [[6] * w for _ in range(h - split)]
    final_displacement = max(0, bottom - top + 1 - onset)
    if left == 0:
        result[split][:w - final_displacement - 1] = [9] * (w - final_displacement - 1)
    else:
        result[split][final_displacement + 1:] = [9] * (w - final_displacement - 1)
    for r, c in cells:
        displacement = max(0, r - top + 1 - onset)
        destination = w - width - displacement if left == 0 else displacement
        result[r][destination + c - left] = 5
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prototype', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('independent_shear_target', args.prototype)
    target = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = target
    spec.loader.exec_module(target)
    from reviewer_support import find_root, canonical_pairs, load_selected_generator
    root = find_root(args.prototype)
    gen, source, digest = load_selected_generator('ad4e576b99c4', root=root)
    canonical = canonical_pairs('ad4e576b99c4', root=root, labeled_only=True)
    # Boundary fixtures are independently selected, not the prototype's sampler.
    grids = []
    settings = []
    for width, height, side in itertools.product((3, 7), (4, 10), ('left', 'right')):
        overrides = dict(grid_h=16, grid_w=16, bottom_rows=6,
                         patch_width=width, patch_height=height, side=side)
        grids.append(gen.generate(731, len(grids), **overrides))
        settings.append(overrides)
    # Use the same explicit Racket bridge protocol as the repository runner,
    # but no prototype Python renderer, sampler, or certificate for expectations.
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    prelude = root / 'shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt'
    comparisons = []
    with RacketBridge(prelude_path=str(prelude), timeout=4.0) as bridge:
        for onset in (2, 3, 4):
            program = target.program_for(onset)
            bridge.eval_text('(define independent-rule ' + wrap_rule(program) + ')')
            for index, grid in enumerate(grids):
                bridge.define_grid('independent-input', grid)
                actual = bridge.eval_text('(independent-rule independent-input)')
                expected = oracle(grid, onset)
                assert actual == expected, (onset, settings[index])
                comparisons.append(dict(onset=onset, geometry=settings[index], equal=True))
    for pair in canonical:
        assert oracle(pair['input'], 3) == pair['output']
    report = dict(status='pass', source_sha256=digest, boundary_comparisons=comparisons,
                  canonical_pairs=len(canonical),
                  scope='Independent point-transport oracle; 8 boundary inputs x 3 settings; canonical equality.')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(status='pass', boundary_comparisons=len(comparisons), canonical_pairs=len(canonical))))


if __name__ == '__main__':
    main()
