"""Independent reading of the selected visible public task; no hidden answers."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
raw=(HERE/'public-challenge.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='6dece13d6599eea896cbb0ebece1f8098a602b601f2030026d3674cc08b4155c'
data=json.loads(raw)
def tile(g,r,c):
 return tuple(tuple(g[y][x] for x in range(c,c+3)) for y in range(r,r+3))
def infer(g):
 assert len(g)==30 and all(len(row)==22 for row in g)
 catalog={tile(g,8+5*r,2+5*c):(r,c) for r in range(4) for c in range(4)}
 assert len(catalog)==16
 header=[tile(g,1,2+5*c) for c in range(4)]
 matches=[catalog[t] for t in header if any(v!=8 for row in t for v in row)]
 complete=len(set(matches))==4 and (len({r for r,c in matches})==1 or len({c for r,c in matches})==1)
 o=[row[:] for row in g]
 for rr,cc in matches:
  for y in range(7+5*rr,12+5*rr):
   for x in range(1+5*cc,6+5*cc):
    if o[y][x]==8:o[y][x]=3
 if complete:
  for y in range(5):
   o[y]=[3 if v==8 else v for v in o[y]]
 for y in (28,29):o[y]=[3 if complete else 2]*22
 return o,matches,complete
report={'schema':'independent-visible-focus-reading-v1','parent_id':'d8e07eb2',
 'public_challenge_sha256':hashlib.sha256(raw).hexdigest(),
 'inference':'Match exact glyph and color; mark catalog tiles; complete row/column gives positive header/footer.',
 'scope':'Independent fixed-layout public-task interpretation; not the generalized prototype or a hidden-answer score.',
 'limits':['The four-match completion requirement is a declared interpretation: supplied successes use four distinct header glyphs; shorter aligned selections are untested by the supplied examples.','Training pair zero disagrees with this rule in the second header glyph; no special-case patch or noise verdict is asserted.'],
 'train':[],'test':[]}
pred=[]
for i,pair in enumerate(data['train']):
 o,matches,complete=infer(pair['input']);actual=pair['output']
 differences=[{'row':y,'col':x,'inferred':o[y][x],'supplied':actual[y][x]} for y in range(30) for x in range(22) if o[y][x]!=actual[y][x]]
 report['train'].append({'index':i,'header_matches':matches,'complete_line':complete,'match':not differences,'different_cells':differences})
for i,pair in enumerate(data['test']):
 o,matches,complete=infer(pair['input'])
 report['test'].append({'index':i,'header_matches':matches,'complete_line':complete,'hidden_answer_status':'not_available'})
 pred.append({'index':i,'predicted_output':o,'status':'inferred_proposal_not_scored'})
report['matching_train_pairs']=sum(r['match'] for r in report['train'])
report['total_train_pairs']=len(report['train'])
(HERE/'root-read.json').write_text(json.dumps(report,indent=2)+'\n')
(HERE/'root-predicted-answers.json').write_text(json.dumps({'public_challenge_sha256':report['public_challenge_sha256'],'test':pred},separators=(',',':'))+'\n')
print(json.dumps({'training_matches':report['matching_train_pairs'],'training_pairs':report['total_train_pairs'],'difference_cells':[len(r['different_cells']) for r in report['train']],'queries':report['test']}))
