from pathlib import Path
import json
from reviewer_support import find_root, load_selected_generator, canonical_pairs
ROOT=find_root(Path(__file__).resolve().parents[3]/'repo')
GEN, PATH, SHA=load_selected_generator('2b34f380ed25', root=ROOT)
pairs=canonical_pairs('2b34f380ed25', root=ROOT, labeled_only=True)
rows=[]
for profile in GEN.PUBLIC_PROFILES:
    grid=GEN.generate(11,29,scene_profile=profile)
    facts=GEN._extract_facts(grid)
    rows.append({
      'profile':profile,
      'signature':[entry[2] for entry in GEN._panel_signature(facts)],
      'macro_shape':[len(facts['row_bands']),len(facts['col_bands'])],
      'row_cuts':facts['row_cuts'],'col_cuts':facts['col_cuts'],
      'changed':facts['changed'],
    })
print(json.dumps({'generator_sha256':SHA,'canonical_splits':[p['split'] for p in pairs],'profiles':rows},indent=2))
