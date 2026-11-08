from pathlib import Path
import ast, collections, hashlib, json, random
root = Path.cwd()
if root.name == 'repo':
    root = root.parent
repo = root / 'repo'
seed = '4512a8b45b15a68449e0fb6cf342af8e44218bfa3a1bcdc15ff85a38328a8e54'
manifest = json.loads((root / 'PACKET-MANIFEST.json').read_text())
ids = random.Random(int(seed, 16)).sample(sorted(manifest['generators']), 3)
assert ids == ['57a410fce3c9', '94d475bf67ba', '20d2c3da584a']
source = repo / 'generators/20d2c3da584a/generator.py'
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash == '014464ab3ad440e84abae9d2e79ed598e78f81a133be574274f2a62be7a1e798'
tree = ast.parse(source.read_text())
shapes = next(ast.literal_eval(n.value) for n in ast.walk(tree)
    if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'shapes' for t in n.targets))
bbox_shapes = [[max(r for r,c in s)-min(r for r,c in s)+1,
                max(c for r,c in s)-min(c for r,c in s)+1] for s in shapes]
assert bbox_shapes == [[3,2], [3,2], [2,3], [2,3]]
assert all(h <= 2 or width <= 2 for h,width in bbox_shapes)
def components(grid):
    todo = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v != 0}
    result = []
    while todo:
        start = min(todo); todo.remove(start)
        color = grid[start[0]][start[1]]; stack = [start]; cells = []
        while stack:
            r,c = stack.pop(); cells.append((r,c))
            for pos in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                if pos in todo and grid[pos[0]][pos[1]] == color:
                    todo.remove(pos); stack.append(pos)
        result.append((color,cells))
    return result
def fill_bbox(grid):
    result = [row[:] for row in grid]
    for color,cells in components(grid):
        r0=min(r for r,c in cells); r1=max(r for r,c in cells)
        c0=min(c for r,c in cells); c1=max(c for r,c in cells)
        for r in range(r0,r1+1):
            for c in range(c0,c1+1): result[r][c] = color
    return result
canonical = repo / 'shared/data/canonical/puzzles.jsonl'
records = [json.loads(line) for line in canonical.read_text().splitlines()]
row = next(row for row in records if row['task_id'] == '20d2c3da584a')
disagreements=[]
for index,pair in enumerate(row['train']):
    grid=[[int(v) for v in line] for line in pair['input']]
    expected=[[int(v) for v in line] for line in pair['output']]
    rival=fill_bbox(grid)
    for r,line in enumerate(expected):
        for c,value in enumerate(line):
            if rival[r][c] != value:
                disagreements.append({'split':'train','index':index,'row':r,'column':c,
                    'canonical_output':value,'fill_bbox_rival':rival[r][c]})
assert disagreements == [
    {'split':'train','index':1,'row':5,'column':4,'canonical_output':0,'fill_bbox_rival':9},
    {'split':'train','index':3,'row':8,'column':4,'canonical_output':0,'fill_bbox_rival':4}]
row57 = next(row for row in records if row['task_id'] == '57a410fce3c9')
canonical57=[]
for split in ['train','test']:
    pairs=row57[split]
    pairs=[pairs] if isinstance(pairs,dict) else pairs
    for index,pair in enumerate(pairs):
        g=[[int(v) for v in line] for line in pair['input']]
        canonical57.append({'split':split,'index':index,'shape':[len(g),len(g[0])],
            'zero_rows':[r for r,line in enumerate(g) if all(v==0 for v in line)],
            'zero_columns':[c for c in range(len(g[0])) if all(line[c]==0 for line in g)]})
assert canonical57[-1]['split']=='test' and canonical57[-1]['zero_rows']==[7]
print(json.dumps({'sampled_ids':ids,'generator_sha256':source_hash,
    'canonical_sha256':hashlib.sha256(canonical.read_bytes()).hexdigest(),
    'current_57a_canonical_zero_lines':canonical57,'shape_bank_bbox_dimensions':bbox_shapes,'canonical_rival_disagreements':disagreements,
    'interpretation':'The fixed generated shape grammar cannot distinguish border-only painting from whole-box filling, although two canonical demonstrations do.',
    'scope':'Fresh AST/record comparison only; no generator execution, no Racket execution, no claim about all possible rivals or training outcomes.'},sort_keys=True))
