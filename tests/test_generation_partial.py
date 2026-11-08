"""Interrupted generation keeps completed episodes; only a full run writes the output."""
import json
import shutil

import pytest

from arcpuzzles import Catalog, cli, runtime



@pytest.fixture
def mock_source_identity(monkeypatch):
    # CLI retention unit tests replace generation itself; runtime source binding
    # has separate tests below using actual mapped fixture files.
    monkeypatch.setattr(cli, "generation_source_identity", lambda *args: "fixture-source-id")

def _episode(index):
    return {"task_id": "t", "seed": 10 + index, "episode_index": index, "train": [], "test": [],
            "executed_rule_hash": "abc", "rejections": [],
            "provenance": {"generator_sha256": "g", "catalog_rule_hash": "r"}}


def test_failed_worker_returns_only_contiguous_completed_episodes(tmp_path, monkeypatch):
    (tmp_path / "gen.py").write_text("# retained fixture source\n")
    source_hash = runtime.hashlib.sha256((tmp_path / "gen.py").read_bytes()).hexdigest()
    row = {"id": "t", "kind": "per_puzzle", "runtime_generator": "gen.py", "generator_sha256": source_hash,
           "rule_hash": "r", "approved": False, "family": None, "split": None, "train_safety": "unverified"}
    monkeypatch.setattr(runtime, "sha256", lambda path: source_hash)
    monkeypatch.setattr(runtime, "local_path", lambda stage, rel: stage / rel)

    def fake_run(command, cwd, timeout):
        lines = [json.dumps(_episode(2)), json.dumps(_episode(3)), json.dumps(_episode(5)), '{"torn']
        (cwd / "episodes.partial.jsonl").write_text("\n".join(lines))
        return {"command": command, "exit_code": -15, "timed_out": True, "stdout": "", "stderr": ""}

    monkeypatch.setattr(runtime, "run_process", fake_run)
    with pytest.raises(runtime.GenerationFailure) as caught:
        runtime.generate_in_runtime(tmp_path, row, count=8, seed=10, difficulty=None, n_train=1,
                                    n_test=1, start_index=2)
    kept = caught.value.partial_episodes
    assert [e["episode_index"] for e in kept] == [2, 3]
    assert all("provenance" in e for e in kept)
    assert caught.value.requested == 6
    assert "2/6 episodes completed and kept" in str(caught.value)


def _args(tmp_path, *extra):
    return ["generate", "t", "--count", "4", "--seed", "10", "--out", str(tmp_path / "out.jsonl"), *extra]


def test_cli_keeps_partial_then_resumes_to_one_complete_file(tmp_path, monkeypatch, capsys, mock_source_identity):
    calls = []
    monkeypatch.setattr(cli.Catalog, "describe",
                        lambda self, tid: {"generator_sha256": "g", "rule_hash": "r"})

    def fake_generate(catalog, task_id, *, count, start_index, **options):
        calls.append(start_index)
        if len(calls) == 1:
            run = {"exit_code": -15, "timed_out": True, "stdout": "", "stderr": ""}
            raise runtime.GenerationFailure(task_id, run, [_episode(0), _episode(1)], count)
        return [_episode(i) for i in range(start_index, count)]

    monkeypatch.setattr(cli, "generate", fake_generate)
    assert cli.main(_args(tmp_path)) == 1
    partial = tmp_path / "out.jsonl.partial.jsonl"
    assert not (tmp_path / "out.jsonl").exists()
    assert len(partial.read_text().splitlines()) == 3  # identity header + two episodes
    assert cli.main(_args(tmp_path)) == 1  # a plain rerun must not clobber the partial file
    assert "--resume" in capsys.readouterr().err
    assert cli.main(_args(tmp_path, "--resume")) == 0
    assert calls == [0, 2]
    rows = [json.loads(line) for line in (tmp_path / "out.jsonl").read_text().splitlines()]
    assert [r["episode_index"] for r in rows] == [0, 1, 2, 3]
    assert not partial.exists()


def test_cli_resume_rejects_changed_arguments(tmp_path, monkeypatch, mock_source_identity):
    monkeypatch.setattr(cli.Catalog, "describe",
                        lambda self, tid: {"generator_sha256": "g", "rule_hash": "r"})
    header = {"schema": "arcpuzzles-generate-partial-v1", "task_id": "t", "count": 4, "seed": 999,
              "sample_index": 0, "difficulty": None, "overrides": {}, "n_train": 3, "n_test": 1,
              "reference": "canonical", "allow_unapproved": False, "generation_sources_sha256": "fixture-source-id"}
    (tmp_path / "out.jsonl.partial.jsonl").write_text(json.dumps(header) + "\n")
    assert cli.main(_args(tmp_path, "--resume")) == 1


