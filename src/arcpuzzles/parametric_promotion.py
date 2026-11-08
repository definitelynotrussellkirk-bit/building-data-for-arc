"""Explicit, source-bound promotion and use of finite parametric prototypes."""
from __future__ import annotations

from itertools import product
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys
import tempfile

from .catalog import Catalog, local_path, sha256
from .parametric_priority import _prototype
from .runtime import run_process, validate_grid

CONTRACT = 'arcpuzzles-parametric-adapter-v1'
QUALIFICATION = 'arcpuzzles-parametric-qualification-v1'
ACCEPTANCE = 'arcpuzzles-parametric-acceptance-v1'


def _raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode() + b'\n'


def _hash(value):
    return hashlib.sha256(_raw(value)).hexdigest()


def _read(path):
    return json.loads(path.read_bytes())


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_raw(value))


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in [{low}, {high}]')


def settings_space(contract):
    parameters = contract.get('parameters')
    if (not isinstance(parameters, dict) or not parameters
            or any(not isinstance(k, str) or not k.isidentifier() for k in parameters)):
        raise ValueError('Adapter needs named finite parameters')
    for values in parameters.values():
        if (not isinstance(values, list) or not values
                or any(type(v) not in (str, int, bool) for v in values)
                or len({_raw(v) for v in values}) != len(values)):
            raise ValueError('Parameter values must be distinct typed JSON scalars')
    names = sorted(parameters)
    if not 2 <= math.prod(len(parameters[k]) for k in names) <= 16:
        raise ValueError('Adapter must declare between 2 and 16 settings')
    result = [dict(zip(names, values)) for values in product(*(parameters[k] for k in names))]
    _setting(contract, contract.get('default'))
    return result


def _setting(contract, setting):
    parameters = contract['parameters']
    if (not isinstance(setting, dict) or set(setting) != set(parameters)
            or any(_raw(setting[k]) not in {_raw(v) for v in values}
                   for k, values in parameters.items())):
        raise ValueError('Setting keys/typed values differ from declared parameters')
    return setting


def _ready(catalog, task_id):
    row = catalog.describe(task_id)
    if not row['approved']:
        raise ValueError('Production generator must be approved on its current source/rule')
    prototype = _prototype(catalog.root, row)
    if prototype['status'] != 'current':
        raise ValueError('Prototype is not current/ready: ' + str(prototype))
    tid = row['id']; base = f'generators/{tid}/workspace/parametric/'
    path = local_path(catalog.root, base + 'promotion.json')
    contract = _read(path)
    if contract.get('schema') != CONTRACT:
        raise ValueError('Missing or invalid promotion adapter contract')
    adapter = contract.get('adapter')
    if (not isinstance(adapter, str) or not adapter.startswith(base)
            or not adapter.endswith('.py')):
        raise ValueError('Adapter must be a Python file in this prototype home')
    settings_space(contract)
    for name in ('demos', 'queries'):
        values = contract.get('limits', {}).get(name)
        if (not isinstance(values, list) or len(values) != 2
                or any(type(v) is not int for v in values)
                or not 1 <= values[0] <= values[1] <= 32):
            raise ValueError('Adapter needs supported demo/query limits in 1..32')
    files = {row['generator'], base + 'promotion.json', adapter}
    # Source-mode rule_wrap loads this exact same-checkout parser.
    parser = catalog.root/'shared/tools/comment_solutions.py'
    if parser.is_file(): files.add(parser.relative_to(catalog.root).as_posix())
    for folder in (catalog.root/base, catalog.root/'shared/runtime'):
        for source in folder.rglob('*'):
            if (source.is_file() and source.suffix in {'.py', '.rkt', '.json'}
                    and not any(part in {'evidence', 'examples', '__pycache__'}
                                for part in source.relative_to(folder).parts)):
                files.add(source.relative_to(catalog.root).as_posix())
    for name in contract.get('resources', []):
        if not isinstance(name, str) or not name.startswith(base):
            raise ValueError('Adapter resources must stay in this prototype home')
        files.add(name)
    bindings = []
    for name in sorted(files):
        source = local_path(catalog.root, name)
        if source.is_symlink() or any(p.is_symlink() for p in source.parents
                                     if p.is_relative_to(catalog.root)):
            raise ValueError('Symlink in adapter source closure')
        if not source.is_file():
            raise ValueError('Missing adapter source: ' + name)
        bindings.append({'path': name, 'sha256': sha256(source)})
    authority = row.get('rule_task_id', tid)
    programs = {v['program_solution'] for v in catalog._variants().get(authority, [])
                if isinstance(v.get('program_solution'), str)}
    if len(programs) != 1:
        raise ValueError('One exact canonical program is required')
    canonical = next(iter(programs))
    binding = {'task_id': tid, 'rule_task_id': authority, 'generator_sha256': row['generator_sha256'],
               'rule_hash': row['rule_hash'], 'canonical_program_sha256':
               hashlib.sha256(canonical.encode()).hexdigest(), 'files': bindings,
               'executor': {p.name: sha256(p) for p in
                            (Path(__file__), *(Path(__file__).with_name(name) for name in
                              ('parametric_worker.py', 'catalog.py', 'runtime.py', 'parametric_priority.py')))}}
    return contract, binding


