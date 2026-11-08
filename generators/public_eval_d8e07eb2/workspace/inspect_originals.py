"""Execute every supplied original pair and build a private visual discrepancy report.

Copy this task-local helper to another public-creation home if useful. It uses
only that explicit checkout, never changes data, and continues after a mismatch
or execution error so later train labels and test gold are still inspected.
It is a diagnostic; it cannot produce a passing authoring preflight receipt.
"""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import argparse
import hashlib
import html
import json
import re
import sys

COLORS=('#000000','#0074d9','#ff4136','#2ecc40','#ffdc00',
        '#aaaaaa','#f012be','#ff851b','#7fdbff','#870c25')
SCHEMA='arcpuzzles-original-pair-visual-diagnostic-v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def typed_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or
        any(type(row) is not list for row in grid) or not 1 <= len(grid[0]) <= 30 or
        any(len(row)!=len(grid[0]) for row in grid) or
        any(type(x) is not int or not 0 <= x <= 9 for row in grid for x in row)):
        raise ValueError('Execution must return a strict rectangular ARC grid')
    return deepcopy(grid)


def original_grid(value):
    """Support the source dataset's digit-row encoding without coercing cells."""
    if type(value) is not list:
        raise ValueError('Original grid must be a list of rows')
    rows=[]
    for row in value:
        if type(row) is str:
            if re.fullmatch('[0-9]{1,30}',row) is None:
                raise ValueError('Encoded original rows must contain only color digits')
            rows.append([ord(c)-ord('0') for c in row])
        else:
            rows.append(row)
    return typed_grid(rows)


def cell_differences(predicted,supplied):
    diffs=[]
    for r in range(max(len(predicted),len(supplied))):
        a=predicted[r] if r<len(predicted) else []
        b=supplied[r] if r<len(supplied) else []
        for c in range(max(len(a),len(b))):
            x=a[c] if c<len(a) else None
            y=b[c] if c<len(b) else None
            if x!=y:diffs.append({'row':r,'col':c,'predicted':x,'supplied':y})
    return diffs


def compare_pairs(pairs,program,apply):
    cases=[]
    for pair in pairs:
        original=typed_grid(pair['input']); supplied=typed_grid(pair['output'])
        case={'split':pair['split'],'index':pair['index'],'input':original,'supplied':supplied}
        try:
            sent=deepcopy(original)
            predicted=typed_grid(apply(program,sent))
            if sent!=original:raise ValueError('Evaluator mutated the supplied input')
            diffs=cell_differences(predicted,supplied)
            for diff in diffs:
                r,c=diff['row'],diff['col']
                diff['input']=original[r][c] if r<len(original) and c<len(original[r]) else None
            case.update(status='mismatch' if diffs else 'matched',predicted=predicted,differences=diffs)
            if diffs:
                case['difference_bounds']={'top':min(d['row'] for d in diffs),
                    'bottom':max(d['row'] for d in diffs),'left':min(d['col'] for d in diffs),
                    'right':max(d['col'] for d in diffs)}
        except Exception as error:
            case.update(status='execution_error',error=type(error).__name__+': '+str(error))
        cases.append(case)
    return cases


def grid_svg(grid,changed=()):
    grid=typed_grid(grid); changed=set(changed);size=12
    width,height=len(grid[0])*size,len(grid)*size
    cells=[]
    for r,row in enumerate(grid):
        for c,value in enumerate(row):
            marker=' class="changed"' if (r,c) in changed else ''
            cells.append(f'<rect{marker} x="{c*size}" y="{r*size}" width="{size}" height="{size}" fill="{COLORS[value]}"><title>row {r}, column {c}, color {value}</title></rect>')
    return f'<svg role="img" aria-label="{len(grid)} by {len(grid[0])} grid" viewBox="0 0 {width} {height}" width="{width}" height="{height}">'+''.join(cells)+'</svg>'