def test_cli_resume_rejects_changed_generator(tmp_path, monkeypatch, mock_source_identity):
    monkeypatch.setattr(cli.Catalog, "describe",
                        lambda self, tid: {"generator_sha256": "NEW", "rule_hash": "r"})
    header = {"schema": "arcpuzzles-generate-partial-v1", "task_id": "t", "count": 4, "seed": 10,
              "sample_index": 0, "difficulty": None, "overrides": {}, "n_train": 3, "n_test": 1,
              "reference": "canonical", "allow_unapproved": False, "generation_sources_sha256": "fixture-source-id"}
    (tmp_path / "out.jsonl.partial.jsonl").write_text(json.dumps(header) + "\n" + json.dumps(_episode(0)) + "\n")
    assert cli.main(_args(tmp_path, "--resume")) == 1


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_start_index_regenerates_the_identical_tail():
    catalog = Catalog()
    full = catalog.generate("6c68e1b008a5", count=4, seed=41, n_train=2, n_test=1)
    tail = catalog.generate("6c68e1b008a5", count=4, seed=41, n_train=2, n_test=1, start_index=2)
    assert [e["episode_index"] for e in full] == [0, 1, 2, 3]
    assert tail == full[2:]


def test_failed_generation_creates_nested_partial_output(tmp_path, monkeypatch, mock_source_identity):
    def fail(*a, **kw):
        raise runtime.GenerationFailure('t', {'exit_code': -15, 'timed_out': True, 'stdout': '', 'stderr': ''},
                                        [_episode(0)], 4)
    monkeypatch.setattr(cli, 'generate', fail)
    out = tmp_path / 'new' / 'nested' / 'out.jsonl'
    assert cli.main(['generate', 't', '--count', '4', '--seed', '10', '--out', str(out)]) == 1
    partial = out.with_name(out.name + '.partial.jsonl')
    assert partial.is_file()
    assert json.loads(partial.read_text().splitlines()[1])['episode_index'] == 0


def test_partial_prefix_stops_at_first_index_gap(tmp_path, monkeypatch):
    (tmp_path / 'gen.py').write_text('# retained fixture source\n')
    source_hash = runtime.hashlib.sha256((tmp_path / 'gen.py').read_bytes()).hexdigest()
    row = {'id': 't', 'kind': 'per_puzzle', 'runtime_generator': 'gen.py', 'generator_sha256': source_hash,
           'rule_hash': 'r', 'approved': False, 'family': None, 'split': None, 'train_safety': 'unverified'}
    monkeypatch.setattr(runtime, 'sha256', lambda p: source_hash)
    monkeypatch.setattr(runtime, 'local_path', lambda stage, rel: stage / rel)
    def fail(command, cwd, timeout):
        (cwd / 'episodes.partial.jsonl').write_text('\n'.join(json.dumps(_episode(i)) for i in [0, 8, 2]))
        return {'exit_code': -15, 'timed_out': True, 'stdout': '', 'stderr': ''}
    monkeypatch.setattr(runtime, 'run_process', fail)
    with pytest.raises(runtime.GenerationFailure) as exc:
        runtime.generate_in_runtime(tmp_path, row, count=4, seed=10, difficulty=None, n_train=1, n_test=1)
    assert [e['episode_index'] for e in exc.value.partial_episodes] == [0]


@pytest.mark.parametrize('indices,seeds', [([0, 1, 2, 3, 4], None), ([0], [777])])
def test_resume_refuses_overfull_or_wrong_seed_partial(tmp_path, monkeypatch, indices, seeds, mock_source_identity):
    monkeypatch.setattr(cli.Catalog, 'describe', lambda self, tid: {'id': 't', 'generator_sha256': 'g', 'rule_hash': 'r'})
    monkeypatch.setattr(cli, 'generate', lambda *a, start_index, count, **kw: [_episode(i) for i in range(start_index, count)])
    header = {'schema': 'arcpuzzles-generate-partial-v1', 'task_id': 't', 'count': 4, 'seed': 10,
              'sample_index': 0, 'difficulty': None, 'overrides': {}, 'n_train': 3, 'n_test': 1,
              'reference': 'canonical', 'allow_unapproved': False, 'generation_sources_sha256': 'fixture-source-id'}
    rows = [_episode(i) for i in indices]
    if seeds:
        rows[0]['seed'] = seeds[0]
    (tmp_path / 'out.jsonl.partial.jsonl').write_text('\n'.join(json.dumps(x) for x in [header, *rows]) + '\n')
    assert cli.main(_args(tmp_path, '--resume')) == 1
    assert not (tmp_path / 'out.jsonl').exists()


