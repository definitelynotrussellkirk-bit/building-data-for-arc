import json,hashlib
from pathlib import Path
root=Path('/workspace/scratch/b1624dafaa34/arc-review/WORK/repo')
print('SOURCE_SHA256',hashlib.sha256((root/'generators/0727bca3d518/generator.py').read_bytes()).hexdigest())
for line in (root/'shared/data/canonical/puzzles.jsonl').open():
 if '0727bca3d518' not in line:continue
 row=json.loads(line)
 if row['task_id']!='0727bca3d518':continue
 print('RULE',row['program_solution'])
 print('RULE_HASH',hashlib.sha256(' '.join(row['program_solution'].split()).encode()).hexdigest()[:12])
 for split in ['train','test']:
  for i,p in enumerate(row[split]):
   print(split,i,p)