def render_report(report):
    esc=lambda x:html.escape(str(x),quote=True)
    summary=[];details=[]
    for case in report['cases']:
        name=f"{case['split']}[{case['index']}]"
        diffs=case.get('differences',[])
        summary.append('<tr><td>'+esc(name)+'</td><td>'+esc(case['status'])+'</td><td>'+str(len(diffs))+'</td></tr>')
        if case['status']=='matched':continue
        changed={(d['row'],d['col']) for d in diffs}
        figures=[]
        for label,key in [('Input','input'),('Program prediction','predicted'),('Supplied label','supplied')]:
            if key in case:
                figures.append('<figure><figcaption>'+label+'</figcaption>'+grid_svg(case[key],changed if key!='input' else ())+'</figure>')
        cells=''.join('<tr>'+''.join('<td>'+esc(d.get(key))+'</td>' for key in ('row','col','input','predicted','supplied'))+'</tr>' for d in diffs)
        error='<p class="error">'+esc(case['error'])+'</p>' if 'error' in case else ''
        details.append('<section><h2>'+esc(name)+'</h2>'+error+'<div class="grids">'+''.join(figures)+'</div>'+
            ('<p>Pink outlines mark the exact disagreement. Coordinates are zero-based; hover over any cell for its position and color.</p><table><thead><tr><th>Row</th><th>Column</th><th>Input</th><th>Prediction</th><th>Supplied</th></tr></thead><tbody>'+cells+'</tbody></table>' if diffs else '')+'</section>')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Original-pair diagnostic</title><style>