def test_keyboard_interrupt_carries_completed_prefix(tmp_path, monkeypatch):
    (tmp_path / 'gen.py').write_text('# retained fixture source\n')
    source_hash = runtime.hashlib.sha256((tmp_path / 'gen.py').read_bytes()).hexdigest()
    row = {'id': 't', 'kind': 'per_puzzle', 'runtime_generator': 'gen.py', 'generator_sha256': source_hash,
           'rule_hash': 'r', 'approved': False, 'family': None, 'split': None, 'train_safety': 'unverified'}
    monkeypatch.setattr(runtime, 'sha256', lambda p: source_hash)
    monkeypatch.setattr(runtime, 'local_path', lambda stage, rel: stage / rel)
    def interrupted(command, cwd, timeout):
        (cwd / 'episodes.partial.jsonl').write_text(json.dumps(_episode(0)) + '\n')
        raise KeyboardInterrupt
    monkeypatch.setattr(runtime, 'run_process', interrupted)
    with pytest.raises(runtime.GenerationFailure) as exc:
        runtime.generate_in_runtime(tmp_path, row, count=4, seed=10, difficulty=None, n_train=1, n_test=1)
    assert [e['episode_index'] for e in exc.value.partial_episodes] == [0]
    assert exc.value.run['interrupted'] is True


@pytest.mark.parametrize('changed_source', ['helper', 'archival'])
def test_resume_source_binding_rejects_helper_and_archival_drift(library, tmp_path, monkeypatch, changed_source):
    tid = 'aaaa00000001'
    helper = library / 'shared/helper.py'
    helper.write_text('VALUE = 1\n')
    archival = library / 'shared/data/base/solutions/authority.json'
    archival.parent.mkdir(parents=True)
    archival.write_text('{"rule": "old"}\n')
    mapping = library / 'catalog/runtime_files.json'
    entries = json.loads(mapping.read_text())
    entries += [{'path': 'shared/helper.py', 'target': 'puzzle_generators/helper.py'},
                {'path': 'shared/data/base/solutions/authority.json', 'target': 'data/base/solutions/authority.json'}]
    mapping.write_text(json.dumps(entries))
    (library / 'catalog/authority_files.json').write_text(json.dumps({'data/base/solutions/authority.json': tid}))
    calls = []
    def generated(catalog, task_id, *, count, start_index, **options):
        row = catalog.describe(task_id)
        def episode(i):
            return {'task_id': tid, 'seed': options['seed'] + i, 'episode_index': i, 'rejections': [],
                    'train': [], 'test': [], 'provenance': {'generator_sha256': row['generator_sha256'],
                    'catalog_rule_hash': row['rule_hash']}}
        calls.append(start_index)
        if len(calls) == 1:
            raise runtime.GenerationFailure(tid, {'exit_code': 1, 'timed_out': False, 'stdout': '', 'stderr': ''},
                                            [episode(0)], count)
        return [episode(i) for i in range(start_index, count)]
    monkeypatch.setattr(cli, 'generate', generated)
    out = tmp_path / 'episodes.jsonl'
    args = ['--library', str(library), 'generate', tid, '--count', '2', '--seed', '10', '--out', str(out),
            '--reference', 'archival', '--allow-unapproved']
    assert cli.main(args) == 1
    original = out.with_name(out.name + '.partial.jsonl').read_bytes()
    (helper if changed_source == 'helper' else archival).write_text('changed source\n')
    assert cli.main(args + ['--resume']) == 1
    assert not out.exists()
    assert out.with_name(out.name + '.partial.jsonl').read_bytes() == original


def test_legacy_partial_without_source_fingerprint_is_refused(tmp_path, monkeypatch, capsys, mock_source_identity):
    monkeypatch.setattr(cli.Catalog, 'describe', lambda self, tid: {'id': 't', 'generator_sha256': 'g', 'rule_hash': 'r'})
    monkeypatch.setattr(cli, 'generate', lambda *a, start_index, count, **kw: [_episode(i) for i in range(start_index, count)])
    header = {'schema': 'arcpuzzles-generate-partial-v1', 'task_id': 't', 'count': 4, 'seed': 10,
              'sample_index': 0, 'difficulty': None, 'overrides': {}, 'n_train': 3, 'n_test': 1,
              'reference': 'canonical', 'allow_unapproved': False}
    (tmp_path / 'out.jsonl.partial.jsonl').write_text('\n'.join(json.dumps(x) for x in [header, _episode(0)]) + '\n')
    assert cli.main(_args(tmp_path, '--resume')) == 1
    assert 'source fingerprint' in capsys.readouterr().err.lower()
    assert not (tmp_path / 'out.jsonl').exists()
