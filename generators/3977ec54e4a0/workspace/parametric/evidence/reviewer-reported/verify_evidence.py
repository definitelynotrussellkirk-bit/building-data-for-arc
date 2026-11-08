"""Independent structural/hash audit of the retained parametric evidence."""
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / 'repo'
ARTIFACT = HERE / 'all-settings'


def digest(value):
    if not isinstance(value, bytes):
        value = value.encode() if isinstance(value, str) else json.dumps(
            value, sort_keys=True, separators=(',', ':')).encode()
    return sha256(value).hexdigest()


report = json.loads((ARTIFACT/'private/report.json').read_text())
assert report['status'] == 'PASS'
assert report['episode_count'] == 8
assert report['train_count'] == 3 and report['test_count'] == 4
assert len(report['programs']) == 8
assert len({row['sha256'] for row in report['programs']}) == 8
for source in report['source_manifest']:
    assert digest((ROOT/source['path']).read_bytes()) == source['sha256'], source
programs = {}
for row in report['programs']:
    raw = (ARTIFACT/row['path']).read_bytes()
    assert digest(raw) == row['sha256']
    programs[(row['parameters']['fill_color'],row['parameters']['fill_edges'])] = raw
assert set(programs) == {(c,e) for c in (2,4,6,8) for e in (False,True)}
assert digest(programs[(8,True)]) == 'b4c2540796af088ba41f486413b1be85ff6f8a9db373d30e6105bdc4529c7f25'
observed_settings, episodes, globally_unique = set(), [], set()
for record in report['episodes']:
    for kind in ('public','private'):
        assert digest((ARTIFACT/record[kind+'_path']).read_bytes()) == record[kind+'_sha256']
    public = json.loads((ARTIFACT/record['public_path']).read_text())
    private = json.loads((ARTIFACT/record['private_path']).read_text())
    params = private['parameters']
    setting = params['fill_color'],params['fill_edges']
    observed_settings.add(setting)
    assert private['program'].encode() == programs[setting]
    assert set(public) == {'train','test'}
    assert len(public['train']) == 3 and len(public['test']) == 4
    assert all(set(pair) == {'input','output'} for pair in public['train'])
    assert all(set(pair) == {'input'} for pair in public['test'])
    assert len(private['pairs']) == 7
    hashes = [digest(pair['input']) for pair in private['pairs']]
    assert len(set(hashes)) == 7
    globally_unique.update(hashes)
    for i,pair in enumerate(private['pairs']):
        assert (public['train']+public['test'])[i]['input'] == pair['input']
        if i < 3:
            assert public['train'][i]['output'] == pair['output']
        accepted = private['report']['sampling']['accepted_pairs'][i]
        assert accepted['sample_index'] == pair['sample_index']
        assert accepted['input_sha256'] == digest(pair['input'])
        assert accepted['output_sha256'] == digest(pair['output'])
    scores = private['report']['finite_rivals']
    assert len(scores) == 16
    assert private['report']['demo_selection_used_query_answers'] is False
    assert private['report']['generator_sha256'] == '406ea39bd1050f238678d02ce90c50e02a8dd6e24e214d739398783ec7c5e603'
    for row in scores:
        namespace,name = row['name'].split(':',1)
        key = 'parameter_predictions' if namespace == 'parameter' else 'lesson_competitor_predictions'
        refuted = [i for i,pair in enumerate(private['pairs'][:3]) if pair[key][name] != pair['output']]
        disagreed = [i for i,pair in enumerate(private['pairs'][3:]) if pair[key][name] != pair['output']]
        assert row['refuting_demonstration_indices'] == refuted
        assert row['query_disagreement_indices'] == disagreed
        assert refuted or (row['chosen_program'] and not disagreed)
    assert all(row['identified'] and row['disagreeing_survivors'] == [] for row in private['report']['query_checks'])
    episodes.append({'parameters':params,'seed':private['seed'],
                     'accepted_indices':[p['sample_index'] for p in private['pairs']],
                     'attempts':private['report']['sampling']['attempts'],
                     'demo_windows':len(private['report']['sampling']['demo_windows'])})
assert observed_settings == set(programs)
probe = json.loads((ARTIFACT/'private/diagnostic-probe.json').read_text())
assert probe['kind'] == 'diagnostic_probe' and probe['status'] == 'ambiguous'
assert probe['demonstration_matches'] == [True]*3 and probe['query_matches'] == [False]
assert probe['query_differences'] == [{'column':3,'inclusive':8,'row':3,'strict':0}]
canonical = json.loads((ARTIFACT/'private/canonical-parity.json').read_text())
assert canonical['labeled_pairs_checked'] == 8 and canonical['unique_inputs'] == 4
result = {'status':'PASS', 'artifact':str(ARTIFACT), 'episodes':episodes,
          'total_demonstrations':24,'total_queries':32,
          'unique_inputs_within_each_episode':7,'unique_inputs_across_all_episodes':len(globally_unique),
          'racket_programs':8,'finite_rivals_per_episode':16,
          'canonical_labels_checked':8,'source_files_bound':len(report['source_manifest']),
          'diagnostic_query_differences':probe['query_differences'],
          'limit':'This audits retained hashes/structure/scores; the CLI and tests provide reference execution evidence.'}
(HERE/'integrity-report.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