body{font:16px/1.5 system-ui,sans-serif;color:#192638;background:#f5f7fa;margin:0;padding:32px;max-width:1200px}h1{font-size:28px;margin:0 0 8px}h2{font-size:22px}p{max-width:1000px}.label{font-size:13px;letter-spacing:.08em;color:#675c48;font-weight:700}section{background:white;border:1px solid #d8e0ea;padding:24px;margin:24px 0;border-radius:12px}.grids{display:flex;gap:28px;flex-wrap:wrap}figure{margin:0}figcaption{font-weight:650;margin-bottom:12px}svg{max-width:100%;height:auto;background:#fff}rect{stroke:#5e6977;stroke-width:.35}rect.changed{stroke:#d500a6;stroke-width:2.4}table{border-collapse:collapse;background:white;margin:16px 0;font-size:14px}th,td{text-align:left;border:1px solid #d8e0ea;padding:8px 14px}th{background:#e8edf3}.error{color:#9a2633}footer{margin-top:28px;font-size:14px;color:#536278}
</style><body><div class="label">AUTHOR-PRIVATE · DIAGNOSTIC ONLY</div><h1>'''+esc(report['task_id'])+''' — supplied-label comparison</h1><p><strong>'''+esc(report['status'])+'</strong> · '+str(report['matched'])+' of '+str(report['labeled'])+' supplied labels matched. Unlabelled queries: '+str(report['unlabelled_queries'])+'.</p><p>This report executes every supplied label, even after a failure. A mismatch establishes disagreement with this program; it does not establish that the supplied label is wrong.</p><table><thead><tr><th>Pair</th><th>Result</th><th>Changed cells</th></tr></thead><tbody>'+''.join(summary)+'</tbody></table>'+''.join(details)+'<footer>'+esc(report['limits'])+'</footer></body></html>\n'


def source_binding(root,home):
    paths={p for p in home.rglob('*') if p.is_file() and '__pycache__' not in p.parts and
        (p.suffix in ('.py','.rkt') or p.name in ('promotion.json','public-parent.json'))}
    paths.update(p for p in (root/'shared/runtime').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.rkt'))
    paths.add(root/'shared/tools/comment_solutions.py')
    for path in paths:
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Source must be a regular file inside the explicit checkout')
    return {'task_id':home.name,'files':[{'path':p.relative_to(root).as_posix(),'sha256':sha(p)} for p in sorted(paths)]}


def inspect(root,task,program_path,out):
    root=Path(root).resolve();out=Path(out).absolute()
    if out.exists():raise FileExistsError('Choose a fresh diagnostic destination')
    if any(p.is_symlink() for p in (out,*out.parents)):raise ValueError('No symlink output paths')
    if not re.fullmatch('public_eval_[0-9a-f]{8}',task):raise ValueError('Expected a public creation task ID')
    home=root/'generators'/task;program_path=home/program_path
    if program_path.is_symlink() or not program_path.resolve().is_relative_to(home):
        raise ValueError('Program must be a same-task regular source file')
    sys.path.insert(0,str(root/'src'));sys.path.insert(0,str(root/'shared/runtime'))
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator
    from arcpuzzles.review_programs import strict_programs
    from arcpuzzles.review_public_creation import digest,SOURCE,SOLUTIONS
    from arcpuzzles.parametric_priority import _challenge
    target=json.loads((home/'workspace/public-parent.json').read_text())
    pid=target['public_task_id']
    if target['task_id']!=task or task!='public_eval_'+pid:raise ValueError('Parent identity mismatch')
    parent=json.loads((root/SOURCE).read_text())[pid]
    gold=json.loads((root/SOLUTIONS).read_text()).get(pid)
    if (digest(parent)!=target['source_record_sha256'] or
        digest(_challenge(parent))!=target['challenge_sha256'] or
        (digest(gold) if gold is not None else None)!=target['test_outputs_sha256']):
        raise ValueError('Frozen parent or supplied test gold identity changed')
    if gold is not None and len(gold)!=len(parent.get('test',[])):raise ValueError('Gold count mismatch')
    pairs=[];masked=0
    for split in ('train','test'):
        for index,pair in enumerate(parent.get(split,[])):
            output=pair.get('output')
            if split=='test' and gold is not None:
                if output is not None and output!=gold[index]:raise ValueError('Conflicting test gold')
                output=gold[index]
            if output is None:
                masked+=1;continue
            pairs.append({'split':split,'index':index,'input':original_grid(pair['input']),'output':original_grid(output)})
    if not pairs:raise ValueError('No supplied labeled pairs')
    binding=source_binding(root,home)
    data_hashes={name:sha(root/name) for name in (SOURCE,SOLUTIONS)}
    program=program_path.read_text()
    syntax=strict_programs(root,[program])
    with _local_imports(root/'shared/runtime',home/'workspace/parametric'):
        apply,identity,bridge=_real_evaluator(root/'shared/runtime')
        try:
            if identity.get('backend')!='racket' or identity.get('protected') is not True:
                raise ValueError('Protected Racket is required')
            cases=compare_pairs(pairs,program,apply)
        finally:
            bridge.close()
    if binding!=source_binding(root,home) or data_hashes!={name:sha(root/name) for name in data_hashes}:
        raise ValueError('Source or original data changed during diagnostic')
    counts=Counter(case['status'] for case in cases)
    status='blocked_original_execution' if counts['execution_error'] else ('blocked_original_labels' if counts['mismatch'] else 'all_supplied_labels_matched')
    report={'schema':SCHEMA,'task_id':task,'status':status,'source_binding':binding,
        'program_path':program_path.relative_to(root).as_posix(),'program':program,
        'program_sha256':hashlib.sha256(program.encode()).hexdigest(),'program_syntax':syntax,
        'original_files_sha256':data_hashes,'racket':identity,'labeled':len(cases),
        'matched':counts['matched'],'mismatches':counts['mismatch'],'execution_errors':counts['execution_error'],
        'unlabelled_queries':masked,'cases':cases,'owner_accepted':False,'training_admitted':False,
        'limits':'All supplied pairs were attempted through protected Racket. Source-bound diagnostic only; no authoring preflight, native qualification, owner acceptance, annotation correction, or training admission.'}
    view=render_report(report).encode()
    report['visual_report_sha256']=hashlib.sha256(view).hexdigest()
    out.mkdir(parents=True)
    (out/'comparison.html').write_bytes(view)
    (out/'comparison.json').write_text(json.dumps(report,sort_keys=True,separators=(',',':'))+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('.'))
    parser.add_argument('--task',default=Path(__file__).resolve().parents[1].name)
    parser.add_argument('--program',type=Path,default=Path('reference.rkt'))
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();report=inspect(args.root,args.task,args.program,args.out)
    print(json.dumps({k:report[k] for k in ('status','labeled','matched','mismatches','execution_errors','unlabelled_queries')}))
    raise SystemExit(0 if report['status']=='all_supplied_labels_matched' else 2)