def _jobs(contract, *, seed, count, demos, queries, settings=None):
    _integer('seed', seed, 0, 2**63-1)
    _integer('count', count, 1, 1000)
    _integer('last seed', seed + count - 1, 0, 2**63-1)
    for name, value in [('demos', demos), ('queries', queries)]:
        _integer(name, value, *contract['limits'][name])
    space = settings_space(contract)
    if settings is not None: _setting(contract, settings)
    return [{'seed': seed+i, 'settings': settings if settings is not None else
             random.Random(seed+i).choice(space), 'demos': demos, 'queries': queries}
            for i in range(count)]


def _execute(catalog, tid, contract, jobs, timeout):
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('timeout must be finite and positive')
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-parametric-') as temp:
        request = Path(temp)/'request.json'
        _write(request, {'root': str(catalog.root), 'task_id': tid,
                         'contract': contract, 'jobs': jobs})
        package = str(Path(__file__).resolve().parents[1])
        result = run_process([sys.executable, '-m', 'arcpuzzles.parametric_worker', str(request)],
                             catalog.root, timeout=timeout,
                             extra_env={'PYTHONPATH': package, 'PYTHONNOUSERSITE': '1',
                                        'PYTHONDONTWRITEBYTECODE': '1'})
        if result['exit_code'] != 0 or result['timed_out']:
            raise ValueError('Parametric worker failed: ' + result['stderr'][-1800:])
        return json.loads(result['stdout'])


def _check_execution(result, jobs, binding, contract):
    if (result.get('racket', {}).get('backend') != 'racket'
            or result.get('racket', {}).get('protected') is not True
            or type(result.get('racket_evaluations')) is not int
            or result['racket_evaluations'] < sum(j['demos']+j['queries'] for j in jobs)):
        raise ValueError('Qualification requires actual protected Racket evidence')
    episodes, checks = result.get('episodes'), result.get('checks')
    if not isinstance(episodes, list) or not isinstance(checks, list) or len(episodes) != len(jobs) or len(checks) != len(jobs):
        raise ValueError('Worker evidence is incomplete')
    programs = {}
    for episode, check, job in zip(episodes, checks, jobs):
        if (episode.get('task_id') != binding['task_id'] or episode.get('seed') != job['seed']
                or _raw(episode.get('settings')) != _raw(job['settings'])
                or len(episode.get('train', [])) != job['demos']
                or len(episode.get('test', [])) != job['queries']
                or _raw(check.get('survivors')) != _raw([job['settings']])
                or check.get('label_count') != job['demos'] + job['queries']):
            raise ValueError('Worker episode or demo-only certificate differs from request')
        program = episode.get('program')
        if not isinstance(program, str) or episode.get('program_sha256') != hashlib.sha256(program.encode()).hexdigest():
            raise ValueError('Worker program bytes/hash differ')
        if (_raw(job['settings']) == _raw(contract['default'])
                and episode['program_sha256'] != binding['canonical_program_sha256']):
            raise ValueError('Default program differs from exact canonical Racket')
        key = _raw(job['settings']).decode().strip()
        previous = programs.setdefault(key, episode['program_sha256'])
        if previous != episode['program_sha256']:
            raise ValueError('Setting changed programs between episodes')
    return programs


def _acceptance_path(catalog, tid):
    return catalog.root/f'generators/{tid}/parametric/accepted.json'


