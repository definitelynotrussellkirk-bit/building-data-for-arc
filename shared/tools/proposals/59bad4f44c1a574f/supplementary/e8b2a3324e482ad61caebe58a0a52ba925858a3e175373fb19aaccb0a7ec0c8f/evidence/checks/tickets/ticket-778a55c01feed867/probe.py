"""One bounded source-level reproduction. Reads exact retained ZIP members only.
No full runtime/catalog or Racket claim: generic target executable/grid not retained.
"""
import ast
import hashlib
import json
import math
from pathlib import Path
import time
import zipfile

ROOT = Path('/workspace/scratch/44208dbd43c4')
ARCHIVE = ROOT / 'upload/SEND-THIS-ARCpuzzles-review(20261023-171140).zip'
REPORT = ROOT / 'ticket_tool_report.json'
REQUEST_ID = 'review-729df00f2eb5fe84:v0001:F4'
PREFIX = 'WORK/repo/'
started = time.monotonic()
sha = lambda raw: hashlib.sha256(raw).hexdigest()
with zipfile.ZipFile(ARCHIVE) as z:
    members = {}
    def read(path):
        raw = z.read(PREFIX + path)
        members[PREFIX + path] = {'bytes': len(raw), 'sha256': sha(raw)}
        return raw
    suggestions_raw = read('REVIEW/suggestions.json')
    request = next(row for row in json.loads(suggestions_raw)['items'] if row.get('request_id') == REQUEST_ID)
    canonical_request_hash = sha(json.dumps(request,sort_keys=True,separators=(',',':')).encode())
    manifest_raw = read('shared/tools/proposals/59bad4f44c1a574f/manifest.json')
    manifest = json.loads(manifest_raw)
    asset = manifest['files'][0]
    log_raw = read(asset['path'])
    generator_raw = read('generators/bca4f37ec5e9/generator.py')
    runtime_raw = read('src/arcpuzzles/runtime.py')
    generic_generator_member = PREFIX + 'shared/runtime/puzzle_generators/generic/concepts/band_dock/gen1.py'
    generic_generator_retained = generic_generator_member in z.namelist()

identity_checks = {
    'request_source_sha256': sha(suggestions_raw) == '8a7400259dc327111c9fe07280e12fe8ec2ca7038baf6f272d7c23cd6af5ad97',
    'request_canonical_sha256': canonical_request_hash == 'e016e26f2bac1aec90d59f284d2cb4ab7bf36ce0e683d4dbac18fc798da28788',
    'assets_manifest_sha256': sha(manifest_raw) == 'b8fbb8f8eb7a4260fa7e33decfe848beb77f7d06965a3fdfb9c9de649823d467',
    'asset_sha256': sha(log_raw) == asset['sha256'],
    'asset_bytes': len(log_raw) == asset['bytes'],
    'ticket_generator_sha256': sha(generator_raw) == '80add324b59500cbb90e762c2cfd6b9ad26d54325a4982f2d07684f5ef555c21',
}
assert all(identity_checks.values()), identity_checks
runtime_source = runtime_raw.decode()
tree = ast.parse(runtime_source)
selected = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {'apply_rule','validate_grid'}]
assert len(selected) == 2
# Preserve exact function ASTs. Postpone annotations to avoid importing unrelated runtime.
module = ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0), *selected],type_ignores=[])
namespace = {'math':math,'MAX_APPLY_INPUTS':64}
exec(compile(ast.fix_missing_locations(module),'WORK/repo/src/arcpuzzles/runtime.py','exec'),namespace)
class GenericCatalog:
    """Synthetic described generic row; no claim to load the absent generator."""
    def describe(self, task_id):
        assert task_id == 'generic_band_dock_gen1'
        return {'id':task_id,'has_generator':True,'kind':'generic'}
observed = None
probe_started = time.monotonic()
try:
    namespace['apply_rule'](GenericCatalog(),'generic_band_dock_gen1',[[[0]]],timeout=120)
except ValueError as exc:
    observed = str(exc)
probe_elapsed = time.monotonic()-probe_started
expected = 'generic_band_dock_gen1: apply needs a per-puzzle generator whose canonical rule can be resolved'
assert observed == expected, observed
assert expected in log_raw.decode()
guard = next(node for node in ast.walk(next(n for n in selected if n.name=='apply_rule')) if isinstance(node,ast.If) and 'per_puzzle' in ast.get_source_segment(runtime_source,node.test))
report = {
    'ticket_id':'ticket-778a55c01feed867','type':'tool_reproduction','request_id':REQUEST_ID,
    'seed':'fb46bc33d87e9f3496b538d75ca5bfe62eed4316cd0cfae5d3539fe1d09cc7e7',
    'status':'completed',
    'identity_checks':identity_checks,'request_canonical_sha256':canonical_request_hash,
    'members_read':members,'request':request,'assets_manifest':manifest,
    'retained_log':log_raw.decode(),
    'probe':{'kind':'source-level API guard replay from exact retained AST',
        'count':1,'input':[[[0]]],
        'catalog_row':'synthetic has_generator=true, kind=generic',
        'observed_exception':'ValueError','observed_message':observed,
        'matches_retained_log':True,'elapsed_seconds':probe_elapsed,
        'racket_executed':False,'full_cli_executed':False,
        'guard_line':guard.lineno,'guard_source':ast.get_source_segment(runtime_source,guard)},
    'proposed_request_disposition':{
        'decision':'accept_for_scoped_maintainer_assessment',
        'reason':'Retained log and current exact apply_rule guard agree: every described generic generator is rejected before runtime preparation. Request remains relevant; no generic replay feature is implemented here.',
        'suggested_scope':'Supported one-grid replay of selected generic PROGRAM with exact generator/program hashes, explicit research provenance, and no approval inheritance.',
    },
    'limitations':[
        'Historical asset contains only a rejection log; no original command receipt or replay grid is retained.',
        'The generic_band_dock_gen1 executable member is absent from this selected archive; target availability and its selected PROGRAM identity are not established.',
        'The synthetic catalog row isolates the unconditional API guard. It does not reproduce catalog lookup, full CLI execution, or Racket output.',
        'Ticket generator bca4f37ec5e9 is source-verified but is not the generic audit target. The old request source_sha256 is retained verbatim and is not asserted current.',
        'No broader generic-rule compatibility or safety claim; no unrelated shared changes implemented.'
    ],
    'generic_generator_member':generic_generator_member,
    'generic_generator_retained':generic_generator_retained,
    'total_script_seconds':time.monotonic()-started,
    'elapsed_minutes':None,
}
REPORT.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'report':str(REPORT),'status':report['status'],'identity_checks':identity_checks,'probe':report['probe'],'generic_generator_retained':generic_generator_retained},indent=2))
