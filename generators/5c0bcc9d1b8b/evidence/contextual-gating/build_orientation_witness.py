from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK = '5c0bcc9d1b8b'
ROOT = find_root(__file__)
GEN, SOURCE, SHA = load_selected_generator(TASK, root=ROOT)
records = []
for sample_index, profile in enumerate(('n11_vertical_c7', 'n11_horizontal_c7')):
    grid = GEN.generate(17, sample_index, difficulty='medium', scene_profile=profile)
    records.append({'seed':17, 'sample_index':sample_index, 'difficulty':'medium', 'scene_profile':profile, 'input':grid})
out = Path(__file__).resolve().parent
(out/'orientation-inputs.json').write_text(json.dumps([r['input'] for r in records], indent=2)+'\n')
(out/'orientation-request.json').write_text(json.dumps({'task_id':TASK,'generator_sha256':SHA,'records':records}, indent=2)+'\n')
print(json.dumps({'task_id':TASK,'generator_sha256':SHA,'profiles':[r['scene_profile'] for r in records]}, indent=2))
