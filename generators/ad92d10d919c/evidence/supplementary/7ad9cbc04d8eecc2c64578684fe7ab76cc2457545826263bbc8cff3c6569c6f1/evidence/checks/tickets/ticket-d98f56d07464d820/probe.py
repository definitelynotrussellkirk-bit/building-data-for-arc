#!/usr/bin/env python3
from __future__ import annotations
import hashlib, inspect, importlib.util, json
from pathlib import Path

repo=Path.cwd().resolve()
manifest_path=repo/'generators/ad92d10d919c/workspace/parametric/evidence/manifest.json'
expected_manifest='5c8c6e9f3391c736e5e506e2beaf171717ea4ac03818340dd6604ef89f5d16f1'
assert hashlib.sha256(manifest_path.read_bytes()).hexdigest()==expected_manifest
manifest=json.loads(manifest_path.read_text())
generator=repo/'generators/ad92d10d919c/generator.py'
assert hashlib.sha256(generator.read_bytes()).hexdigest()==manifest['generator_sha256']=='c58bf9b69b5aad40ea5f186d1bd46ed4b9ae57d04ff98d458955f09f2ebc2f27'
for row in manifest['files']:
 p=repo/row['path']; data=p.read_bytes()
 assert len(data)==row['bytes']
 assert hashlib.sha256(data).hexdigest()==row['sha256']

prototype_path=repo/'generators/ad92d10d919c/workspace/parametric/prototype.py'
spec=importlib.util.spec_from_file_location('ticket_ad92_parametric',prototype_path)
assert spec and spec.loader
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
sig=str(inspect.signature(module.generate_episode))

root=repo/'generators/ad92d10d919c/workspace/parametric/evidence/gallery'
episodes=[]
for public_path in sorted((root/'public').glob('episode-*.json')):
 private_path=root/'private'/public_path.name
 public=json.loads(public_path.read_text())
 private=json.loads(private_path.read_text())
 assert set(public)=={'train','test'}
 assert len(public['train'])==3 and len(public['test'])==1
 assert all(set(q)=={'input'} for q in public['test'])
 assert len(private['train'])==3 and len(private['test'])==1
 assert 'output' in private['test'][0]
 assert private['parameters']['required_matches'] in (3,4)
 episodes.append({
  'public_file':public_path.name,
  'required_matches':private['parameters']['required_matches'],
  'train_count':len(public['train']),
  'query_count':len(public['test']),
  'public_query_keys':sorted(public['test'][0]),
  'private_query_has_output':True,
 })
result={
 'schema':'supplementary-parameter-queries-v1',
 'ticket_id':'ticket-d98f56d07464d820',
 'status':'completed',
 'pinned_manifest_sha256':expected_manifest,
 'generator_sha256':manifest['generator_sha256'],
 'parameter_space':manifest['parameters'],
 'generate_episode_signature':sig,
 'episodes':episodes,
 'boundary_result':{
  'public_private_masking':'pass',
  'fixed_setting_per_episode':'pass',
  'retained_simultaneous_queries_per_episode':1,
  'four_query_support_in_pinned_evidence':False,
 },
 'assessment':'Pinned evidence masks the single query label correctly, but exposes no independent demo/query count interface and retains only one simultaneous query per setting. This supports prototype follow-up only and does not imply variant approval.',
}
out=Path(__file__).with_name('result.json'); out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
