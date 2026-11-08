"""Reversibly evict only manifest-authenticated, unselected generator references.

Journal is fsynced before any unlink. Restore never overwrites existing paths.
Only original immutable references may share restored inodes; selected tasks,
contracts, baseline data, helpers, runtime APIs, symlinks and mounts are excluded
from deduplication. No directories or original archive bytes are removed.
"""
from __future__ import annotations
import argparse, collections, datetime, gc, gzip, hashlib, json, os, re, stat, sys, zipfile
from pathlib import Path, PurePosixPath

PROTECTED={'2692a3e47a66','8a34b3906f3a','4056ed281704','db4cb6bcf6fe'}
HEX=re.compile(r'[0-9a-f]{12}')
CHUNK=131072

def digest_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(CHUNK),b''): h.update(b)
    return h.hexdigest()

def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def encode(o): return (json.dumps(o,separators=(',',':'),sort_keys=True)+'\n').encode()
def scope(key):
    p=PurePosixPath(key); s=p.parts
    return not p.is_absolute() and '..' not in s and len(s)>=4 and s[:2]==('repo','generators') and bool(HEX.fullmatch(s[2])) and s[2] not in PROTECTED

def immutable(key):
    parts=PurePosixPath(key).parts
    if any('baseline' in s.lower() or 'contract' in s.lower() for s in parts): return False
    if any(x in parts for x in PROTECTED): return False
    return scope(key) or (len(parts)>4 and parts[:4]==('repo','shared','tools','proposals'))

def mount_paths(work):
    result=[]
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        raw=line.split()[4]
        p=Path(re.sub(r'\\([0-7]{3})',lambda m:chr(int(m[1],8)),raw))
        if p!=work and p.is_relative_to(work): result.append(p)
    return result

def safe(work,key,mounts,missing=False):
    p=work/key
    if any(p==m or m in p.parents for m in mounts): return None,'mount'
    for parent in reversed(p.parents):
        if parent==work or parent.is_relative_to(work):
            try: s=parent.lstat()
            except FileNotFoundError: return None,'missing_parent'
            if not stat.S_ISDIR(s.st_mode) or stat.S_ISLNK(s.st_mode): return None,'unsafe_parent'
    try: s=p.lstat()
    except FileNotFoundError: return (p,None) if missing else (None,'missing')
    if stat.S_ISLNK(s.st_mode): return None,'symlink'
    if not stat.S_ISREG(s.st_mode): return None,'nonregular'
    if s.st_dev!=work.stat().st_dev: return None,'different_filesystem'
    return p,None

def open_verified(path,expected):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        s=os.fstat(fd); h=hashlib.sha256()
        if not stat.S_ISREG(s.st_mode): raise ValueError('Not a regular file')
        for b in iter(lambda:os.read(fd,CHUNK),b''): h.update(b)
        t=os.fstat(fd)
        if (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,stat.S_IMODE(s.st_mode))!=(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,stat.S_IMODE(t.st_mode)) or h.hexdigest()!=expected:
            raise ValueError('File changed or manifest SHA mismatch: '+str(path))
        return fd,t
    except BaseException:
        os.close(fd); raise

def metrics(work):
    v=os.statvfs(work); d={'filesystem_available_bytes':v.f_bavail*v.f_frsize}
    for name in ('memory.current','memory.max'):
        p=Path('/sys/fs/cgroup')/name
        if p.exists(): d[name]=p.read_text().strip()
    return d

def save_json(path,obj):
    with path.open('x') as f:
        json.dump(obj,f,indent=2,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())

def rows(journal):
    with gzip.open(journal,'rt') as f:
        next(f)
        for line in f: yield json.loads(line)

def validate_row(row,manifest):
    if len(row)!=8 or not scope(row[0]) or manifest.get(row[0])!=row[1]: raise ValueError('Journal escaped original manifest scope')
    if any(not isinstance(x,int) or x<0 for x in row[2:]): raise ValueError('Invalid journal metadata')

