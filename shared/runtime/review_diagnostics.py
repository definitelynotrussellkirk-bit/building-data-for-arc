"""Finite, advisory reviewer diagnostics; never semantic certification.

Generic rivals mutate measured Racket-labelled pairs. They are bounded
hypotheses on that support, not independent solvers or labels for new inputs.
SEARCHED_RIVAL_PROVIDER() supplies independent (name, transform) candidates;
it is separate from the generator's declared compact rival dictionaries.
"""
from collections import Counter
from copy import deepcopy
import json
import importlib.util
from pathlib import Path
import sys
from reviewer_support import normalize_grid


def _key(grid):
    return json.dumps(grid,separators=(',',':'))


def objects(grid):
    remaining={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v}
    result=[]
    while remaining:
        start=min(remaining);color=grid[start[0]][start[1]]
        cells={start};todo=[start];remaining.remove(start)
        while todo:
            r,c=todo.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in remaining and grid[p[0]][p[1]]==color:
                    remaining.remove(p);cells.add(p);todo.append(p)
        result.append((color,sorted(cells)))
    return result


def structural_signature(pair):
    inp,out=normalize_grid(pair['input']),normalize_grid(pair['output'])
    before={v for row in inp for v in row if v};after={v for row in out for v in row if v}
    same=len(inp)==len(out) and len(inp[0])==len(out[0])
    markers=[(r,c,color) for color,cells in objects(inp) if len(cells)==1 for r,c in cells]
    return {'object_count':len(objects(inp)), 'shape_preserving':same,
            'palette_roles':{'preserved':len(before&after),'introduced':len(after-before),'removed':len(before-after)},
            'marker_count':len(markers),
            'persistent_markers':sum(r<len(out) and c<len(out[0]) and out[r][c]==v for r,c,v in markers)}


def compare_structure(canonical,generated):
    canonical=[p if isinstance(p,dict) else {'input':p[0],'output':p[1]} for p in canonical]
    canonical=[p for p in canonical if p.get('output') is not None]
    generated=[p for p in generated if p.get('output') is not None]
    cs=[structural_signature(p) for p in canonical];gs=[structural_signature(p) for p in generated]
    features=('object_count','shape_preserving','palette_roles','marker_count','persistent_markers')
    support=lambda rows,k:{json.dumps(r[k],sort_keys=True) for r in rows}
    disjoint=[k for k in features if cs and gs and support(cs,k).isdisjoint(support(gs,k))]
    return {'status':'advisory_mismatch' if disjoint else 'no_mismatch_found' if cs and gs else 'insufficient_support',
            'scope':'Coarse signatures on measured support; mismatch is a review lead, agreement is not semantic proof.',
            'disjoint_features':disjoint,'canonical_signatures':cs,'generated_signatures':gs,
            'witness':deepcopy(generated[0]) if disjoint else None}


