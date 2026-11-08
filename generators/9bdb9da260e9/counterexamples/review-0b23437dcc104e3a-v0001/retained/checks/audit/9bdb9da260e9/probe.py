import importlib.util, json
from pathlib import Path
path=Path('generators/9bdb9da260e9/generator.py')
spec=importlib.util.spec_from_file_location('audit_9bdb',path)
g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
grid=g.generate(0, 0, texture='missing_match')
report={
  'task_id': g.TASK_ID,
  'generator_version': g.VERSION,
  'probe': 'public generate(seed=0, sample_index=0, texture=missing_match)',
  'input': grid,
  'self_check': g.self_check(grid),
  'colors': sorted({v for row in grid for v in row}),
  'shape': [len(grid), len(grid[0])],
}
Path('../checks/audit/9bdb9da260e9/missing_match_input.json').write_text(json.dumps(grid,indent=2)+'\n')
Path('../checks/audit/9bdb9da260e9/probe.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report,indent=2,sort_keys=True))