def evict(a,work,manifest,journal,report):
    if journal.exists(): raise FileExistsError('Journal already exists; evict is deliberately one-shot')
    source=a.source_zip.resolve()
    if not a.source_zip_sha256 or digest_file(source)!=a.source_zip_sha256: raise ValueError('Original source ZIP identity mismatch')
    header={'schema':'arc-review-reference-cache-v1','work':str(work),'source_zip':str(source),'source_zip_sha256':a.source_zip_sha256,'packet_manifest_sha256':digest_file(work/'PACKET-MANIFEST.json'),'protected_task_ids':sorted(PROTECTED),'row_fields':['path','sha256','size','mode','device','inode','original_nlink','allocated_bytes'],'created_utc':utc()}
    temp=journal.with_name(journal.name+'.incomplete')
    mounts=mount_paths(work); counts=collections.Counter(); raw_hash=hashlib.sha256(); raw_bytes=0
    def emit(f,value):
        nonlocal raw_bytes
        b=encode(value); f.write(b); raw_hash.update(b); raw_bytes+=len(b)
    try:
        with temp.open('xb') as raw:
            with gzip.GzipFile(filename='',mode='wb',fileobj=raw,compresslevel=9,mtime=0) as gz:
                emit(gz,header)
                for key,expected in manifest.items():
                    if not scope(key): continue
                    counts['scope_manifest_paths']+=1
                    p,reason=safe(work,key,mounts)
                    if reason: counts['skipped_'+reason]+=1; continue
                    fd,s=open_verified(p,expected)
                    os.close(fd)
                    emit(gz,[key,expected,s.st_size,stat.S_IMODE(s.st_mode),s.st_dev,s.st_ino,s.st_nlink,s.st_blocks*512])
                    counts['journal_paths']+=1; counts['journal_logical_bytes']+=s.st_size
            raw.flush(); os.fsync(raw.fileno())
        os.link(temp,journal); temp.unlink()
        dfd=os.open(journal.parent,os.O_RDONLY|os.O_DIRECTORY)
        try: os.fsync(dfd)
        finally: os.close(dfd)
    except BaseException:
        if temp.exists(): temp.unlink()
        raise
    report['journal']={'path':str(journal.relative_to(work)),'compression':'gzip, level 9, deterministic mtime 0','compressed_bytes':journal.stat().st_size,'compressed_sha256':digest_file(journal),'uncompressed_bytes':raw_bytes,'uncompressed_sha256':raw_hash.hexdigest(),'durable_before_any_unlink':True}
    print(json.dumps({'phase':'journal_saved','paths':counts['journal_paths'],'compressed_bytes':journal.stat().st_size}),flush=True)
    report['identity']=header
    for row in rows(journal):
        validate_row(row,manifest)
        key,expected,size,mode,device,inode,nlink,allocated=row
        p,reason=safe(work,key,mounts)
        if reason: counts['unlink_skipped_'+reason]+=1; continue
        fd,s=open_verified(p,expected)
        try:
            t=p.lstat()
            if (t.st_dev,t.st_ino,t.st_size,stat.S_IMODE(t.st_mode))!=(device,inode,size,mode) or (s.st_dev,s.st_ino)!=(device,inode): raise ValueError('Identity changed before unlink: '+key)
            os.unlink(p)
            counts['unlinked_paths']+=1; counts['unlinked_logical_bytes']+=size
            if os.fstat(fd).st_nlink==0:
                counts['fully_unlinked_unique_inodes']+=1
                counts['fully_unlinked_unique_content_bytes']+=size
                counts['fully_unlinked_unique_allocated_bytes']+=s.st_blocks*512
        finally: os.close(fd)
    report['counts']=dict(counts)
    report['status']='reference_cache_evicted_restore_required'
    report['scope']='Original manifest files only under unprotected 12-hex generator task directories; no directories, mounts, symlinks, helpers, shared API paths or protected task paths removed.'
    report['unique_bytes_method']='Count size and allocated blocks once only when the verified open inode has zero hardlinks immediately after unlink, then close its descriptor. Filesystem/cgroup deltas are observational and can include concurrent activity.'
    report['restore_argv']=[sys.executable,'-B',str(Path(__file__).resolve()),'restore','--work',str(work),'--source-zip',str(source)]

