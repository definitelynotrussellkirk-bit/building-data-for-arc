"""Offline venv construction from already installed pure-Python distributions."""
import base64,csv,hashlib,importlib.metadata as metadata,io,json,os,subprocess,sys,zipfile
from pathlib import Path
work=Path(sys.argv[1]).resolve()
venv=work/'.venv-review'; wheel_dir=work/'.review/offline-test-wheels';wheel_dir.mkdir(parents=True,exist_ok=True)
receipt=[]
for name in ('pytest','iniconfig','pluggy','pygments'):
 dist=metadata.distribution(name); files={}
 for file in dist.files:
  relative=Path(str(file))
  if relative.is_absolute() or '..' in relative.parts or '__pycache__' in relative.parts or relative.suffix=='.pyc' or relative.name=='RECORD':continue
  source=dist.locate_file(file)
  if source.is_file():files[relative.as_posix()]=source.read_bytes()
 wheel_metadata=[n for n in files if n.endswith('.dist-info/WHEEL')]
 if len(wheel_metadata)!=1 or b'Root-Is-Purelib: true' not in files[wheel_metadata[0]]:raise RuntimeError(f'{name}: expected pure Python distribution')
 record_name=wheel_metadata[0].replace('/WHEEL','/RECORD');stream=io.StringIO();writer=csv.writer(stream,lineterminator='\n')
 for path,body in sorted(files.items()):writer.writerow([path,'sha256='+base64.urlsafe_b64encode(hashlib.sha256(body).digest()).decode().rstrip('='),len(body)])
 writer.writerow([record_name,'','']);files[record_name]=stream.getvalue().encode()
 wheel=wheel_dir/f'{name}-{dist.version}-py3-none-any.whl'
 with zipfile.ZipFile(wheel,'w',zipfile.ZIP_DEFLATED) as archive:
  for path,body in sorted(files.items()):archive.writestr(path,body)
 receipt.append({'name':name,'version':dist.version,'local_installed_source':str(dist.locate_file('')),'wheel':str(wheel),'wheel_sha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'files':len(files)})
subprocess.run([sys.executable,'-m','venv','--system-site-packages',str(venv)],check=True)
argv=[str(venv/'bin/python'),'-m','pip','install','--no-index','--no-deps','--force-reinstall',*[r['wheel'] for r in receipt]]
subprocess.run(argv,check=True,env={**os.environ,"PYTHONNOUSERSITE":"1"})
(work/'checks/environment/offline-test-wheels.json').write_text(json.dumps({'python':sys.executable,'venv':str(venv),'install_argv':argv,'distributions':receipt},indent=2)+'\n')
print(json.dumps({'venv_python':str(venv/'bin/python'),'distributions':receipt}))
