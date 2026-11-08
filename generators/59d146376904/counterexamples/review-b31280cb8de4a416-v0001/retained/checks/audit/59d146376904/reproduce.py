import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator
TASK='59d146376904'
root=find_root(__file__)
generator, source, source_hash=load_selected_generator(TASK, root=root)
requested={'seed':0,'sample_index':0,'difficulty':'easy','overrides':{'grid_h':4}}
grid=generator.generate(requested['seed'],requested['sample_index'],difficulty=requested['difficulty'],**requested['overrides'])
tied=generator.generate(0,0,texture='tied_majority')
record={
 'schema':'arcpuzzles-audit-reproducer-v1',
 'task_id':TASK,
 'generator_path':source.relative_to(root).as_posix(),
 'generator_sha256':source_hash,
 'findings':[
   {
     'id':'A1',
     'kind':'ignored_exact_override',
     'call':requested,
     'requested_grid_h':4,
     'observed_shape':[len(grid),len(grid[0])],
     'self_check':generator.self_check(grid),
     'input':grid,
     'reproduced':len(grid)!=4 and generator.self_check(grid)==[],
   },
   {
     'id':'A2',
     'kind':'validator_accepts_tied_majority_degenerate',
     'call':{'seed':0,'sample_index':0,'difficulty':None,'overrides':{'texture':'tied_majority'}},
     'observed_shape':[len(tied),len(tied[0])],
     'top_left_nonzero_counts':{'4':2,'6':2},
     'self_check':generator.self_check(tied),
     'input':tied,
     'reproduced':generator.self_check(tied)==[],
   }
 ],
 'command': ['python3','review.py','run','python3','../checks/audit/59d146376904/reproduce.py'],
 'cwd':'packet_root',
}
Path('../checks/audit/59d146376904/reproducer.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(json.dumps({f['id']:f['reproduced'] for f in record['findings']},sort_keys=True))
