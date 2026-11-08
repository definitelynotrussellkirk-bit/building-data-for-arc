#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import prototype as p


def dump(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    out=args.out.resolve(); public=out/'public'; private=out/'private'
    public.mkdir(parents=True,exist_ok=True); private.mkdir(parents=True,exist_ok=True)
    assignments=((0,'split_both'),(1,'clockwise_only'),(3,'counterclockwise_only'))
    errors=[]; manifest=[]; reference_inputs=None
    for seed,setting in assignments:
        episode=p.build_episode(seed,setting)
        inputs=[x['input'] for x in episode['demonstrations']]+[episode['query']['input']]
        if reference_inputs is None:
            reference_inputs=[p.make_scene(seed*1009+i) for i in range(4)]
        for pair_index,item in enumerate(episode['demonstrations']+[episode['query']]):
            grid=item['input']; expected=item['output']
            if not p.is_lawful_scene(grid): errors.append(f'{setting} pair {pair_index}: unlawful input')
            outs={s:p.solve(grid,s) for s in p.SETTINGS}
            if len({json.dumps(v,separators=(',',':')) for v in outs.values()})!=3:
                errors.append(f'{setting} pair {pair_index}: settings not distinguishable')
            if outs[setting]!=expected:
                errors.append(f'{setting} pair {pair_index}: private label mismatch')
            try:
                racket=p.run_racket(grid,setting)
                if racket!=expected: errors.append(f'{setting} pair {pair_index}: Racket/Python mismatch')
            except Exception as exc:
                errors.append(f'{setting} pair {pair_index}: Racket error: {exc}')
        pub=p.public_projection(episode)
        if 'output' in pub['query']: errors.append(f'{setting}: query label leaked publicly')
        pub_path=public/f'episode-{setting}.json'; priv_path=private/f'episode-{setting}.json'
        dump(pub_path,pub); dump(priv_path,episode)
        manifest.append({
            'seed':seed,'setting':setting,
            'public':str(pub_path.relative_to(out)),
            'private':str(priv_path.relative_to(out)),
            'demonstrations':len(episode['demonstrations']),
            'query_labeled_private':True,
            'all_pairs_distinguish_settings':True,
        })
    checked,mismatches=p.check_canonical_training()
    if checked<1: errors.append('canonical task source not found')
    if mismatches: errors.append(f'canonical default mismatches {len(mismatches)}/{checked} public training pairs')
    canonical=p.extract_canonical_program()
    snapshot=p.HERE/'racket'/'canonical-source.rkt'
    if snapshot.read_text()!=canonical: errors.append('canonical source snapshot drifted')
    dump(private/'same-input-setting-witness.json',{
        'seed':23,
        'input':p.make_scene(23),
        'outputs':{s:p.solve(p.make_scene(23),s) for s in p.SETTINGS},
    })
    report={
        'status':'passed' if not errors else 'failed',
        'task_id':p.TASK_ID,
        'parameter':'branch_mode',
        'canonical_setting':p.CANONICAL_SETTING,
        'settings':list(p.SETTINGS),
        'semantics':p.SEMANTICS,
        'canonical_training_pairs_checked':checked,
        'canonical_training_mismatches':len(mismatches),
        'canonical_program_sha256':hashlib.sha256(canonical.encode()).hexdigest(),
        'generator_sha256':hashlib.sha256(p.GENERATOR.read_bytes()).hexdigest(),
        'episodes':manifest,
        'errors':errors,
    }
    dump(out/'manifest.json',{'episodes':manifest,'public_private_separated':True})
    dump(out/'report.json',report)
    return 0 if not errors else 1

if __name__=='__main__':
    raise SystemExit(main())
