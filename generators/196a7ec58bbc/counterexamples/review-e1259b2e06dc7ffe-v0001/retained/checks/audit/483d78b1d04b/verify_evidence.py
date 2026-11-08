import json,pathlib,hashlib,sys
OUT=pathlib.Path(__file__).parent
probe=json.loads((OUT/'probe.json').read_text());racket=json.loads((OUT/'racket.json').read_text());production=json.loads((OUT/'production-seed6.jsonl').read_text());combined=json.loads((OUT/'combined/result.json').read_text())
assert len(racket['results'])==5 and all(x['error'] is None for x in racket['results'])
pairs=probe['filled_rectangle_lesson_probe']['pairs']
assert all(p['input']==r['input'] and p['border_prediction']==r['output'] for p,r in zip(pairs,racket['results'][1:],strict=True))
assert probe['validator_counterexample']['input']==racket['results'][0]['input']
actual=production['train']+production['test']
assert all(p['input']==r['input'] and p['border_prediction']==r['output'] for p,r in zip(pairs,actual,strict=True))
matches=[p['filled_rival_prediction']==r['output'] for p,r in zip(pairs,actual,strict=True)]
assert matches==[True,True,True,False]
assert production['sample_indices']==[0,1,2,3] and production['rejections']==[]
assert racket['generator_sha256']==probe['generator_sha256']==combined['audit_summary']['generator_sha256']==production['provenance']['generator_sha256']
verification={'status':'verified_findings','generator_sha256':probe['generator_sha256'],'rule_text_sha256':racket['rule_text_sha256'],'executed_rule_hash':racket['executed_rule_hash'],'racket_pairs':5,'racket_errors':0,'production_episode_seed':6,'production_sample_indices':production['sample_indices'],'production_rejections':0,'filled_rival_demo_matches':matches[:3],'filled_rival_query_match':matches[3],'checked_files_sha256':{f:hashlib.sha256((OUT/f).read_bytes()).hexdigest() for f in ['probe.json','racket.json','production-seed6.jsonl','combined/result.json']}}
(OUT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
py='/workspace/scratch/d2d336ea4d37/arc-review/WORK/.venv-review/bin/python'
prefix=[py,'review.py','run',py]
rows=[('strict_combined_audit',['-m','arcpuzzles','check','483d78b1d04b','--stage','audit','--phase','audit','--timeout','1200','--out','../checks/audit/483d78b1d04b/combined'],1,['combined/result.json','combined/checks/483d78b1d04b_audit_semantic_gate.json']),('bounded_adversarial_probe',['../checks/audit/483d78b1d04b/probe.py'],0,['probe.json','input.json']),('canonical_reference_execution',['-m','arcpuzzles','apply','483d78b1d04b','--input','../checks/audit/483d78b1d04b/input.json','--out','../checks/audit/483d78b1d04b/racket.json'],0,['racket.json']),('production_episode_reproduction',['-m','arcpuzzles','generate','483d78b1d04b','--allow-unapproved','--count','1','--seed','6','--difficulty','easy','--train','3','--test','1','--out','../checks/audit/483d78b1d04b/production-seed6.jsonl'],0,['production-seed6.jsonl']),('evidence_assertions',['../checks/audit/483d78b1d04b/verify_evidence.py'],0,['verification.json'])]
commands={'task_id':'483d78b1d04b','generator_sha256':probe['generator_sha256'],'rule_text_sha256':racket['rule_text_sha256'],'commands':[{'name':n,'cwd':'packet_root','argv':prefix+a,'exit_code':e,'evidence_paths':['checks/audit/483d78b1d04b/'+f for f in fs]} for n,a,e,fs in rows]}
(OUT/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
print(json.dumps(verification))