def status(catalog, task_id):
    tid = catalog.describe(task_id)['id']; path = _acceptance_path(catalog, tid)
    if not path.exists(): return {'task_id': tid, 'status': 'not_accepted', 'training_admitted': False}
    try:
        if path.is_symlink(): raise ValueError('Acceptance must be a local regular file')
        record = _read(path)
        if not isinstance(record, dict): raise ValueError('Invalid acceptance record')
        contract, binding = _ready(Catalog(catalog.root), tid)
        if record.get('schema') != ACCEPTANCE or record.get('source_binding') != binding:
            raise ValueError('Accepted source or rule changed')
        qid = record.get('qualification_id')
        if not isinstance(qid, str) or len(qid) != 64 or any(c not in '0123456789abcdef' for c in qid):
            raise ValueError('Invalid acceptance qualification identity')
        base = f'generators/{tid}/evidence/parametric-acceptance/{qid}/'
        expected = {base+'qualification.json', base+'execution.json'}
        if (not isinstance(record.get('files'), list) or len(record['files']) != 2
                or {item.get('path') for item in record['files']} != expected):
            raise ValueError('Incomplete accepted qualification inventory')
        for item in record['files']:
            if sha256(local_path(catalog.root, item['path'])) != item['sha256']:
                raise ValueError('Accepted qualification evidence changed')
        q = _read(catalog.root/(base+'qualification.json'))
        execution = _read(catalog.root/(base+'execution.json'))
        if (q.get('schema') != QUALIFICATION or q.get('owner_acceptance_reexecuted') is not True
                or _hash(q) != qid or q.get('source_binding') != binding
                or q.get('contract') != contract
                or q['execution'].get('sha256') != sha256(catalog.root/(base+'execution.json'))
                or _check_execution(execution, q['jobs'], binding, contract) != record.get('programs')
                or _raw(record.get('parameters')) != _raw(contract['parameters'])
                or _raw(record.get('default')) != _raw(contract['default'])
                or record.get('limits') != contract['limits']):
            raise ValueError('Accepted qualification snapshot differs')
        if record.get('status') != 'accepted': raise ValueError('Not accepted')
        return {**record, 'acceptance_sha256': sha256(path)}
    except (ValueError, KeyError, OSError, TypeError, AttributeError) as error:
        return {'task_id': tid, 'status': 'stale', 'reason': str(error), 'training_admitted': False}


def qualify(catalog, task_id, output, *, seeds=None, demos=3, queries=4, timeout=180):
    catalog = Catalog(catalog.root); tid = catalog.describe(task_id)['id']
    contract, binding = _ready(catalog, tid)
    seeds = [0, 17] if seeds is None else seeds
    if not isinstance(seeds, list) or not 2 <= len(seeds) <= 8 or len(set(_raw(s) for s in seeds)) != len(seeds):
        raise ValueError('Qualification needs 2..8 distinct fresh seeds')
    _integer('qualification queries', queries, 4, 32)
    jobs = [job for setting in settings_space(contract) for seed in seeds
            for job in _jobs(contract, seed=seed, count=1, demos=demos,
                             queries=queries, settings=setting)]
    output = Path(output)
    if output.exists() or output.is_symlink(): raise FileExistsError(output)
    result = _execute(catalog, tid, contract, jobs, timeout)
    programs = _check_execution(result, jobs, binding, contract)
    if _ready(Catalog(catalog.root), tid)[1] != binding:
        raise ValueError('Adapter sources changed during qualification')
    output.mkdir(parents=True, exist_ok=False)
    execution = output/'execution.json'; _write(execution, result)
    report = {'schema': QUALIFICATION, 'status': 'qualified', 'task_id': tid,
              'source_binding': binding, 'contract': contract, 'jobs': jobs,
              'programs': programs, 'execution': {'path': 'execution.json', 'sha256': sha256(execution)},
              'limits': 'Fresh finite settings/seeds only; no universal identifiability or measured training gain.',
              'training_admitted': False}
    receipt = output/'qualification.json'; _write(receipt, report)
    return {**report, 'receipt': str(receipt.resolve())}


