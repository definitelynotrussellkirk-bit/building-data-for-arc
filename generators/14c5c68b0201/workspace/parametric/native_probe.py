"""Replay bounded native tiling episodes and export actor-safe examples.

Run with the issued review.py launcher. The destination must be a fresh path.
This helper checks labels through the same wrap_rule path as native qualification.
"""
from copy import deepcopy
import argparse
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():
        raise FileExistsError('Choose a fresh evidence directory')
    path=Path(__file__).with_name('adapter.py')
    spec=importlib.util.spec_from_file_location('tiling_native_probe_adapter',path)
    adapter=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    reports,examples,matched=[],[],{}
    labels=0
    with RacketBridge(timeout=10.0,startup_timeout=30.0) as bridge:
        identity=bridge.runtime_identity
        assert identity['backend']=='racket' and identity['protected'] is True
        for seed in (0,17):
            for demos in (2,6):
                for axis in ('both','horizontal','vertical'):
                    settings={'tiling_axes':axis}
                    ep=adapter.generate(seed,settings,demos=demos,queries=4)
                    pairs=ep['train']+ep['test']
                    inputs=[p['input'] for p in pairs]
                    assert len({json.dumps(g) for g in inputs})==len(inputs)
                    key=(seed,demos)
                    if key in matched:
                        assert inputs==matched[key]
                    else:
                        matched[key]=inputs
                    callable_rule=wrap_rule(adapter.program(settings))
                    for pair in pairs:
                        literal="'("+' '.join('('+' '.join(map(str,row))+')' for row in pair['input'])+')'
                        assert bridge.eval_text(f'({callable_rule} {literal})')==pair['output']
                        labels+=1
                    teaching=adapter.teaching_report(ep['train'],settings)
                    assert teaching['all_refuted']
                    single=adapter.generate(seed,settings,demos=demos,queries=1)
                    assert adapter.visible_turn(ep,0)==adapter.visible_turn(single,0)
                    private_changed=deepcopy(ep)
                    private_changed.update(seed=-1,settings={'private':'changed'},program_solution='private')
                    for pair in private_changed['test']:
                        pair['output']=[[0]]
                    assert public_challenge_bytes(private_changed)==public_challenge_bytes(ep)
                    scene=adapter.observables(ep['test'][-1]['input'])
                    assert (scene['height'],scene['width'])==(30,30)
                    assert len(scene['holes'])==2
                    holes_area=sum((h['bbox'][2]-h['bbox'][0]+1)*(h['bbox'][3]-h['bbox'][1]+1) for h in scene['holes'])
                    assert holes_area==288
                    reports.append({'seed':seed,'demos':demos,'queries':4,'settings':settings,
                                    'labels_checked':len(pairs),'teaching':teaching,
                                    'large_scene':scene,'large_hole_cells':holes_area})
                    if seed==0 and demos==2:
                        examples.append(ep)
    args.out.mkdir(parents=True)
    exported=adapter.write_batch(examples,args.out/'examples')
    report={'schema':'14c5c68b0201-native-self-audit-v1','status':'passed',
            'episodes_attempted':len(reports),'episodes_passed':len(reports),'episodes_failed':0,
            'protected_racket_labels':labels,'runtime_identity':identity,'episodes':reports,
            'matched_input_settings':True,'first_turn_prefix_invariance':True,
            'private_field_public_byte_invariance':True,'examples':exported,
            'limits':'Two seeds, all three settings, 2/6 demonstrations and four queries. Finite 10/11-rival teaching check, no owner acceptance or training admission.'}
    (args.out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ('status','episodes_attempted','episodes_passed','episodes_failed','protected_racket_labels')}))


if __name__=='__main__':
    main()
