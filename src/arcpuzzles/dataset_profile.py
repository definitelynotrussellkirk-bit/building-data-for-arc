"""Controller-only dimensions and supervision counts from verified exports."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import median

from .datasets import verify_dataset
from .host_dataset import is_grid


def _ratio(count, denominator):
    return {'count': count, 'fraction': count / denominator if denominator else None}


def _shape(value):
    if not is_grid(value):
        raise ValueError('Profile grids must be rectangular 1..30 with exact integer colors0..9')
    return len(value), len(value[0])


def _summary(shapes, detailed):
    n = len(shapes);areas = [h*w for h,w in shapes]
    longest = [max(h,w) for h,w in shapes]
    def hits(predicate):return _ratio(sum(predicate(h,w) for h,w in shapes), n)
    bands = [('1-10', 1, 10), ('11-15', 11, 15), ('16-20', 16, 20), ('21-29', 21, 29), ('30', 30, 30)]
    result = {'grids': n, 'cells': sum(areas),
        'median_height': median([h for h,_ in shapes]) if n else None,
        'median_width': median([w for _,w in shapes]) if n else None,
        'median_area': median(areas) if n else None,
        'exact_30x30': hits(lambda h,w: h==w==30),
        'longest_side_at_least_20': hits(lambda h,w: max(h,w)>=20),
        'longest_side_over_20': hits(lambda h,w: max(h,w)>20),
        'both_sides_at_least_20': hits(lambda h,w: min(h,w)>=20),
        'area_at_least_400': hits(lambda h,w: h*w>=400),
        'max_side_bands': {name:_ratio(sum(low<=side<=high for side in longest),n) for name,low,high in bands}}
    if detailed:
        result['shapes'] = {f'{h}x{w}':count for (h,w),count in sorted(Counter(shapes).items())}
    return result


def _bound_rows(root, manifest, name):
    raw = (root/name).read_bytes();wanted = manifest['files'][name]
    if len(raw)!=wanted['bytes'] or hashlib.sha256(raw).hexdigest()!=wanted['sha256']:
        raise ValueError('Dataset input changed while profiling: '+name)
    # JSONL is LF-delimited; Unicode line separators inside strings stay data.
    return [json.loads(line) for line in raw.split(b'\n') if line.strip()]


def profile_dataset(directory, *, detailed_shapes=False):
    """Verify once, then describe captured bytes without changing the artifact.

    Query-output dimensions are private controller information. Cell/pair ratios
    are not token ratios, semantic difficulty or proof of training consumption.
    """
    if type(detailed_shapes) is not bool:raise ValueError('detailed_shapes must be a boolean')
    root = Path(directory).resolve();manifest_path = root/'manifest.json'
    manifest_raw = manifest_path.read_bytes()
    try:
        manifest = verify_dataset(root)
    except (TypeError, KeyError, AttributeError, IndexError) as error:
        raise ValueError('Malformed export metadata/projection: '+str(error)) from error
    if manifest_path.read_bytes()!=manifest_raw:
        raise ValueError('Dataset manifest changed while verifying')
    public = _bound_rows(root, manifest, 'public.jsonl')
    private = _bound_rows(root, manifest, 'labels.private.jsonl')
    roles = {name:[] for name in ['demonstration_inputs','demonstration_outputs','query_inputs','query_outputs']}
    demos,queries = Counter(),Counter()
    repeated = seen_in_demos = four_novel = 0
    for task,labels in zip(public,private):
        train,test = task['train'],task['test'];demos[len(train)]+=1;queries[len(test)]+=1
        for pair in train:
            roles['demonstration_inputs'].append(_shape(pair['input']))
            roles['demonstration_outputs'].append(_shape(pair['output']))
        for pair,answer in zip(test,labels['test_outputs']):
            roles['query_inputs'].append(_shape(pair['input']))
            roles['query_outputs'].append(_shape(answer))
        key = lambda value: json.dumps(value,separators=(',',':'))
        train_inputs = {key(p['input']) for p in train}
        test_inputs = [key(p['input']) for p in test]
        repeated += len(test_inputs)-len(set(test_inputs))
        seen_in_demos += sum(value in train_inputs for value in test_inputs)
        four_novel += len(set(test_inputs)-train_inputs)>=4
    grids = {name:_summary(values,detailed_shapes) for name,values in roles.items()}
    demo_count = grids['demonstration_inputs']['grids'];query_count = grids['query_inputs']['grids']
    demo_cells = grids['demonstration_outputs']['cells'];query_cells = grids['query_outputs']['cells']
    if manifest_path.read_bytes()!=manifest_raw:
        raise ValueError('Dataset manifest changed while profiling')
    return {'schema':'arcpuzzles-export-size-profile-v1','visibility':'controller_only',
        'dataset_id':manifest['dataset_id'],'manifest_sha256':hashlib.sha256(manifest_raw).hexdigest(),
        'observed_episodes':len(public),'export_style':manifest['options']['style'],
        'verification':{'status':'passed_hashes_and_projection','files':len(manifest['files']),
                        'racket_reexecuted':False,'generator_executed':False},
        'source_files':{name:manifest['files'][name] for name in ['public.jsonl','labels.private.jsonl']},
        'supervision':{'demonstration_pairs':demo_count,'query_pairs':query_count,
            'demos_per_episode':{str(k):v for k,v in sorted(demos.items())},
            'queries_per_episode':{str(k):v for k,v in sorted(queries.items())},
            'query_pairs_per_demonstration_pair':query_count/demo_count if demo_count else None,
            'query_output_cells_per_demo_output_cell':query_cells/demo_cells if demo_cells else None,
            'episodes_with_four_distinct_novel_queries':_ratio(four_novel,len(public)),
            'repeated_query_inputs_within_episodes':repeated,
            'query_inputs_repeating_demonstrations':seen_in_demos},
        'grids':grids,'detailed_shapes':detailed_shapes,
        'scope':'Observed exported episode grids and pair/cell counts only. Empty denominators are unknown. No measure of content span, model tokens, actual training consumption or learning benefit; no admission or mixture change.'}