def accept(catalog, task_id, qualification, *, reason):
    from .review import _lock
    if not isinstance(reason, str) or not reason.strip(): raise ValueError('Acceptance reason is required')
    with _lock(catalog.root/'REVIEW'):
        catalog = Catalog(catalog.root); tid = catalog.describe(task_id)['id']
        contract, binding = _ready(catalog, tid); path = Path(qualification); q = _read(path)
        if (q.get('schema') != QUALIFICATION or q.get('status') != 'qualified'
                or q.get('source_binding') != binding or q.get('contract') != contract):
            raise ValueError('Qualification differs from current source/contract')
        coverage = {}
        jobs = q.get('jobs', [])
        if not isinstance(jobs, list) or not jobs:
            raise ValueError('Missing qualification coverage')
        for job in jobs:
            _jobs(contract, seed=job['seed'], count=1, demos=job['demos'],
                  queries=job['queries'], settings=job['settings'])
            _integer('qualification queries', job['queries'], 4, 32)
            key = _raw(job['settings'])
            seeds = coverage.setdefault(key, set())
            if job['seed'] in seeds: raise ValueError('Duplicate qualification seed')
            seeds.add(job['seed'])
        if (set(coverage) != {_raw(x) for x in settings_space(contract)}
                or any(not 2 <= len(seeds) <= 8 for seeds in coverage.values())):
            raise ValueError('Qualification needs two fresh seeds per setting')
        if q.get('execution', {}).get('path') != 'execution.json':
            raise ValueError('Invalid qualification evidence path')
        execution = path.parent/'execution.json'
        if sha256(execution) != q['execution']['sha256']:
            raise ValueError('Qualification evidence changed')
        submitted = _read(execution)
        programs = _check_execution(submitted, q['jobs'], binding, contract)
        if programs != q['programs'] or set(programs) != {_raw(x).decode().strip() for x in settings_space(contract)}:
            raise ValueError('Qualification does not cover every setting')
        # A returned JSON receipt is a claim, even if it contains hashes and
        # says protected=true. Acceptance performs its own bounded execution.
        fresh = _execute(catalog, tid, contract, jobs, 180)
        if (_check_execution(fresh, jobs, binding, contract) != programs
                or _raw(fresh['episodes']) != _raw(submitted['episodes'])
                or _raw(fresh['checks']) != _raw(submitted['checks'])):
            raise ValueError('Fresh acceptance replay differs from qualification evidence')
        if _ready(Catalog(catalog.root), tid)[1] != binding:
            raise ValueError('Adapter changed during fresh acceptance recheck')
        execution_bytes = _raw(fresh)
        q = {**q, 'submitted_qualification_sha256': sha256(path),
             'owner_acceptance_reexecuted': True,
             'execution': {'path': 'execution.json',
                           'sha256': hashlib.sha256(execution_bytes).hexdigest()}}
        qid = _hash(q); folder = catalog.root/f'generators/{tid}/evidence/parametric-acceptance/{qid}'
        folder.mkdir(parents=True, exist_ok=True)
        for name, data in [('qualification.json', _raw(q)), ('execution.json', execution_bytes)]:
            target = folder/name
            if target.exists() and target.read_bytes() != data: raise ValueError('Changed qualification snapshot')
            target.write_bytes(data)
        record = {'schema': ACCEPTANCE, 'status': 'accepted', 'task_id': tid,
                  'source_binding': binding, 'parameters': contract['parameters'],
                  'default': contract['default'], 'limits': contract['limits'],
                  'qualification_id': qid, 'reason': reason.strip(), 'programs': programs,
                  'training_admitted': False,
                  'files': [{'path': p.relative_to(catalog.root).as_posix(), 'sha256': sha256(p)}
                            for p in sorted(folder.iterdir()) if p.is_file()]}
        target = _acceptance_path(catalog, tid); target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.tmp'); _write(temporary, record); os.replace(temporary, target)
        return status(catalog, tid)


def generate(catalog, task_id, *, count=1, seed=0, demos=3, queries=4, settings=None, timeout=180):
    catalog = Catalog(catalog.root); accepted = status(catalog, task_id)
    if accepted['status'] != 'accepted':
        raise ValueError('Parametric generator is not currently accepted: ' + str(accepted))
    tid = accepted['task_id']; contract, binding = _ready(catalog, tid)
    jobs = _jobs(contract, seed=seed, count=count, demos=demos, queries=queries, settings=settings)
    result = _execute(catalog, tid, contract, jobs, timeout)
    programs = _check_execution(result, jobs, binding, contract)
    if any(accepted['programs'].get(setting) != digest for setting, digest in programs.items()):
        raise ValueError('Generated program differs from the accepted setting program')
    if status(Catalog(catalog.root), tid).get('acceptance_sha256') != accepted['acceptance_sha256']:
        raise ValueError('Accepted source changed during generation')
    for episode, certificate in zip(result['episodes'], result['checks']):
        episode.update(parametric_accepted=True, training_admitted=False,
                       provenance={'generator_sha256': binding['generator_sha256'],
                                   'canonical_rule_hash': binding['rule_hash'],
                                   'parametric_acceptance_sha256': accepted['acceptance_sha256'],
                                   'racket_runtime': result['racket'],
                                   'demo_only_certificate': certificate})
    return result['episodes']


