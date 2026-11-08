"""Bounded same-checkout parametric adapter evaluation in a disposable process."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib
import importlib.util
import itertools
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys

from .catalog import Catalog

sys.dont_write_bytecode = True


def _typed(value):
    """JSON equality with explicit scalar types, including bool versus int."""
    kind = type(value)
    if kind in {str, bool, int, type(None)}:
        return (kind.__name__, value)
    if kind is float and math.isfinite(value):
        return ('float', value)
    if kind is list:
        return ('list', tuple(_typed(v) for v in value))
    if kind is dict and all(type(k) is str for k in value):
        return ('dict', tuple((k, _typed(value[k])) for k in sorted(value)))
    raise ValueError('Parameter settings must contain finite typed JSON values')


def _settings(value, parameters):
    if not isinstance(value, dict) or set(value) != set(parameters):
        raise ValueError('Parameter settings must name exactly the declared keys')
    for key, options in parameters.items():
        if _typed(value[key]) not in {_typed(option) for option in options}:
            raise ValueError(f'Parameter settings value is undeclared: {key}')
    return copy.deepcopy(value)


def _grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30 or type(value[0]) is not list
            or not 1 <= len(value[0]) <= 30 or any(type(row) is not list or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row) for row in value)):
        raise ValueError('A grid must be rectangular 1..30 with exact integer cells 0..9')
    return copy.deepcopy(value)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in {low}..{high}; bool is forbidden')
    return value


@contextlib.contextmanager
def _local_imports(runtime, adapter_parent):
    before = list(sys.path)
    prefixes = ('arc_repl', 'puzzle_generators')
    saved = {k: v for k, v in sys.modules.items() if k.split('.')[0] in prefixes}
    for key in saved:
        del sys.modules[key]
    sys.path[:0] = [str(runtime), str(adapter_parent)]
    try:
        yield
    finally:
        sys.path[:] = before
        for key in list(sys.modules):
            if key.split('.')[0] in prefixes:
                del sys.modules[key]
        sys.modules.update(saved)


def _real_evaluator(runtime):
    bridge_module = importlib.import_module('arc_repl.racket_bridge')
    wrap_module = importlib.import_module('puzzle_generators.rule_wrap')
    for module in (bridge_module, wrap_module):
        if not Path(module.__file__).resolve().is_relative_to(runtime):
            raise ValueError('Reference runtime must come from the same checkout')
    bridge = bridge_module.RacketBridge()
    try:
        identity = bridge.runtime_identity
        if identity.get('backend') != 'racket' or identity.get('protected') is not True:
            raise ValueError('Qualification requires a live protected Racket backend')
        identity = {k: identity[k] for k in ('schema', 'backend', 'protected', 'binary_sha256',
            'prelude_sha256', 'bridge_sha256', 'boot_script_sha256',
            'candidate_symbol_policy_sha256') if k in identity}
    except Exception:
        bridge.close()
        raise
    wrapped = {}
    def apply(program, grid):
        if program not in wrapped:
            wrapped[program] = wrap_module.wrap_rule(program)
        literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
        return bridge.eval_text(f'({wrapped[program]} {literal})')
    return apply, identity, bridge


def evaluate_contract(root: Path, task_id: str, contract: dict, jobs: list[dict], apply_program=None) -> dict:
    """Verify finite identification and all private labels, without accepting source."""
    with contextlib.redirect_stdout(sys.stderr):
        return _evaluate(Path(root).resolve(), task_id, contract, jobs, apply_program)


def _evaluate(root, task_id, contract, jobs, apply_program):
    if not isinstance(task_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', task_id):
        raise ValueError('Invalid task identity')
    catalog = Catalog(root)
    selected = catalog.describe(task_id)
    rule_task_id = selected.get('rule_task_id', task_id)
    canonical = {v.get('program_solution') for v in catalog._variants().get(rule_task_id, [])}
    expected = f'generators/{task_id}/workspace/parametric/adapter.py'
    if not isinstance(contract, dict) or contract.get('adapter') != expected:
        raise ValueError('The adapter must be in this task\'s parametric workspace')
    adapter_path = root / expected
    if (not adapter_path.is_file() or adapter_path.resolve() != adapter_path
            or any((root / Path(*PurePosixPath(expected).parts[:i])).is_symlink()
                   for i in range(1, len(PurePosixPath(expected).parts) + 1))):
        raise ValueError('The adapter must be a regular same-checkout source file')
    parameters = contract.get('parameters')
    if not isinstance(parameters, dict) or any(type(k) is not str for k in parameters):
        raise ValueError('Declared parameters must be an object')
    size = 1
    for key, options in parameters.items():
        if type(options) is not list or not options or len({_typed(v) for v in options}) != len(options):
            raise ValueError(f'Parameter {key} needs distinct typed JSON options')
        size *= len(options)
        if size > 16:
            raise ValueError('At most 16 Cartesian parameter settings are supported')
    default = _settings(contract.get('default'), parameters)
    if not isinstance(jobs, list) or not jobs:
        raise ValueError('At least one qualification job is required')
    normalized_jobs = []
    for job in jobs:
        if not isinstance(job, dict):
            raise ValueError('Qualification jobs must be objects')
        normalized_jobs.append({'seed': _integer(job.get('seed'), 0, 2**63 - 1, 'seed'),
            'settings': _settings(job.get('settings'), parameters),
            'demos': _integer(job.get('demos'), 1, 32, 'demos'),
            'queries': _integer(job.get('queries'), 1, 32, 'queries')})
    keys = sorted(parameters)
    settings = [dict(zip(keys, values)) for values in itertools.product(*(parameters[k] for k in keys))]
    runtime = root / 'shared/runtime'
    with _local_imports(runtime, adapter_path.parent):
        name = '_arc_parametric_' + hashlib.sha256(str(adapter_path).encode()).hexdigest()
        spec = importlib.util.spec_from_file_location(name, adapter_path)
        adapter = importlib.util.module_from_spec(spec)
        sys.modules[name] = adapter
        spec.loader.exec_module(adapter)
        if not callable(getattr(adapter, 'program', None)) or not callable(getattr(adapter, 'generate', None)):
            raise ValueError('Adapter must export program(settings) and generate(seed,settings,demos,queries)')
        programs = [adapter.program(copy.deepcopy(s)) for s in settings]
        if any(type(p) is not str or not p.strip() for p in programs):
            raise ValueError('Every adapter program must be nonempty exact Racket text')
        default_index = next(i for i, setting in enumerate(settings) if _typed(setting) == _typed(default))
        if canonical != {programs[default_index]}:
            raise ValueError('Default program must match the unique selected canonical program byte-for-byte')
        bridge = None
        if apply_program is None:
            apply, identity, bridge = _real_evaluator(runtime)
        else:
            if not callable(apply_program):
                raise ValueError('apply_program must be callable')
            apply, identity = apply_program, {'backend': 'test', 'protected': False}
        episodes, checks, evaluations = [], [], 0
        def execute(program, grid):
            nonlocal evaluations
            evaluations += 1
            return _grid(apply(program, copy.deepcopy(grid)))
        try:
            for job in normalized_jobs:
                chosen = next(i for i, setting in enumerate(settings) if _typed(setting) == _typed(job['settings']))
                generated = adapter.generate(job['seed'], copy.deepcopy(job['settings']), job['demos'], job['queries'])
                if not isinstance(generated, dict) or generated.get('program_solution') != programs[chosen]:
                    raise ValueError('Generated program_solution must equal program(settings) exactly')
                splits = {}
                for split, count in (('train', job['demos']), ('test', job['queries'])):
                    pairs = generated.get(split)
                    if not isinstance(pairs, list) or len(pairs) != count:
                        raise ValueError(f'Generated {split} count does not match request')
                    normalized = []
                    for pair in pairs:
                        if not isinstance(pair, dict) or not {'input', 'output'} <= set(pair):
                            raise ValueError('Each generated pair needs input and output grids')
                        normalized.append({'input': _grid(pair['input']), 'output': _grid(pair['output'])})
                    splits[split] = normalized
                inputs = [json.dumps(p['input']) for split in splits.values() for p in split]
                if len(inputs) != len(set(inputs)):
                    raise ValueError('All demonstration and query inputs must be distinct')
                survivors = []
                for index, program in enumerate(programs):
                    outputs = [execute(program, pair['input']) for pair in splits['train']]
                    if all(output == pair['output'] for output, pair in zip(outputs, splits['train'])):
                        survivors.append(index)
                if survivors != [chosen]:
                    raise ValueError('Demonstrations must identify the selected setting as the sole finite survivor')
                for pair in splits['test']:
                    outputs = [execute(programs[index], pair['input']) for index in survivors]
                    if any(output != pair['output'] or output != outputs[0] for output in outputs):
                        raise ValueError('Racket query labels or surviving rival agreement failed')
                program = programs[chosen]
                episodes.append({'task_id': task_id, 'seed': job['seed'], 'settings': job['settings'],
                    **splits, 'program': program, 'program_sha256': hashlib.sha256(program.encode()).hexdigest(),
                    'reference': 'accepted_parametric'})
                checks.append({'settings': job['settings'], 'seed': job['seed'],
                    'counts': {'demos': job['demos'], 'queries': job['queries']},
                    'survivors': [copy.deepcopy(settings[i]) for i in survivors],
                    'label_count': job['demos'] + job['queries']})
        finally:
            if bridge is not None:
                bridge.close()
    return {'episodes': episodes, 'checks': checks, 'racket': identity, 'racket_evaluations': evaluations}


def main(args=None):
    args = sys.argv[1:] if args is None else args
    try:
        if len(args) != 1:
            raise ValueError('Usage: python -m arcpuzzles.parametric_worker REQUEST.json')
        request = json.loads(Path(args[0]).read_bytes())
        result = evaluate_contract(Path(request['root']), request['task_id'], request['contract'], request['jobs'])
    except Exception as exc:
        print(json.dumps({'error': type(exc).__name__, 'message': str(exc)}))
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
