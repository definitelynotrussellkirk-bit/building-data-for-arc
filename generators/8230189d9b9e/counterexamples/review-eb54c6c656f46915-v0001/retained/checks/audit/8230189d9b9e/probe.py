"""Read-only focused audit: public canonical data, integer controls and rotation."""
import hashlib
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator, canonical_pairs

TASK='8230189d9b9e'
ROOT=find_root(__file__)
G,source,sha=load_selected_generator(TASK,root=ROOT)
DEST=Path(__file__).parent

def main():
    row=next(json.loads(line) for line in (ROOT/'shared/data/canonical/puzzles.jsonl').read_text().splitlines() if json.loads(line).get('task_id')==TASK)
    program=row['program_solution']
    pairs=canonical_pairs(TASK,root=ROOT,labeled_only=True)
    canonical=[{'mirror_matches':G.rule_mirror(p['input'])==p['output'],'self_check':G.self_check(p['input'])} for p in pairs]
    controls=[]
    for name,value in [('seed',True),('seed',1.5),('seed','1'),('sample_index',True),('sample_index',1.5),('sample_index','1'),('sample_index',-1)]:
        kwargs={'seed':1,'sample_index':1};kwargs[name]=value
        try:
            grid=G.generate(**kwargs)
            if name == 'seed' and value is True:
                (DEST/'invalid_seed_bool_input.json').write_text(json.dumps(grid)+'\n')
                (DEST/'invalid_seed_bool_expected.json').write_text(json.dumps(G.rule_mirror(grid))+'\n')
            controls.append({'argument':name,'value':value,'accepted':True,'self_check':G.self_check(grid),'same_as_int_coercion':grid==G.generate(int(kwargs['seed']),int(kwargs['sample_index']))})
        except Exception as exc:
            controls.append({'argument':name,'value':value,'accepted':False,'exception':type(exc).__name__,'message':str(exc)})
    # Ordinary lesson: four consecutive demos plus one query. Rotate the five
    # pairs to reveal whether a unique repetition witness can become the query.
    seed=0;start=0;band='easy'
    grids=[G.generate(seed,start+i,difficulty=band) for i in range(5)]
    expected=[G.rule_mirror(grid) for grid in grids]
    rival=G.LESSON_COMPETITORS['deduplicate_repeated_query']
    agrees=[rival(grid)==output for grid,output in zip(grids,expected)]
    query_index=2
    demos=[{'input':grid,'output':output} for i,(grid,output) in enumerate(zip(grids,expected)) if i!=query_index]
    query={'input':grids[query_index]}
    hook=G.lesson_identifiable(demos,query)
    assert agrees==[True,True,False,True,True],agrees
    assert hook and all(G.self_check(grid)==[] for grid in grids)
    for i,grid in enumerate(grids):
        (DEST/f'input_{i}.json').write_text(json.dumps(grid)+'\n')
    (DEST/'input.json').write_text(json.dumps(grids[query_index])+'\n')
    (DEST/'expected.json').write_text(json.dumps(expected[query_index])+'\n')
    (DEST/'rival.json').write_text(json.dumps(rival(grids[query_index]))+'\n')
    report={'task_id':TASK,'generator_sha256':sha,'version':G.VERSION,'rule_hash':hashlib.sha256(' '.join(program.split()).encode()).hexdigest()[:12],'rule_text_sha256':hashlib.sha256(program.encode()).hexdigest(),'review_index_present':(source.parent/'evidence/review_index.json').is_file(),'canonical_pairs':canonical,'controls':controls,'rotation':{'seed':seed,'start_sample_index':start,'difficulty':band,'query_original_sample_index':query_index,'demo_original_sample_indices':[0,1,3,4],'rival':'deduplicate_repeated_query','agreements_in_original_order':agrees,'self_checks':[G.self_check(grid) for grid in grids],'lesson_identifiable_reasons':hook,'reference_output_shape':[len(expected[query_index]),len(expected[query_index][0])],'rival_output_shape':[len(rival(grids[query_index])),len(rival(grids[query_index])[0])]},'limits':'No selected Racket execution or full battery performed. Reference expected is the task Python mirror, read against canonical Racket source and verified on all three labeled canonical pairs. Rotation ambiguity is detected by the existing lesson hook; production unrotated schedule is not shown faulty.'}
    (DEST/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
