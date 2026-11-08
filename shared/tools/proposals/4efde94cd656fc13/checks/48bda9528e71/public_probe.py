"""Probe strict saved one-query projection using temporary corrupted copies."""
import argparse, hashlib, importlib.util, json, shutil, tempfile
from pathlib import Path

def digest_tree(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}

def run(bundle, output):
    work = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location('packet_public_projection_probe', work / 'preview_public.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    bundle = Path(bundle).resolve()
    before = digest_tree(bundle)
    valid = module.verify_export(bundle)
    records = []
    for case in ('leaked_query_answer', 'orphan_public_file', 'missing_public_view'):
        with tempfile.TemporaryDirectory(prefix='arc-public-rejection-') as tmp:
            clone = Path(tmp) / 'bundle'; shutil.copytree(bundle, clone)
            public = sorted((clone / 'public').glob('*.json'))
            if case == 'leaked_query_answer':
                value = json.loads(public[0].read_text()); value['test'][0]['output'] = [[0]]
                public[0].write_text(json.dumps(value))
            elif case == 'orphan_public_file':
                (clone / 'public' / ('0' * 64 + '.json')).write_text('{}')
            else:
                public[0].unlink()
            try:
                module.verify_export(clone)
            except (ValueError, OSError, KeyError, TypeError) as error:
                records.append({'case': case, 'rejected': True, 'error': str(error)})
            else:
                records.append({'case': case, 'rejected': False})
    unchanged = before == digest_tree(bundle)
    result = {'valid_projection': valid, 'negative_cases': records, 'original_unchanged': unchanged,
              'source_files': before, 'racket_replayed': False, 'training_admitted': False}
    Path(output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'views': valid['views'], 'rejections': sum(x['rejected'] for x in records),
                      'original_unchanged': unchanged, 'output': str(output)}))
    if not unchanged or not all(x['rejected'] for x in records): raise SystemExit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True); parser.add_argument('--out', required=True)
    args = parser.parse_args(); run(args.bundle, args.out)
