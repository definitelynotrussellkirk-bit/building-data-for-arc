import hashlib, importlib.util, json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
REPO=ROOT/'repo'
sys.path.insert(0,str(REPO/'shared/runtime'))
spec=importlib.util.spec_from_file_location('audit_target',REPO/'generators/4cccb4dba000/generator.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def components(g):
 seen=set();out=[]
 for r,row in enumerate(g):
  for c,v in enumerate(row):
   if not v or (r,c) in seen:continue
   seen.add((r,c));stack=[(r,c)];cells=[]
   while stack:
    a,b=stack.pop();cells.append((a,b))
    for x in range(a-1,a+2):
     for y in range(b-1,b+2):
      if 0<=x<len(g) and 0<=y<len(g[0]) and g[x][y] and (x,y) not in seen:
       seen.add((x,y));stack.append((x,y))
   bb=[min(a for a,b in cells),min(b for a,b in cells),max(a for a,b in cells),max(b for a,b in cells)]
   out.append({'bbox':bb,'red_count':sum(g[a][b]==2 for a,b in cells),'area':len(cells),'output':[row[bb[1]:bb[3]+1] for row in g[bb[0]:bb[2]+1]]})
 return out
kwargs={'grid_h':22,'grid_w':22,'n_clusters':5,'cluster_size_kind':'small','red_count_distribution':'wide_spread'}
probes=[]
for sample in range(8):
 g=m.generate(0,sample,difficulty="hard",**kwargs);cs=components(g);reds=[c['red_count'] for c in cs]
 entry={'seed':0,'sample_index':sample,'difficulty':'hard','overrides':kwargs,'red_counts':reds,'self_check':m.self_check(g)}
 probes.append(entry)
 if reds.count(max(reds))>1:
  winners=[c for c in cs if c['red_count']==max(reds)]
  result={'task_id':m.TASK_ID,'generator_sha256':hashlib.sha256((REPO/'generators/4cccb4dba000/generator.py').read_bytes()).hexdigest(),'generator_version':m.VERSION,'generation':entry,'input':g,'components':cs,'rival_description':'Among equal maximum-red components, choose the last in row-major order instead of the first. Both satisfy the stated most-red criterion.','rival_output':winners[-1]['output'],'documented_domain':False,'domain_reason':'Generated using declared helpful axes within every numeric range, but violates STRICTLY unique max red-count invariant.','candidate_axes_in_documented_domain':True,'self_check_result':m.self_check(g),'probes':probes}
  out=ROOT/'checks/audit/4cccb4dba000'
  (out/'input.json').write_text(json.dumps(g)+'\n')
  (out/'evidence.json').write_text(json.dumps(result,indent=2)+'\n')
  print(json.dumps(entry));print('generator_sha256',result['generator_sha256']);break
else: raise RuntimeError('No witness in 8 focused samples')