def _public(episode):
    return {'train': [{'input': validate_grid(p['input']), 'output': validate_grid(p['output'])}
                      for p in episode['train']],
            'test': [{'input': validate_grid(p['input'])} for p in episode['test']]}


def export(catalog, task_id, output, **options):
    output = Path(output)
    if output.exists() or output.is_symlink(): raise FileExistsError(output)
    episodes = generate(catalog, task_id, **options)
    planned = []
    for episode in episodes:
        public = _public(episode); payload = _raw(public)
        identifier = hashlib.sha256(payload).hexdigest()
        planned.append((identifier, payload, episode))
    if len({x[0] for x in planned}) != len(planned):
        raise ValueError('duplicate visible challenge in export')
    planned.sort(key=lambda x: x[0])
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='parametric-export-', dir=output.parent) as temp:
        stage = Path(temp); (stage/'public').mkdir()
        public_rows, private_rows = [], []
        for identifier, payload, episode in planned:
            (stage/'public'/f'{identifier}.json').write_bytes(payload)
            public_rows.append(_raw({'episode_id': identifier, **json.loads(payload)}))
            private_rows.append(_raw({'episode_id': identifier, **episode}))
        (stage/'public.jsonl').write_bytes(b''.join(public_rows))
        (stage/'private.jsonl').write_bytes(b''.join(private_rows))
        manifest = {'schema': 'arcpuzzles-parametric-export-v1', 'status': 'complete',
                    'task_id': episodes[0]['task_id'], 'episodes': len(episodes),
                    'dataset_id': _hash([x[0] for x in planned]), 'training_admitted': False,
                    'parametric_acceptance_sha256': episodes[0]['provenance']['parametric_acceptance_sha256'],
                    'files': [{'path': p.relative_to(stage).as_posix(), 'sha256': sha256(p)}
                              for p in sorted(stage.rglob('*')) if p.is_file()]}
        _write(stage/'manifest.json', manifest)
        output.mkdir(exist_ok=False)
        # Manifest moves last. Interrupted publication remains visibly incomplete.
        for name in ['public', 'public.jsonl', 'private.jsonl', 'manifest.json']:
            os.replace(stage/name, output/name)
    return verify_export(output)


def verify_export(output):
    output = Path(output); manifest = _read(output/'manifest.json')
    if manifest.get('schema') != 'arcpuzzles-parametric-export-v1' or manifest.get('status') != 'complete':
        raise ValueError('Incomplete parametric export')
    files=manifest.get('files')
    actual={p.relative_to(output).as_posix() for p in output.rglob('*')
            if p.is_file() and p.name!='manifest.json'}
    if (not isinstance(files,list) or len(files)!=len(actual)
            or {row.get('path') for row in files}!=actual
            or not {'public.jsonl','private.jsonl'} <= actual):
        raise ValueError('Export inventory is incomplete or differs from files')
    for row in manifest['files']:
        if sha256(local_path(output, row['path'])) != row['sha256']:
            raise ValueError('Export file changed: ' + row['path'])
    public = [json.loads(line) for line in (output/'public.jsonl').read_bytes().splitlines()]
    private = [json.loads(line) for line in (output/'private.jsonl').read_bytes().splitlines()]
    ids = [row['episode_id'] for row in public]
    if len(public) != manifest['episodes'] or len(private) != len(public) or ids != sorted(set(ids)):
        raise ValueError('Export counts/IDs differ')
    for visible, hidden in zip(public, private):
        for split in ('train','test'):
            if not hidden.get(split): raise ValueError('Export has empty grid pairs')
            for pair in hidden[split]:
                validate_grid(pair['input']);validate_grid(pair['output'])
        if hidden.get('provenance',{}).get('parametric_acceptance_sha256') != manifest.get('parametric_acceptance_sha256'):
            raise ValueError('Export acceptance provenance differs')
        payload = _raw(_public(hidden)); identifier = hashlib.sha256(payload).hexdigest()
        if (visible != {'episode_id': identifier, **json.loads(payload)}
                or hidden['episode_id'] != identifier
                or (output/'public'/f'{identifier}.json').read_bytes() != payload):
            raise ValueError('Export public/private projection differs')
    if manifest['dataset_id'] != _hash(ids): raise ValueError('Export dataset ID differs')
    return manifest
