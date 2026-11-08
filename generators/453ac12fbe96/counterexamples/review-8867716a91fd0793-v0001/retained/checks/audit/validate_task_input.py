import argparse, hashlib, importlib, json
from pathlib import Path

p=argparse.ArgumentParser(); p.add_argument('task'); p.add_argument('input'); p.add_argument('out'); a=p.parse_args()
gen=importlib.import_module(f'puzzle_generators.per_puzzle.{a.task}.generator')
grid=json.loads(Path(a.input).read_text())
path=Path(gen.__file__)
result={'task_id':a.task,'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'self_check':gen.self_check(grid),'input':grid}
Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2,sort_keys=True))
