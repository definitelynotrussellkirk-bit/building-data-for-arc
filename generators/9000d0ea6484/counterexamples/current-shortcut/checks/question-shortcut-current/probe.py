from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK='9000d0ea6484'
root=find_root(__file__)
mod,path,source_hash=load_selected_generator(TASK,root=root)
overrides=dict(sec0_color=1,sec1_color=2,sec2_color=4,sec3_color=9,extra_overlap_count=5)
grid=mod.generate(41,7,difficulty='medium',**overrides)
intended=mod.rule_mirror(grid)
rival=mod.SEMANTIC_RIVALS['fixed_canonical_color_priority'](grid)
mismatches=[{'row':r,'col':c,'intended':intended[r][c],'rival':rival[r][c]}
            for r in range(4) for c in range(4) if intended[r][c]!=rival[r][c]]
report={
 'task_id':TASK,'generator_source':path.relative_to(root).as_posix(),'generator_sha256':source_hash,
 'seed':41,'sample_index':7,'difficulty':'medium','overrides':overrides,
 'input':grid,'input_sha256':hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest(),
 'self_check_errors':mod.self_check(grid,difficulty='medium'),
 'observed_overrides':mod.observe_overrides(grid),
 'intended_output':intended,'rival':'fixed canonical color priority 9 > 4 > 8 > 5',
 'rival_output':rival,'mismatches':mismatches,
}
out=Path(__file__).with_name('counterexample.json')
out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
Path(__file__).with_name('input.json').write_text(json.dumps({'inputs':[grid]},indent=2)+'\n')
print(json.dumps({'out':str(out),'generator_sha256':source_hash,'input_sha256':report['input_sha256'],'mismatch_count':len(mismatches)},indent=2))
assert report['self_check_errors']==[] and len(mismatches)==4
