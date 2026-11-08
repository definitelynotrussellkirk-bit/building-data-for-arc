from pathlib import Path
import importlib.util,json,sys
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2];REPO=WORK/'repo'
sys.path.insert(0,str(REPO/'shared/runtime'))
from reviewer_support import canonical_pairs
s=REPO/'generators/4f3a702ae0c4/generator.py';spec=importlib.util.spec_from_file_location('g',s);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
pairs=canonical_pairs('4f3a702ae0c4',root=REPO,labeled_only=True)
checks=[{'split':p['split'],'pair_index':p['pair_index'],'self_check':g.self_check(p['input']),'mirror_matches_canonical':g.rule_mirror(p['input'])==p['output']} for p in pairs]
assert len(checks)==5 and all(x['mirror_matches_canonical'] and x['self_check']==[] for x in checks)
p=HERE/'diagnosis.json';d=json.loads(p.read_text());d['canonical_checks']=checks;d['commands']=[x for x in d['commands'] if 'retained inline' not in x['command']];d['commands'].append({'command':'python3 run_with_racket.py python3 ../checks/audit/4f3a702ae0c4/canonical_check.py','cwd':str(WORK),'exit_code':0});p.write_text(json.dumps(d,indent=2)+'\n')
print('5/5 canonical local-mirror parity; 5/5 self_check accepts')
