"""Read-only baseline fixed-point rival reproduction; no solve artifacts used."""
from pathlib import Path
from collections import Counter
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent / 'repo'
sys.path.insert(0, str(ROOT / 'shared/runtime'))
sys.path.insert(0, str(ROOT / 'src'))
from reviewer_support import canonical_pairs
from arcpuzzles.catalog import Catalog
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper

BASELINE_SHA = '3d840b93077aaf640b9f596ce1a41298424d35edcdb3e2e78d96ee6dc4029a27'
source = ROOT / 'generators/b3d7f3a15b3d/evidence/reviewer-solves/contexts' / BASELINE_SHA / 'generator.py'
assert hashlib.sha256(source.read_bytes()).hexdigest() == BASELINE_SHA
spec = importlib.util.spec_from_file_location('baseline_generator', source)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
production_source = ROOT / 'generators/b3d7f3a15b3d/generator.py'
production_sha_before = hashlib.sha256(production_source.read_bytes()).hexdigest()

def fixed(grid):
    """Independent closure with original common/color/offset roles frozen."""
    nr,nc=(len(grid)-1)//5,(len(grid[0])-1)//5
    values=[grid[1+5*r+dr][1+5*c+dc] for r in range(nr) for c in range(nc)
            for dr in (1,2) for dc in (1,2)]
    common=Counter(values).most_common(1)[0][0]
    colors=sorted(set(values)-{0,common})
    current=[row[:] for row in grid]
    for _ in range(50):
        out=[row[:] for row in current]
        for color in colors:
            for dr in (1,2):
                for dc in (1,2):
                    for r in range(nr):
                        anchors=[c for c in range(nc) if current[1+5*r+dr][1+5*c+dc]==color]
                        if len(anchors)>=2:
                            for c in range(min(anchors),max(anchors)+1):
                                out[1+5*r+dr][1+5*c+dc]=color
                    for c in range(nc):
                        anchors=[r for r in range(nr) if current[1+5*r+dr][1+5*c+dc]==color]
                        if len(anchors)>=2:
                            for r in range(min(anchors),max(anchors)+1):
                                out[1+5*r+dr][1+5*c+dc]=color
        if out == current:
            return out
        current = out
    raise RuntimeError('fixed point did not converge')

def diffs(a, b):
    return [[r,c,a[r][c],b[r][c]] for r in range(len(a)) for c in range(len(a[0])) if a[r][c] != b[r][c]]

pairs = canonical_pairs(g.TASK_ID, root=ROOT)
variants=Catalog(ROOT).get(g.TASK_ID)['variants']
programs={row['program_solution'] for row in variants if row.get('program_solution')}
assert len(programs)==1
program=programs.pop()
body=strip_rule_wrapper(program)
assert body.startswith('(lambda (g)')
bridge=RacketBridge()
def official_apply(grid):
    bridge.define_grid('g',grid)
    return bridge.eval_text(f'({body} g)')

def stable_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
try:
    canonical = []
    for pair in pairs:
        official = official_apply(pair['input'])
        canonical.append({**{k:v for k,v in pair.items() if k not in ('input','output')}, 'official_matches_label': official == pair['output'], 'fixedpoint_matches_label': fixed(pair['input']) == pair['output']})
    hand = g._blank_scene(3,3,8,4)
    for r,c in [(0,0),(0,2),(2,1)]:
        g._put_marker(hand,r,c,(1,1),2)
    for r,c in [(0,0),(2,0)]:
        g._put_marker(hand,r,c,(2,2),3)
    hand_output = official_apply(hand)
    assert hand_output[7][7]==4 and fixed(hand)[7][7]==2
    lesson = []
    for index in range(4):
        grid = g.generate(15,index,difficulty=None)
        output = official_apply(grid)
        assert output == g.rule_mirror(grid)
        lesson.append({'seed':15,'sample_index':index,'difficulty':None,'input':grid,'output':output,'fixedpoint_differences':diffs(output,fixed(grid))})
    assert lesson[3]['output'][12][7]==8 and fixed(lesson[3]['input'])[12][7]==2
    assert [bool(pair['fixedpoint_differences']) for pair in lesson]==[False,False,False,True]
    assert len(canonical)==8 and all(row['official_matches_label'] and row['fixedpoint_matches_label'] for row in canonical)
    counts = []
    first_ambiguities = []
    for band in [None,'easy','medium','hard']:
        count = Counter()
        first = None
        for seed in range(50):
            flags = []
            for index in range(4):
                grid = g.generate(seed,index,difficulty=band)
                disagreement = fixed(grid) != g.rule_mirror(grid)
                count[(index,disagreement)] += 1
                flags.append(disagreement)
            if first is None and flags == [False,False,False,True]:
                first = seed
        counts.append({'difficulty':band,'counts':[{'sample_index':i,'fixedpoint_differs':d,'n':n} for (i,d),n in sorted(count.items())]})
        first_ambiguities.append({'difficulty':band,'first_seed':first})
    receipt = {'baseline_source':str(source.relative_to(ROOT)),'source_sha256':BASELINE_SHA,'rule_hash':g.RULE_HASH,'canonical_program_sha256':hashlib.sha256(program.encode()).hexdigest(),'canonical_occurrences':canonical,'canonical_unique_inputs':len({json.dumps(p['input']) for p in pairs}),'hand_witness':{'input':hand,'official_output':hand_output,'self_check_errors':g.self_check(hand),'mirror_matches_official':g.rule_mirror(hand)==hand_output,'fixedpoint_differences':diffs(hand_output,fixed(hand))},'official_lesson':lesson,'baseline_lesson_identifiable_errors':g.lesson_identifiable(lesson[:3],lesson[3]),'census_seed_range':[0,49],'census':counts,'first_ambiguous_seed_by_band':first_ambiguities}
    assert hashlib.sha256(production_source.read_bytes()).hexdigest()==production_sha_before
    receipt.update(schema='canonical-adversary-supported-api-v2',
        probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        production_source_sha256_before=production_sha_before,
        production_source_sha256_after=hashlib.sha256(production_source.read_bytes()).hexdigest(),
        canonical_pairs_sha256=stable_hash(pairs),
        scope={'canonical_occurrences':8,'canonical_unique_inputs':4,'official_hand_scenes':1,'official_lesson_pairs':4,'census_seeds':[0,49],'census_indices':[0,1,2,3],'census_difficulties':[None,'easy','medium','hard'],'census_draws':800,'census_label_basis':'baseline Python mirror; canonical8+hand1+lesson4 independently checked with supported RacketBridge'},
        rival_semantics='Independent simultaneous per-color/per-offset row-and-column span iteration; original common color and propagated colors frozen before iteration.',
        official_api='Catalog.get + RacketBridge.define_grid/eval_text + strip_rule_wrapper')
    receipt['scope_sha256']=stable_hash(receipt['scope'])
    receipt['census_disagreements']=sum(item['n'] for band in counts for item in band['counts'] if item['fixedpoint_differs'])
    (HERE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('hand_witness','official_lesson')},indent=2))
    print('HAND_DIFFS',receipt['hand_witness']['fixedpoint_differences'])
    print('LESSON_DIFFS',[p['fixedpoint_differences'] for p in lesson])
finally:
    bridge.close()
