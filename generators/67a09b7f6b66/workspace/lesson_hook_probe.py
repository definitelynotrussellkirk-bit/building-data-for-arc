"""Reproduce labeled-grid boundary defects without changing the rule."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from reference_probe import load_generator, retained_degenerate_inputs


def run():
    gen = load_generator()
    lesson = []
    for index in range(4):
        grid = gen.generate(7651, index)
        lesson.append({'input': grid, 'output': gen.rule_mirror(grid)})
    demos, query = lesson[:3], lesson[3]
    report = {
        'schema': 'arcpuzzles-task-local-probe-v1',
        'source_sha256': hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
        'rule_hash': gen.RULE_HASH,
        'normal_lesson_errors': gen.lesson_identifiable(demos, query),
        'old_degenerate_metadata_errors': [gen.self_check(grid, meta={'texture': name}) for name, grid in zip(('no_dots', 'no_legend', 'no_walls'), retained_degenerate_inputs())],
        'cases': {},
    }
    for name in ('float_output', 'bool_output', 'tuple_input', 'tuple_output'):
        trial = deepcopy(query)
        if name == 'float_output':
            trial['output'] = [[float(value) for value in row] for row in trial['output']]
        elif name == 'bool_output':
            trial['output'][0][0] = False
        elif name == 'tuple_input':
            trial['input'] = tuple(tuple(row) for row in trial['input'])
        else:
            trial['output'] = tuple(tuple(row) for row in trial['output'])
        row = {'input_errors': gen.self_check(trial['input'])}
        try:
            row['lesson_errors'] = gen.lesson_identifiable(demos, trial)
        except Exception as exc:
            row['raised'] = f'{type(exc).__name__}: {exc}'
        report['cases'][name] = row
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
