import hashlib
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator, canonical_pairs
from arcpuzzles import Catalog

root = find_root(Path(__file__).resolve().parents[3] / 'repo')
g, source, digest = load_selected_generator('ce7050977ab7', root=root)
out = Path(__file__).resolve().parent
cases = [
    ('width', 'easy', dict(grid_h=12, grid_w=12, frame_h=4, frame_w=6, n_fillers=2)),
    ('count', 'medium', dict(grid_h=14, grid_w=14, frame_h=4, frame_w=5, n_fillers=3)),
]
results = []
for name, difficulty, overrides in cases:
    grid = g.generate(0, 0, difficulty=difficulty, **overrides)
    path = out / ('input.json' if name == 'width' else 'count-input.json')
    path.write_text(json.dumps(grid) + '\n')
    colors = sorted({v for row in grid for v in row} - {0})
    counts = {str(color): sum(row.count(color) for row in grid) for color in colors}
    results.append(dict(case=name, seed=0, sample_index=0, difficulty=difficulty,
                        overrides=overrides, observed_height=len(grid), observed_width=len(grid[0]),
                        observed_nonzero_colors=colors, color_counts=counts,
                        self_check=g.self_check(grid), input_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))

weak = dict(empty_scene=g.self_check([[0] * 3 for _ in range(3)]),
            boolean_cell=g.self_check([[True, 0], [0, 0]]),
            floating_cell=g.self_check([[1.5, 0], [0, 0]]))
base = g.generate(0, 0)
weak['unknown_key_ignored'] = base == g.generate(0, 0, misspelled_control=987)
weak['boolean_n_fillers_accepted'] = not g.self_check(g.generate(0, 0, n_fillers=True))
canon = canonical_pairs('ce7050977ab7', root=root, labeled_only=True)
canonical = [dict(input_dimensions=[len(p['input']),len(p['input'][0])],
                  output_dimensions=[len(p['output']),len(p['output'][0])],
                  self_check=g.self_check(p['input'])) for p in canon]
record = Catalog(root=root).get('ce7050977ab7')
report = dict(generator_sha256=digest, source=str(source), cases=results,
              validator_and_controls=weak, canonical_profiles=canonical,
              catalog_record=record)
(out / 'probe-results.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k,v in report.items() if k != 'catalog_record'}, indent=2))
