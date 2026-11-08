"""Capture/replay a prior sampler's unsupported two-demo lesson gap.

Capture reads frozen packet baseline source. Replay uses retained exact inputs
and programs and needs no old implementation. No query label informs fitting.
"""
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path.cwd().resolve()
TASK = '8e6c44aee812'
HOME = ROOT / f'generators/{TASK}/workspace/parametric'
RUNTIME = ROOT / 'shared/runtime'
sys.path[:0] = [str(ROOT/'src'), str(RUNTIME)]
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run(output, replay=None):
    if output.exists():
        raise FileExistsError(output)
    with _local_imports(RUNTIME, HOME):
        audit = load(HOME/'audit_native.py', '_staircase_prefix_audit')
        if replay is None:
            baseline = ROOT.parent/'.review/baseline/repo'/f'generators/{TASK}'
            prior_path = baseline/'workspace/parametric/prototype.py'
            prior = load(prior_path, '_staircase_prior_prototype')
            episode = prior.generate_episode(0, difficulty='easy', output_scale=3,
                                             demo_count=2, query_count=4)
            settings = {'output_scale': 3}
            rival_name = 'first_run_per_color'
            assert all(audit.rival_reference(p['input'], settings, rival_name) == p['output']
                       for p in episode['train'])
            candidates = [i for i, p in enumerate(episode['test'])
                          if audit.rival_reference(p['input'], settings, rival_name) != p['output']]
            assert candidates, 'No prior short-prefix counterexample in the fixed episode'
            index = candidates[0]
            prior_reasons = prior.lesson_identifiable(episode['train'], episode['test'][index], output_scale=3)
            document = {
                'schema': '8e6c44aee812-short-prefix-probe-v1', 'task_id': TASK,
                'mode': 'capture_prior_baseline', 'settings': settings,
                'recipe': {'seed': 0, 'difficulty': 'easy', 'demo_count': 2,
                           'query_count': 4, 'selected_query_index': index},
                'prior_sources_sha256': {
                    'generator.py': sha((baseline/'generator.py').read_bytes()),
                    'workspace/parametric/prototype.py': sha(prior_path.read_bytes())},
                'probe_sha256': sha(Path(__file__).read_bytes()),
                'rival': rival_name,
                'reference_program': episode['program'],
                'rival_program': audit.rival_program(settings, rival_name),
                'train': deepcopy(episode['train']), 'test': [deepcopy(episode['test'][index])],
                'prior_lesson_check': prior_reasons,
                'limits': 'Prior generate_episode accepted demo_count=2, but its legacy lesson checker rejected fewer than five demonstrations. This is an unsupported short-context sampler gap, not a claim of previously accepted training corruption. The fixed episode and one disagreeing query are a finite witness; no prevalence claim.',
                'training_admitted': False,
            }
        else:
            document = json.loads(replay.read_text())
            assert document['schema'] == '8e6c44aee812-short-prefix-probe-v1'
            document['mode'] = 'replay_retained_inputs_and_programs'
            document['replayed_evidence_sha256'] = sha(replay.read_bytes())
        apply, identity, bridge = _real_evaluator(RUNTIME)
        assert identity['backend'] == 'racket' and identity['protected'] is True
        try:
            document['racket'] = identity
            count = 0
            demo_fit = []
            for split in ('train', 'test'):
                for pair in document[split]:
                    reference = _grid(apply(document['reference_program'], pair['input']))
                    rival = _grid(apply(document['rival_program'], pair['input']))
                    count += 2
                    assert reference == pair['output']
                    assert reference == audit.reference(pair['input'], document['settings'])
                    assert rival == audit.rival_reference(pair['input'], document['settings'], document['rival'])
                    pair['rival_output'] = rival
                    pair['different_cells'] = [[r,c] for r,row in enumerate(reference)
                                               for c,v in enumerate(row) if rival[r][c] != v]
                    if split == 'train':
                        demo_fit.append(not pair['different_cells'])
            document['racket_evaluations'] = count
            document['demonstration_fit'] = all(demo_fit)
            document['finding_confirmed'] = all(demo_fit) and bool(document['test'][0]['different_cells'])
            assert document['finding_confirmed']
            document['reference_program_sha256'] = sha(document['reference_program'].encode())
            document['rival_program_sha256'] = sha(document['rival_program'].encode())
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(document, indent=2, sort_keys=True)+'\n')
        finally:
            bridge.close()
    print(json.dumps({'output': str(output), 'finding_confirmed': document['finding_confirmed'],
                      'different_cells': len(document['test'][0]['different_cells']),
                      'racket_evaluations': document['racket_evaluations'],
                      'prior_lesson_check': document['prior_lesson_check']}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    args=parser.parse_args()
    run(args.out, args.replay)
