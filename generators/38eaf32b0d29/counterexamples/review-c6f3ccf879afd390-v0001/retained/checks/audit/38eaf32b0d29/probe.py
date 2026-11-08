"""Reproduce an advertised inner-position control defect; no source edits."""
from pathlib import Path
from collections import Counter
import argparse, hashlib, json
from reviewer_support import load_selected_generator

parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
root = Path.cwd().resolve()
out = args.out.resolve()
task = '38eaf32b0d29'
module, source, source_hash = load_selected_generator(task, root=root)
expected_source = 'f3852992522feb56d3b0591fbdc3473035760baeca47a1c8c67ba52bca07110e'
assert source_hash == expected_source, (source_hash, expected_source)
settings = {'difficulty': 'medium', 'grid_size': 15, 'n_outer_marks': 8}
br = module.generate(123, 0, **settings, inner_position='br')
tr = module.generate(123, 0, **settings, inner_position='tr')
counts = Counter(v for row in br for v in row)
background = max(counts, key=counts.get)
nonbackground = [v for v in counts if v != background]
assert len(nonbackground) == 2
inner = min(nonbackground, key=counts.get)
outer = max(nonbackground, key=counts.get)
positions = [[i, j] for i, row in enumerate(br) for j, v in enumerate(row) if v == inner]
expected = [[len(br)-2, len(br[0])-2]]
validator = module.self_check(br, difficulty='medium')
def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()
result = {
    'schema': 'arcpuzzles-audit-control-probe-v1', 'task_id': task,
    'finding_id': 'A1', 'finding_kind': 'advertised_input_axis_realization',
    'source_path': source.relative_to(root).as_posix(), 'generator_sha256': source_hash,
    'rule_hash_expected': '267d0c1f4d6a',
    'seed': 123, 'sample_index': 0, 'common_overrides': settings,
    'requested_inner_position': 'br', 'comparison_inner_position': 'tr',
    'axis_declaration': module.AXES['inner_position'],
    'grid_shape': [len(br), len(br[0])], 'color_counts': dict(counts),
    'background_color': background, 'outer_color': outer, 'inner_color': inner,
    'expected_inner_positions': expected, 'actual_inner_positions': positions,
    'br_tr_inputs_equal': br == tr,
    'br_input_sha256': grid_hash(br), 'tr_input_sha256': grid_hash(tr),
    'self_check_errors': validator,
    'defect_reproduced': br == tr and positions != expected and validator == [],
    'rival_output': None,
    'scope': 'Two same-seed generated inputs; documented numeric and enum override domain. This checks an input control, not an output-rule rival or all seeds.',
    'prior_leads': ['review-0062d8f12011f0be:v0001', 'review-4fb2a93096b60c50:v0001'],
    'prior_lead_path': 'repo/generators/38eaf32b0d29/evidence/review_index.json',
    'source_modified': False,
}
assert result['defect_reproduced'], result
assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
(out/'input.json').write_text(json.dumps(br, indent=2)+'\n')
(out/'probe.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps({'status': 'defect_reproduced', 'task_id': task, 'source_sha256': source_hash,
 'actual_inner_positions': positions, 'expected_inner_positions': expected,
 'br_tr_inputs_equal': br == tr, 'self_check_errors': validator}, sort_keys=True))
