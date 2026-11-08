from contextlib import redirect_stdout,redirect_stderr
from pathlib import Path,PurePosixPath
import hashlib,io,json,os,stat,sys,zipfile

cold=Path(__file__).resolve().parent;repo=cold/'checkout/WORK/repo'
sys.path[:0]=[str(repo/'src'),str(repo/'shared/runtime')]
from arcpuzzles.cli import main
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
bundle=repo/'generators/7b0cb3b9a618/evidence/owner-parametric-promotion/ACCEPTED-CROSSING-BANDS-STANDARD.zip'
assert sha(bundle)=='e21b3f316f0d306684a47de0ba5a9032faa3ecac167d1f5fc01462fb5ca9c35d'
data=cold/'profile-export';data.mkdir()
with zipfile.ZipFile(bundle) as z:
    for info in z.infolist():
        name=PurePosixPath(info.filename)
        assert not name.is_absolute() and '..' not in name.parts and not stat.S_ISLNK(info.external_attr>>16)
    z.extractall(data)
before={p.relative_to(data).as_posix():sha(p) for p in data.rglob('*') if p.is_file()}
fake=cold/'profile-fake-runtime';fake.mkdir();racket=fake/'racket';marker=fake/'invoked'
racket.write_text('#!'+sys.executable+'\nfrom pathlib import Path\nPath('+repr(str(marker))+').write_text("called")\nraise SystemExit(97)\n');racket.chmod(0o755)
os.environ['RACKET_PATH']=str(racket);os.environ['PATH']=str(fake)+os.pathsep+os.environ['PATH']
results=[]
def run(name,options):
    args=['--library',str(repo),'inspect-export',str(data),*options];out,err=io.StringIO(),io.StringIO()
    with redirect_stdout(out),redirect_stderr(err):code=main(args)
    results.append({'name':name,'argv':args,'exit_code':code,
                    'stdout_sha256':hashlib.sha256(out.getvalue().encode()).hexdigest(),
                    'stderr_sha256':hashlib.sha256(err.getvalue().encode()).hexdigest()})
    return code,out.getvalue(),err.getvalue()
code,raw,_=run('default',[]);assert code==0;manifest=json.loads(raw);assert manifest['schema']=='arcpuzzles-dataset-v1'
code,raw,_=run('sizes',['--sizes']);assert code==0;profile=json.loads(raw)
assert profile['visibility']=='controller_only' and profile['dataset_id']==manifest['dataset_id']
assert profile['observed_episodes']==8 and profile['supervision']['query_pairs']==32
assert profile['supervision']['episodes_with_four_distinct_novel_queries']['count']==8
assert profile['grids']['query_outputs']['longest_side_at_least_20']['count']==0
code,raw,_=run('detailed',['--sizes','--detailed-shapes']);assert code==0;detailed=json.loads(raw)
assert detailed['grids']['query_outputs']['shapes']=={'1x1':32}
code,_,err=run('missing-sizes',['--detailed-shapes']);assert code==1 and 'requires --sizes' in err
assert before=={p.relative_to(data).as_posix():sha(p) for p in data.rglob('*') if p.is_file()}
assert not marker.exists()
result={'schema':'arcpuzzles-export-size-profile-cold-v1','status':'passed','dataset_id':profile['dataset_id'],
        'source_files':{name:sha(repo/name) for name in ['src/arcpuzzles/dataset_profile.py','src/arcpuzzles/cli.py']},
        'bundle_sha256':sha(bundle),'episodes':8,'queries':32,'four_distinct_novel_query_episodes':8,
        'query_output_shapes':detailed['grids']['query_outputs']['shapes'],'selected_fake_racket_invoked':False,
        'artifact_hashes_unchanged':True,'commands':results,
        'scope':'Native CLI in a fresh packet with owner/predecessor reads denied. Static artifact observations only; no generation/Racket rerun, mixture or training admission change.'}
(cold/'profile-probe-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['commands','source_files']},indent=2,sort_keys=True))
