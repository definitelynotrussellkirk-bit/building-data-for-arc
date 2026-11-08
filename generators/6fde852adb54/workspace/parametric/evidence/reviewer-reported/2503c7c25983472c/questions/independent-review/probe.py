"""One bounded independent gate probe; no source changes or Racket executions."""
import copy,hashlib,importlib.util,json
from collections.abc import Mapping
from pathlib import Path
W=Path(__file__).resolve().parents[3]
T=W/'repo/generators/6fde852adb54'
paths=[T/'generator.py',T/'workspace/questions/question_gate.py',T/'workspace/questions/probe_questions.py',T/'tests/test_question_gate.py']
def hashes():
    return {str(f.relative_to(W)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths}
before=hashes()
assert before['repo/generators/6fde852adb54/generator.py']=='f7a534e4c744da6f32b2576f5831721a01f71a7ec0df48694fd97c52bbd176db'
spec=importlib.util.spec_from_file_location('independent_question_gate',paths[1])
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
row=next(json.loads(line) for line in (W/'repo/shared/data/canonical/puzzles.jsonl').read_text().splitlines() if json.loads(line).get('task_id')=='6fde852adb54' and json.loads(line).get('source')=='training')
demos=row['train'];query={'input':g.make_witness()};original=copy.deepcopy((demos,query))
records=[]
def check(name,ds,qs,expected,predictor=None):
    report=g.lesson_gate(ds,qs,canonical_predict=predictor or g.GENERATOR.rule_mirror)
    assert report['status']==expected,(name,report)
    records.append({'case':name,'status':report['status'],'demo_matches':report['demo_matches'],'query_difference_cells':report['query_difference_cells']})
    return report
baseline=check('canonical_demos_leave_witness_ambiguous',demos,query,'ambiguous')
assert baseline['demo_matches']==[True,True,True] and baseline['query_difference_cells']==6
class SealedQuery(Mapping):
    def __init__(self):self.access=[]
    def __getitem__(self,key):
        self.access.append(key)
        if key!='input':raise AssertionError('private key was read: '+key)
        return query['input']
    def __iter__(self):raise AssertionError('query metadata was enumerated')
    def __len__(self):raise AssertionError('query metadata length was read')
sealed=SealedQuery()
assert check('mapping_reads_only_input',demos,sealed,'ambiguous')==baseline
assert set(sealed.access)=={'input'}
for label,value in [('absent_sentinel',None),('boolean_grid',[[False]]),('rival_answer',g.rival_predict(query['input'])),('arbitrary_object',object())]:
    candidate={'input':query['input'],'output':value,'private_answer':object(),'task_id':'wrong'}
    assert check('query_label_'+label,demos,candidate,'ambiguous')==baseline
same=check('surviving_rival_answer_equivalent',demos,{'input':row['test'][0]['input']},'pass')
assert same['demo_matches']==baseline['demo_matches'] and same['query_difference_cells']==0
fixed=demos+[{'input':query['input'],'output':g.GENERATOR.rule_mirror(query['input'])}]
fixed_query={'input':g.make_witness(height=18,width=20,start=7,reflected=True)}
fixed_report=check('only_discriminating_demo_eliminates_rival',fixed,fixed_query,'pass')
assert fixed_report['demo_matches']==[True,True,True,False] and fixed_report['query_difference_cells']==6
calls=[]
def forbidden(grid):calls.append(grid);raise AssertionError('malformed data reached reference')
malformed_queries=[None,[],{}, {'input':None},{'input':[]},{'input':[[]]},{'input':[[7]*14]},{'input':[[7]*14,[7]*13]}, {'input':[[False]*14]*14},{'input':[[7.0]*14]*14},{'input':[[10]*14]*14}]
for i,bad in enumerate(malformed_queries):check('malformed_query_'+str(i),demos,bad,'invalid',forbidden)
malformed_demos=[None,{},[],[None],[{}],[{'input':query['input']}],[{'output':query['input']}],[{'input':[],'output':[]}],[{'input':query['input'],'output':[[False]*14]*14}],[{'input':query['input'],'output':[[7]*13]*14}],[{'input':tuple(query['input']),'output':query['input']}]]
for i,bad in enumerate(malformed_demos):check('malformed_demos_'+str(i),bad,query,'invalid',forbidden)
assert not calls
wrong=copy.deepcopy(demos);wrong[0]['output'][0][0]=(wrong[0]['output'][0][0]+1)%10
check('well_formed_wrong_demo_label',wrong,query,'invalid')
for label,value in [('none',None),('bool',True),('ragged',[[1],[1,2]]),('boolean_grid',[[False]*14]*14),('float_grid',[[7.0]*14]*14),('wrong_shape',[[7]])]:
    check('reference_return_'+label,demos,query,'reference_error',lambda _,v=value:v)
def failed(_):raise RuntimeError('controlled reference failure')
check('reference_raises',demos,query,'reference_error',failed)
count=[0]
def broken_query(grid):
    count[0]+=1
    return g.GENERATOR.rule_mirror(grid) if count[0]<=len(demos) else [[False]]
check('reference_query_only_malformed',demos,query,'reference_error',broken_query)
assert count[0]==len(demos)+1
mutating_calls=[]
def mutating(grid):
    answer=g.GENERATOR.rule_mirror(grid);grid[0][0]=(grid[0][0]+1)%10;mutating_calls.append(1);return answer
assert check('reference_input_copy_isolation',demos,query,'ambiguous',mutating)==baseline
assert len(mutating_calls)==len(demos)+1
assert (demos,query)==original
assert hashes()==before,'source changed during independent probe'
print(json.dumps({'schema':'question-gate-independent-probe-v1','status':'pass','source_hashes':before,'case_count':len(records),'cases':records,'scope':'one fixed validation and noninterference matrix, Python mirror used as supplied reference; no fresh Racket run, CLI runtime-failure injection, seed sweep, or universal rival claim'},indent=2))
