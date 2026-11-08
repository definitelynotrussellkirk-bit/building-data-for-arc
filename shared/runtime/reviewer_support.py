"""Portable public helpers for reviewer tests in libraries and copied runtimes.

In a runtime: ``from reviewer_support import canonical_pairs, find_root,
load_selected_generator``.
Use ``root=find_root(__file__)`` to bind data to the test's own tree, not cwd.
Canonical answers are authoring data; do not import them during a blind solve.
"""
from pathlib import Path


def public_challenge_bytes(challenge):
    """Canonical bytes of visible demos/query inputs, excluding private fields.

    Use these exact bytes for an opt-in public file and its content ID. This
    does not change existing dataset identities or validate reference labels.
    """
    import json

    def grid(value):
        if (type(value) is not list or not 1 <= len(value) <= 30
                or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
            raise ValueError('public grid must have 1..30 rows and columns')
        width = len(value[0])
        if any(type(row) is not list or len(row) != width
               or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
               for row in value):
            raise ValueError('public grid must be rectangular with exact integer colors 0..9')
        return value

    if not isinstance(challenge, dict):
        raise ValueError('challenge must contain train/test lists')
    train, test = challenge.get('train'), challenge.get('test')
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError('challenge must contain nonempty train/test lists')
    try:
        public = {'train': [{'input': grid(pair['input']), 'output': grid(pair['output'])}
                            for pair in train],
                  'test': [{'input': grid(pair['input'])} for pair in test]}
    except (KeyError, TypeError) as error:
        raise ValueError('visible pairs require their input and demonstration output grids') from error
    return (json.dumps(public, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode('utf-8')


def public_challenge_id(challenge):
    """SHA-256 of exactly public_challenge_bytes(challenge)."""
    import hashlib
    return hashlib.sha256(public_challenge_bytes(challenge)).hexdigest()
import hashlib
import importlib
import importlib.util
import json
import os
import re
import sys


def canonical_path(root):
    root = Path(root).resolve()
    for relative in ('data/canonical/puzzles.jsonl', 'shared/data/canonical/puzzles.jsonl'):
        path = root / relative
        if path.is_file():
            return path
    raise FileNotFoundError(f'No canonical ledger under {root}')


def find_root(start):
    """Find the nearest library/runtime for an explicit file or directory.

    Also supports packet evidence at WORK/checks/... with WORK/repo/ beside
    checks. A nearer copied runtime wins. This bounded fallback never uses cwd,
    environment variables, arbitrary sibling names, or escaping symlinks.
    """
    path = Path(start).resolve()
    if path.is_file():
        path = path.parent
    for candidate in (path, *path.parents):
        try:
            canonical_path(candidate)
            return candidate
        except FileNotFoundError:
            pass
        # Only the documented packet checks/repo sibling layout is inferred.
        # Source-bound task evidence under repo/generators already uses the
        # normal ancestor branch above.
        if path.is_relative_to(candidate / 'checks'):
            repo = candidate / 'repo'
            ledger = repo / 'shared/data/canonical/puzzles.jsonl'
            if ledger.is_file():
                resolved_repo = repo.resolve()
                if (not resolved_repo.is_relative_to(candidate)
                        or not ledger.resolve().is_relative_to(resolved_repo)):
                    raise ValueError(f'Workspace repository escapes its tree: {repo}')
                return resolved_repo
    raise FileNotFoundError(f'No library/runtime ancestor or checks/repo workspace for {start}')


def load_selected_generator(task_id, *, root=None):
    """Return ``(module, source_path, sha256)`` from one explicit source tree.

    Exact IDs only. ``root`` wins over ARCPUZZLES_HOME; otherwise that variable
    or this helper's own library/runtime ancestor is used, never cwd. Repository
    sources live in generators/<id>/generator.py. A staged runtime must select
    that source in RUNTIME_MANIFEST.json, including generic-generator mappings.

    This executes the selected module's top-level Python, not generate(), tests
    or Racket. It reports current source bytes, not approval or training status.
    Cached puzzle_generators dependencies from another tree are rejected: use a
    fresh process to inspect a different tree. A task-test snapshot's own
    shared/runtime mirror is allowed only when its manifest identity and bytes
    match the selected execution-layout copy. sys.path is restored after import.
    """
    if not isinstance(task_id, str) or not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_-]*', task_id):
        raise ValueError('Use an exact generator ID, not a path or alias')
    if root is None:
        root = os.environ.get('ARCPUZZLES_HOME')
        if not root:
            helper = Path(__file__).resolve()
            root = find_root(helper)
            # The repository's canonical ledger also makes shared/ a data
            # root. Its generator library is one level above, unlike a copied
            # runtime where this helper and the selected sources share a root.
            if ((root.parent / 'shared/runtime/reviewer_support.py').resolve() == helper
                    and (root.parent / 'generators').is_dir()):
                root = root.parent
    root = Path(root).resolve()
    canonical_path(root)  # An explicit root must itself be a library/runtime.
    library_path = f'generators/{task_id}/generator.py'
    manifest_path = root / 'RUNTIME_MANIFEST.json'
    if manifest_path.is_file():
        entries = json.loads(manifest_path.read_text(encoding='utf-8')).get('files', [])
        matches = [row for row in entries if row.get('library_path') == library_path]
        # Task-test snapshots also copy repository paths for Catalog/tests.
        # Those mirrors do not replace the selected execution-layout source.
        selected = [row for row in matches if row.get('runtime_path') != library_path]
        matches = selected or matches
        if not matches:
            raise FileNotFoundError(f'Generator {task_id} is not selected in {manifest_path}')
        if len(matches) != 1:
            raise ValueError(f'Ambiguous runtime selection for {task_id}')
        relative = Path(matches[0]['runtime_path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError(f'Unsafe runtime generator path: {relative}')
        source = root / relative
        dependency_root = root
    elif (root / 'generators').is_dir():
        source = root / library_path
        dependency_root = root / 'shared/runtime'
    else:
        raise FileNotFoundError(f'No selected generator library/runtime under {root}')
    if source.is_symlink() or not source.resolve().is_relative_to(root):
        raise ValueError(f'Generator source must stay inside its selected tree: {source}')
    if not source.is_file():
        raise FileNotFoundError(source)
    package_root = (dependency_root / 'puzzle_generators').resolve()
    if not package_root.is_relative_to(root) or not package_root.is_dir():
        raise ValueError(f'Missing local puzzle_generators dependencies under {dependency_root}')

    def same_snapshot_mirror(origin):
        """Accept only declared identical mirrors, never arbitrary in-tree files."""
        if not manifest_path.is_file():
            return False
        mirror = root / 'shared/runtime/puzzle_generators'
        path = Path(origin).resolve()
        if not path.is_relative_to(mirror):
            return False
        if path.is_dir():
            path = path / '__init__.py'
        selected = package_root / path.relative_to(mirror)
        matches = []
        for candidate in (path, selected):
            if candidate.is_symlink() or not candidate.is_file() or not candidate.resolve().is_relative_to(root):
                return False
            rows = [row for row in entries if row.get('runtime_path') == candidate.relative_to(root).as_posix()]
            if len(rows) != 1:
                return False
            row = rows[0]
            if hashlib.sha256(candidate.read_bytes()).hexdigest() != row.get('sha256'):
                return False
            matches.append(row)
        return (matches[0].get('library_path') is not None
                and matches[0].get('library_path') == matches[1].get('library_path')
                and matches[0].get('sha256') == matches[1].get('sha256'))

    def check_cached_dependencies():
        for name, module in tuple(sys.modules.items()):
            if name != 'puzzle_generators' and not name.startswith('puzzle_generators.'):
                continue
            origins = list(getattr(module, '__path__', []))
            origin = getattr(module, '__file__', None)
            if origin:
                origins.append(origin)
            if not origins or any(not Path(path).resolve().is_relative_to(package_root)
                                  and not same_snapshot_mirror(path) for path in origins):
                raise ImportError(f'{name} belongs to another source tree; use a fresh process for {root}')

    check_cached_dependencies()
    body = source.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    name = '_arcpuzzles_selected_' + hashlib.sha256(str(source).encode()).hexdigest() + '_' + digest
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError(f'Cannot import selected generator {source}')
    module = importlib.util.module_from_spec(spec)
    before_path = list(sys.path)
    previous = sys.modules.get(name)
    try:
        sys.path.insert(0, str(dependency_root))
        importlib.import_module('puzzle_generators')
        check_cached_dependencies()
        sys.modules[name] = module
        # Compile exactly the hashed bytes; timestamp-based pyc reuse could
        # otherwise return old code while reporting a new source hash.
        exec(compile(body, str(source), 'exec'), module.__dict__)
        check_cached_dependencies()  # also verify dependencies first imported by this module
    except BaseException:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise
    finally:
        sys.path[:] = before_path
    return module, source, digest


def normalize_grid(grid):
    """Normalize integer grids and canonical digit row strings; reject missing data."""
    if not isinstance(grid, list) or not grid:
        raise ValueError('Expected a nonempty grid')
    rows = []
    for row in grid:
        if isinstance(row, str):
            row = [int(c) for c in row if not c.isspace()]
        if not isinstance(row, list) or not row or any(type(c) is not int or not 0 <= c <= 9 for c in row):
            raise ValueError('Expected nonempty rows of integer colors 0..9')
        rows.append(list(row))
    if len({len(row) for row in rows}) != 1:
        raise ValueError('Ragged grid')
    return rows


def canonical_pairs(task_id, *, root, variant=None, labeled_only=False):
    """Read normalized train/test pairs, retaining variant/split/pair identity.

    Exact task IDs only. All variants by default; malformed pairs raise instead
    of silently shrinking coverage. ``variant`` selects a zero-based ledger row.
    ``labeled_only=True`` skips test queries with no output key. Inputs are still
    validated; missing train labels and malformed present outputs always raise.
    """
    rows = []
    with canonical_path(root).open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get('task_id') == task_id:
                    rows.append(row)
    if not rows:
        raise KeyError(task_id)
    if variant is not None and (type(variant) is not int or not 0 <= variant < len(rows)):
        raise ValueError('Canonical variant out of range')
    result = []
    for vi, row in enumerate(rows):
        if variant is not None and vi != variant:
            continue
        for split in ('train', 'test'):
            pairs = row.get(split, [])
            if isinstance(pairs, dict):
                pairs = [pairs]
            if not isinstance(pairs, list):
                raise ValueError(f'{task_id} variant {vi} {split}: invalid pair collection')
            for pi, pair in enumerate(pairs):
                if not isinstance(pair, dict):
                    raise ValueError(f'{task_id} variant {vi} {split} pair {pi}: invalid pair')
                inp = normalize_grid(pair.get('input'))
                if labeled_only and split == 'test' and 'output' not in pair:
                    continue
                result.append({'input': inp,
                               'output': normalize_grid(pair.get('output')),
                               'variant': vi, 'split': split, 'pair_index': pi})
    return result