def restore(a,work,manifest,journal,report):
    previous=json.loads((journal.parent/'replay-reference-cache-evict.json').read_text())
    if digest_file(journal)!=previous['journal']['compressed_sha256']: raise ValueError('Restore journal SHA mismatch')
    with gzip.open(journal,'rt') as f: header=json.loads(next(f))
    source=(a.source_zip or Path(header['source_zip'])).resolve()
    if digest_file(source)!=header['source_zip_sha256']: raise ValueError('Original ZIP identity changed')
    if digest_file(work/'PACKET-MANIFEST.json')!=header['packet_manifest_sha256']: raise ValueError('Original packet manifest changed')
    mounts=mount_paths(work); anchors={}; prior=set(); counts=collections.Counter()
    for row in rows(journal):
        validate_row(row,manifest)
        if row[6]>1 and immutable(row[0]): prior.add((row[1],row[2],row[3],row[4],row[5]))
    # Only surviving original immutable inodes may anchor pre-existing links.
    # A shared proposal is considered solely if its original inode is recorded.
    for key,expected in manifest.items():
        if not immutable(key): continue
        p,reason=safe(work,key,mounts)
        if reason: continue
        s=p.lstat(); identity=(expected,s.st_size,stat.S_IMODE(s.st_mode),s.st_dev,s.st_ino)
        if identity not in prior: continue
        fd,t=open_verified(p,expected); os.close(fd)
        anchors.setdefault(identity[:3],p)
    counts['surviving_verified_prior_anchors']=len(anchors)
    del prior; gc.collect()
    with zipfile.ZipFile(source) as z:
        h=hashlib.sha256()
        with z.open('WORK/PACKET-MANIFEST.json') as f:
            for b in iter(lambda:f.read(CHUNK),b''): h.update(b)
        if h.hexdigest()!=header['packet_manifest_sha256']: raise ValueError('ZIP manifest identity mismatch')
        for i,row in enumerate(rows(journal)):
            validate_row(row,manifest)
            key,expected,size,mode,device,inode,nlink,allocated=row
            p,reason=safe(work,key,mounts,missing=True)
            if reason: raise ValueError('Unsafe restore destination '+key+': '+reason)
            dedup=(expected,size,mode)
            if p.exists():
                fd,s=open_verified(p,expected); os.close(fd)
                if s.st_size!=size or stat.S_IMODE(s.st_mode)!=mode: raise ValueError('Existing file metadata differs: '+key)
                counts['already_exact']+=1
            elif immutable(key) and dedup in anchors:
                anchor=anchors[dedup]
                ap,reason=safe(work,str(anchor.relative_to(work)),mounts)
                if reason: raise ValueError('Unsafe dedup anchor')
                fd,s=open_verified(ap,expected)
                try:
                    if s.st_size!=size or stat.S_IMODE(s.st_mode)!=mode: raise ValueError('Dedup metadata differs')
                    os.link(ap,p,follow_symlinks=False)
                finally: os.close(fd)
                counts['restored_hardlinks']+=1; counts['deduplicated_logical_bytes']+=size
            else:
                member=z.getinfo('WORK/'+key)
                if member.file_size!=size or stat.S_ISLNK(member.external_attr>>16): raise ValueError('Invalid original ZIP member: '+key)
                temp=p.with_name('.replay-reference-restore-'+str(os.getpid())+'-'+str(i))
                try:
                    h=hashlib.sha256(); total=0
                    with temp.open('xb') as out,z.open(member) as src:
                        for b in iter(lambda:src.read(CHUNK),b''):
                            out.write(b); h.update(b); total+=len(b)
                        out.flush()
                        if total!=size or h.hexdigest()!=expected: raise ValueError('Original ZIP member SHA mismatch: '+key)
                        os.fchmod(out.fileno(),mode); os.fsync(out.fileno())
                    os.link(temp,p); temp.unlink()
                except BaseException:
                    if temp.exists(): temp.unlink()
                    raise
                counts['restored_unique_copies']+=1; counts['restored_unique_copy_bytes']+=size
            if immutable(key): anchors.setdefault(dedup,p)
            counts['verified_paths']+=1; counts['verified_logical_bytes']+=size
    report['status']='all_journal_paths_restored_exactly'
    report['counts']=dict(counts); report['journal_sha256']=digest_file(journal)
    report['source_zip_sha256']=header['source_zip_sha256']
    report['dedup_scope']='Only exact SHA/size/mode original immutable references; surviving prior inode anchors or already verified restored references. Selected/audit/blind tasks, contracts, baseline data, helpers, APIs and mounts excluded.'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode',choices=('evict','restore'))
    ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--source-zip',type=Path)
    ap.add_argument('--source-zip-sha256')
    a=ap.parse_args(); work=a.work.resolve(); evidence=work/'checks/environment'
    journal=evidence/'replay-reference-cache.jsonl.gz'
    receipt=evidence/('replay-reference-cache-'+a.mode+'.json')
    if receipt.exists(): raise FileExistsError('Receipt exists; refusing to overwrite evidence: '+str(receipt))
    report={'started_utc':utc(),'argv':sys.orig_argv,'cwd':str(Path.cwd()),'TMPDIR':os.environ.get('TMPDIR'),'script_sha256':digest_file(Path(__file__)),'mount_namespace':os.readlink('/proc/self/ns/mnt'),'before':metrics(work)}
    rc=0
    try:
        manifest=json.loads((work/'PACKET-MANIFEST.json').read_text())['files']
        if a.mode=='evict' and a.source_zip is None: raise ValueError('evict requires --source-zip')
        (evict if a.mode=='evict' else restore)(a,work,manifest,journal,report)
    except BaseException as e:
        rc=1; report['status']='failed'; report['error']=type(e).__name__+': '+str(e)
    report['returncode']=rc; report['finished_utc']=utc(); report['after']=metrics(work)
    save_json(receipt,report)
    print(json.dumps(report,sort_keys=True),flush=True)
    return rc

if __name__=='__main__': sys.exit(main())
