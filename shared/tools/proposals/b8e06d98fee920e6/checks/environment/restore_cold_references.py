"""Restore only hash-verified cold references from the unchanged source packet."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    work=a.work.resolve()
    d=json.loads(a.manifest.read_text())
    source=Path(d['source_zip'])
    h=hashlib.sha256()
    with source.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    assert h.hexdigest()==d['source_zip_sha256'],'Original ZIP identity changed'
    restored=already=total=0
    with zipfile.ZipFile(source) as z:
        for row in d['rows']:
            p=work/row['path']
            assert p.resolve().is_relative_to(work)
            data=z.read(row['zip_member'])
            assert len(data)==row['bytes'] and sha(data)==row['sha256'],row['path']
            if p.exists():
                assert p.is_file() and not p.is_symlink()
                assert sha(p.read_bytes())==row['sha256'],f'Unexpected existing bytes: {p}'
                already+=1
            else:
                p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('xb') as f:f.write(data)
                assert sha(p.read_bytes())==row['sha256'],row['path']
                restored+=1
            row['restored']=True
            total+=row['bytes']
    d['restored']=all(row['restored'] for row in d['rows'])
    a.manifest.write_text(json.dumps(d,indent=2)+'\n')
    report={'status':'restored_and_verified','source_zip_sha256':h.hexdigest(),
            'rows':len(d['rows']),'restored_this_run':restored,'already_exact':already,
            'raw_bytes_verified':total,'manifest_sha256':sha(a.manifest.read_bytes()),
            'all_original_reference_bytes_restored':d['restored'],
            'script_sha256':sha(Path(__file__).read_bytes()),
            'argv':[sys.executable,*sys.argv], 'cwd':str(Path.cwd())}
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,sort_keys=True))

if __name__=='__main__':main()