def _scalar_axis_domains(axes):
    """Reuse the override checker's parser from this source or staged runtime."""
    here = Path(__file__).resolve().parent
    candidates = (here / 'scripts/check_generator_override_contract.py',
                  here.parent / 'tools/check_generator_override_contract.py')
    path = next((p for p in candidates if p.is_file()), None)
    if path is None:
        raise FileNotFoundError('Scalar probes require the local override-domain checker')
    spec = importlib.util.spec_from_file_location('_review_scalar_domains', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.axis_domain_report(axes)


def scalar_override_probes(gen):
    """Bounded request-contract checks, calibrated by accepted control calls.

    Common call arguments and exact integer/color overrides are separate. Use
    the existing domain parser's surviving endpoints, in each standard band.
    Rejected controls are unknown coverage, never evidence of scalar rejection.
    Nothing here scores a label or certifies the generator's semantic domain.
    """
    findings = []
    axes = getattr(gen, 'AXES', {})
    exact_axes = {name: spec for name, spec in axes.items()
                  if name not in {'seed', 'sample_index', 'difficulty'}
                  and isinstance(spec, dict) and spec.get('type') in ('int', 'color')}
    domains = _scalar_axis_domains(axes) if exact_axes else []

    def call(axis, value, band):
        return gen.generate(value if axis == 'seed' else 991,
                            value if axis == 'sample_index' else 0,
                            difficulty=value if axis == 'difficulty' else band,
                            **({axis: value} if axis in exact_axes else {}))

    def probe(axis, values, band, control, kind):
        seen = set()
        for value in values:
            identity = type(value).__name__, repr(value)
            if identity in seen:
                continue
            seen.add(identity)
            record = {'axis': axis, 'value': value, 'value_type': identity[0],
                      'probe_kind': kind, 'difficulty': band, 'control_value': control}
            try:
                call(axis, value, band)
            except (ValueError, TypeError):
                continue
            except Exception as exc:
                findings.append({**record, 'status': 'unexpected_exception',
                                 'error': f'{type(exc).__name__}: {exc}'})
            else:
                findings.append({**record, 'status': 'accepted_invalid_scalar'})

    for band in ('easy', None, 'hard'):
        try:
            call(None, None, band)
        except Exception as exc:
            findings.append({'axis': 'call_arguments', 'probe_kind': 'call_argument',
                'difficulty': band, 'status': 'no_accepted_control',
                'error': f'{type(exc).__name__}: {exc}'})
            continue
        probe('seed', (True, False, 1.0, 1.75, '1'), band, 991, 'call_argument')
        probe('sample_index', (True, False, 1.0, 1.75, '1', -1), band, 0, 'call_argument')
        probe('difficulty', (True, False, 0, 1.0, '__invalid_difficulty__'), band, band, 'call_argument')
        for domain in domains:
            if domain.name not in exact_axes or domain.status == 'diagnostic':
                continue
            candidates = sorted(v for v in domain.values if type(v) is int)
            if not candidates:
                findings.append({'axis': domain.name, 'probe_kind': 'declared_override',
                    'difficulty': band, 'status': 'integer_domain_unavailable',
                    'error': domain.reason})
                continue
            controls = sorted({candidates[0], candidates[-1]})
            accepted = False
            control_errors = []
            for control in controls:
                try:
                    call(domain.name, control, band)
                except Exception as exc:
                    control_errors.append({'value': control, 'error': f'{type(exc).__name__}: {exc}'})
                    continue
                accepted = True
                values = [True, False, str(control)]
                try:
                    values.extend((float(control), control + 0.75))
                except OverflowError:
                    # No representable finite floating probe at this endpoint.
                    pass
                if not candidates[0] <= -1 <= candidates[-1]:
                    values.append(-1)
                probe(domain.name, values, band, control, 'declared_override')
            if not accepted:
                findings.append({'axis': domain.name, 'probe_kind': 'declared_override',
                    'difficulty': band, 'status': 'no_accepted_control',
                    'control_errors': control_errors})
    return findings


def schedule_metadata(gen,reporting_modulus,enumerate_schedule):
    declared=getattr(gen,'LESSON_SCHEDULE_PERIOD',None)
    warnings=[]
    if declared is not None and (type(declared) is not int or declared<1): warnings.append('Invalid declared schedule period')
    elif declared and declared<=64 and not enumerate_schedule: warnings.append('Declared short schedule was not explicitly enumerated')
    return {'declared_schedule_period':declared,'reporting_residue_modulus':reporting_modulus,
            'enumerated_schedule_period':declared if enumerate_schedule else None,'warnings':warnings}


def _generic_candidates(pairs):
    lookup={_key(p['input']):p['output'] for p in pairs}
    def mutate(grid,mode):
        out=deepcopy(lookup[_key(grid)])
        if mode=='no_fill': return deepcopy(grid)
        if len(out)!=len(grid) or len(out[0])!=len(grid[0]):
            raise ValueError('same-size construction mutation not applicable')
        colors=sorted({v for row in grid for v in row if v})
        if not colors: return out
        components=objects(grid)
        if mode=='first_color_only': selected={colors[0]}
        elif mode=='last_color_only': selected={colors[-1]}
        elif mode in ('first_object_only','topmost_object_only','reverse_position_tie'):
            # A bounded spatial attribution hypothesis: each changed cell is
            # attributed to its nearest input component (Manhattan distance).
            # Same-color components remain distinct. Reverse tie chooses the
            # last tied component; this is not a universal rule decomposition.
            winner=0
            for r,row in enumerate(out):
                for c,v in enumerate(row):
                    if v==grid[r][c]: continue
                    distances=[min(abs(r-rr)+abs(c-cc) for rr,cc in cells) for _,cells in components]
                    tied=[i for i,n in enumerate(distances) if n==min(distances)]
                    owner=tied[-1] if mode=='reverse_position_tie' else tied[0]
                    if owner!=winner: out[r][c]=grid[r][c]
            return out
        elif mode=='omit_last_changed_cell':
            changed=[(r,c) for r,row in enumerate(out) for c,v in enumerate(row) if v!=grid[r][c]]
            if changed: r,c=changed[-1];out[r][c]=grid[r][c]
            return out
        else: raise ValueError(mode)
        for r,row in enumerate(out):
            for c,v in enumerate(row):
                if v!=grid[r][c] and v not in selected: out[r][c]=grid[r][c]
        return out
    modes=('first_color_only','last_color_only','first_object_only','topmost_object_only','reverse_position_tie','no_fill','omit_last_changed_cell')
    return {'generic:'+mode:lambda g,m=mode:mutate(g,m) for mode in modes}


def _minimize_demo_witness(lesson):
    # Remove duplicate evidence only, keeping every distinct teaching fact.
    # Arbitrarily deleting all agreeing demos would manufacture a weaker lesson.
    seen=set();train=[]
    for pair in lesson['train']:
        key=json.dumps(pair,sort_keys=True)
        if key not in seen: seen.add(key);train.append(deepcopy(pair))
    return {'train':train,'test':deepcopy(lesson['test']),
            'minimization':'duplicate demonstrations removed; unique evidence preserved'}


def search_lesson(gen,lesson,*,max_candidates=128):
    if type(max_candidates) is not int or not 1<=max_candidates<=1024: raise ValueError('max_candidates must be 1..1024')
    candidates=_generic_candidates(lesson['train']+lesson['test'])
    provider=getattr(gen,'SEARCHED_RIVAL_PROVIDER',None)
    report={'candidates':{},'provider_status':'not_declared','errors':[],
            'scope':'Bounded measured support; generic label mutations and independent provider candidates are reported separately.',
            'candidate_limit':max_candidates,'truncated':len(candidates)>max_candidates}
    if provider is not None:
        try:
            if not callable(provider): raise TypeError('SEARCHED_RIVAL_PROVIDER must be callable')
            for i,item in enumerate(provider()):
                if len(candidates)>=max_candidates: report['truncated']=True;break
                name,fn=item
                if not isinstance(name,str) or not name or not callable(fn): raise TypeError('provider must yield (name, transform)')
                if 'provider:'+name in candidates: raise ValueError('duplicate provider name: '+name)
                candidates['provider:'+name]=fn
            report['provider_status']='loaded'
        except Exception as exc:
            report['provider_status']='error';report['errors'].append(f'{type(exc).__name__}: {exc}')
    for name,fn in list(candidates.items())[:max_candidates]:
        try:
            train=[normalize_grid(fn(deepcopy(p['input'])))==p['output'] for p in lesson['train']]
            query=[normalize_grid(fn(deepcopy(p['input'])))==p['output'] for p in lesson['test']]
            status='refuted' if not all(train) else 'support_equivalent' if all(query) else 'ambiguous'
            report['candidates'][name]={'status':status,'origin':'independent_provider' if name.startswith('provider:') else 'measured_label_mutation',
                                       'support_disagreements':len(train)+len(query)-sum(train)-sum(query)}
            if status=='ambiguous': report['candidates'][name]['witness']=_minimize_demo_witness(lesson)
        except ValueError as exc:
            report['candidates'][name]={'status':'not_applicable' if name.startswith('generic:') else 'error','error':str(exc)}
        except Exception as exc:
            report['candidates'][name]={'status':'error','error':f'{type(exc).__name__}: {exc}'}
    report['ambiguous']=any(v['status']=='ambiguous' for v in report['candidates'].values())
    return report


def summarize_searches(reports):
    """Aggregate across measured lessons without calling zero disagreements refuted."""
    rows={}
    for report in reports:
        for name,value in report["candidates"].items():
            row=rows.setdefault(name,{"outcomes":{},"support_disagreements":0})
            status=value["status"]
            row["outcomes"][status]=row["outcomes"].get(status,0)+1
            row["support_disagreements"]+=value.get("support_disagreements",0)
    for row in rows.values():
        outcomes=row["outcomes"]
        row["status"]=("error" if "error" in outcomes else "ambiguous" if "ambiguous" in outcomes else
                       "refuted" if row["support_disagreements"] else "support_equivalent" if "support_equivalent" in outcomes else "not_applicable")
    return rows
