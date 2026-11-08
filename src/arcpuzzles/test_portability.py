"""Explicit owner-side migration of narrow portable-test loader idioms.

No tests are imported or executed, and no fixture is rewritten by the runner.
Preview first; applying requires the exact saved source-bound proposal.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

SCHEMA = 'arcpuzzles-test-portability-proposal-v1'


def _sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _regular(root: Path, path: Path) -> None:
    if not path.is_relative_to(root):
        raise ValueError(f'Test path escapes library: {path}')
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f'Test migration refuses symlink paths: {part}')
        if part == root:
            break


def _rewrite(body: bytes, task_id: str) -> tuple[bytes, list[str]]:
    """Replace proven fixed-root ledger expressions and exact generator imports."""
    text = body.decode('utf-8')
    tree = ast.parse(text)
    bound = {}
    for node in ast.walk(tree):
        names = ([node.id] if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
                 else [node.arg] if isinstance(node, ast.arg)
                 else [node.name] if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                 else [a.asname or a.name.split('.')[0] for a in node.names]
                 if isinstance(node, (ast.Import, ast.ImportFrom)) else [])
        for name in names:
            bound[name] = bound.get(name, 0) + 1
    assigned = {n.targets[0].id: n.value for n in tree.body if isinstance(n, ast.Assign)
                and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                and bound.get(n.targets[0].id) == 1}
    path_names = {a.asname or a.name for n in tree.body if isinstance(n, ast.ImportFrom)
                  and n.level == 0 and n.module == 'pathlib' for a in n.names if a.name == 'Path'
                  and bound.get(a.asname or a.name) == 1}
    importlib_names = {a.asname or a.name for n in tree.body if isinstance(n, ast.Import)
                       for a in n.names if a.name == 'importlib'
                       and bound.get(a.asname or a.name) == 1}

    def fixed_root(node, seen=frozenset()):
        if isinstance(node, ast.Name) and node.id in assigned and node.id not in seen:
            return fixed_root(assigned[node.id], seen | {node.id})
        if isinstance(node, ast.Attribute) and node.attr == 'parent':
            return file_path(node.value) or fixed_root(node.value, seen)
        return (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute)
                and node.value.attr == 'parents' and file_path(node.value.value)
                and isinstance(node.slice, ast.Constant) and type(node.slice.value) is int
                and node.slice.value >= 0)

    def file_path(node):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in ('resolve', 'absolute') and not node.args and not node.keywords):
            return file_path(node.func.value)
        return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in path_names and len(node.args) == 1 and not node.keywords
                and isinstance(node.args[0], ast.Name) and node.args[0].id == '__file__')

    used = set(bound) | {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    used.update(a.asname or a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
                for a in n.names)
    suffix = 0
    while any(f'_arc_review_{name}{suffix}' in used for name in ('root', 'canonical', 'generator')):
        suffix += 1
    aliases = {name: f'_arc_review_{name}{suffix}' for name in ('root', 'canonical', 'generator')}
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    lines = body.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))

    def span(node):
        return offsets[node.lineno - 1] + node.col_offset, offsets[node.end_lineno - 1] + node.end_col_offset

    edits, changes = [], set()
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            parent = parents.get(node)
            if isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Div):
                continue  # only the complete path, never a matching prefix
            parts, base = [], node
            while isinstance(base, ast.BinOp) and isinstance(base.op, ast.Div):
                if not isinstance(base.right, ast.Constant) or type(base.right.value) is not str:
                    break
                parts.insert(0, base.right.value)
                base = base.left
            if '/'.join(parts) in ('data/canonical/puzzles.jsonl', 'shared/data/canonical/puzzles.jsonl') and fixed_root(base):
                edits.append((*span(node), f"{aliases['canonical']}({aliases['root']}(__file__))".encode()))
                changes.add('canonical_path')
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and isinstance(node.func.value, ast.Name) and node.func.value.id in importlib_names
              and node.func.attr == 'import_module' and not node.keywords and len(node.args) == 1
              and isinstance(node.args[0], ast.Constant)
              and node.args[0].value == f'puzzle_generators.per_puzzle.{task_id}.generator'
              and isinstance(parents.get(node), ast.Assign) and parents[node] in tree.body):
            edits.append((*span(node), f"{aliases['generator']}({task_id!r}, root={aliases['root']}(__file__))[0]".encode()))
            changes.add('selected_generator')
    if not edits:
        return body, []
    imports = [('find_root', aliases['root'])]
    if 'canonical_path' in changes:
        imports.append(('canonical_path', aliases['canonical']))
    if 'selected_generator' in changes:
        imports.append(('load_selected_generator', aliases['generator']))
    # Insert after the docstring/future block, before any rewritten call can
    # execute. Keep leading comments/shebang/encoding and avoid AST reformatting.
    imports_at = tree.body[0].lineno - 1
    if isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
        imports_at = tree.body[0].end_lineno
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == '__future__':
            imports_at = node.end_lineno
    ending = '\r\n' if b'\r\n' in body else '\n'
    insertion = 'from reviewer_support import ' + ', '.join(f'{a} as {b}' for a, b in imports) + ending
    edits.append((offsets[imports_at], offsets[imports_at], insertion.encode()))
    for start, end, replacement in sorted(edits, reverse=True):
        body = body[:start] + replacement + body[end:]
    ast.parse(body)  # fail closed if a lexical edge case makes the patch invalid
    return body, sorted(changes)


def _binding(proposal: dict) -> str:
    return _sha(json.dumps({k: proposal[k] for k in ('schema', 'library', 'task_id', 'files', 'manual_review')},
                           sort_keys=True, separators=(',', ':')).encode())


def plan_migration(root: Path, task_id: str) -> dict:
    """Preview task-owned test edits; complex imports remain manual findings."""
    root = Path(root).absolute()
    if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_-]*', task_id):
        raise ValueError('Use an exact generator ID')
    home = root / 'generators' / task_id
    _regular(root, home)
    if not home.is_dir():
        raise FileNotFoundError(home)
    paths = sorted((home / 'tests').rglob('*.py')) if (home / 'tests').exists() else []
    fixture = home / f'test_generator_{task_id}.py'
    if fixture.exists() or fixture.is_symlink():
        paths.append(fixture)
    rows, manual = [], []
    for path in paths:
        _regular(root, path)
        before = path.read_bytes()
        try:
            after, changes = _rewrite(before, task_id)
        except (UnicodeError, SyntaxError) as error:
            manual.append({'path': path.relative_to(root).as_posix(), 'code': 'unsupported_syntax', 'message': str(error)})
            continue
        relative = path.relative_to(root).as_posix()
        if changes:
            rows.append({'path': relative, 'before_sha256': _sha(before), 'after_sha256': _sha(after),
                         'changes': changes, 'patch': ''.join(difflib.unified_diff(
                             before.decode().splitlines(keepends=True), after.decode().splitlines(keepends=True),
                             fromfile='a/' + relative, tofile='b/' + relative))})
        # Existing preflight remains authoritative; report residual problems
        # rather than guessing replacements for private tool APIs.
        for n in ast.walk(ast.parse(after)):
            modules = ([n.module] if isinstance(n, ast.ImportFrom) else
                       [a.name for a in n.names] if isinstance(n, ast.Import) else [])
            for module in modules:
                if module and (module == 'scripts' or module.startswith('scripts.')):
                    manual.append({'path': relative, 'line': n.lineno, 'code': 'legacy_scripts_import',
                                   'message': f'{module}: API signatures require manual review; not rewritten'})
    result = {'schema': SCHEMA, 'library': str(root), 'task_id': task_id, 'status': 'preview',
              'files': rows, 'manual_review': manual}
    result['proposal_sha256'] = _binding(result)
    return result


def apply_migration(root: Path, proposal: dict) -> dict:
    """Apply an exact preview to owner tests, retaining originals before edits."""
    root = Path(root).absolute()
    if any((ancestor / 'PACKET-MANIFEST.json').exists() for ancestor in (root, *root.parents)):
        raise ValueError('Issued packet fixtures are frozen; apply migrations in the owner library before issuing a new packet')
    if not isinstance(proposal, dict) or proposal.get('schema') != SCHEMA:
        raise ValueError('Invalid migration proposal')
    if proposal.get('proposal_sha256') != _binding(proposal):
        raise ValueError('Invalid or changed migration proposal')
    current = plan_migration(root, proposal['task_id'])
    if current['proposal_sha256'] != proposal['proposal_sha256']:
        raise ValueError('Migration source changed; preview a new proposal')
    if not current['files']:
        return {**current, 'status': 'no_changes'}
    backup = root / 'var/test-portability' / current['proposal_sha256']
    _regular(root, backup)
    if backup.exists():
        raise FileExistsError(f'Migration backup already exists: {backup}')
    bodies = []
    for row in current['files']:
        path = root / row['path']
        before = path.read_bytes()
        if _sha(before) != row['before_sha256']:
            raise ValueError(f'Migration source changed: {path}')
        after, _ = _rewrite(before, current['task_id'])
        bodies.append((path, before, after))
    # Preserve every predecessor before changing any source file.
    for path, before, _ in bodies:
        saved = backup / path.relative_to(root)
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(before)
    for path, before, after in bodies:
        _regular(root, path)
        if path.read_bytes() != before:
            raise ValueError(f'Migration source changed; originals retained at {backup}')
        descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(after)
            os.chmod(temporary, path.stat().st_mode & 0o777)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return {**current, 'status': 'applied', 'backup_directory': backup.relative_to(root).as_posix(),
            'tests_executed': False, 'approval_changed': False}
