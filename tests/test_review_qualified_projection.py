"""Sequential public writer regressions; fixtures are synthetic, not Racket proof.

The real source inventory, receipt parser and execution validator run here.
The receipt claims are synthetic; no frozen engine is monkeypatched. Native protected
qualification of the actual adapter is separate round evidence.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import parametric_promotion as native


from test_parametric_promotion import candidate

TASK_ID = "aaaa00000001"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "packet_qualified_projection", HOME / "src/arcpuzzles/review_full_packet_files/preview_public.py")
EXPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTER)


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


@pytest.fixture
def qualified(candidate, tmp_path):
    catalog, task_id, home = candidate
    root = catalog.root
    source = home / "adapter.py"
    contract, binding = native._ready(catalog, task_id)
    jobs, episodes, checks = [], [], []
    for rounds, side in ((1, "left"), (2, "right")):
        for seed in (0, 17):
            settings = {"side": side}
            job = {"settings": settings, "seed": seed, "demos": 3, "queries": 4}
            program = "(rule! g)" if rounds == 1 else "(rule! (flip-lr g))"
            pairs = [{"input": [[seed // 10, seed % 10, index, 9]],
                      "output": [[seed // 10, seed % 10, index, 9]] if rounds == 1
                      else [[9, index, seed % 10, seed // 10]]} for index in range(7)]
            jobs.append(job)
            episodes.append({"task_id": TASK_ID, "settings": settings,
                             "seed": seed, "program": program, "program_sha256": sha(program.encode()),
                             "train": pairs[:3], "test": pairs[3:]})
            checks.append({"survivors": [settings], "label_count": 7})
    execution = {"episodes": episodes, "checks": checks,
                 "racket": {"backend": "racket", "protected": True}, "racket_evaluations": 28}
    programs = native._check_execution(execution, jobs, binding, contract)
    directory = tmp_path / "qualification"
    directory.mkdir()
    (directory / "execution.json").write_bytes(raw(execution))
    qualification = {"schema": native.QUALIFICATION, "status": "qualified", "task_id": TASK_ID,
                     "source_binding": binding, "contract": contract, "jobs": jobs, "programs": programs,
                     "execution": {"path": "execution.json", "sha256": sha(raw(execution))},
                     "training_admitted": False}
    path = directory / "qualification.json"
    path.write_bytes(raw(qualification))
    return root, source, path, qualification, execution


def rewrite_receipts(fixture):
    _, _, path, qualification, execution = fixture
    encoded = raw(execution)
    path.with_name("execution.json").write_bytes(encoded)
    qualification["execution"]["sha256"] = sha(encoded)
    path.write_bytes(raw(qualification))


def test_first_view_matches_single_query_and_ignores_all_private_fields(qualified):
    episode = qualified[4]["episodes"][0]
    expected = EXPORTER.public_view_bytes(episode)
    single = deepcopy(episode)
    single["test"] = single["test"][:1]
    assert EXPORTER.public_view_bytes(single) == expected
    changed = deepcopy(episode)
    changed.update(seed=999, settings={"unrelated": "private"}, program="private program")
    changed["test"][0]["output"] = [[8]]
    changed["test"][1:] = [{"input": [[8, 8]], "output": [[7]]}]
    assert EXPORTER.public_view_bytes(changed) == expected
    visible = json.loads(expected)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])


@pytest.mark.parametrize("index", [True, False, -1, 4, 1.0])
def test_query_index_is_an_exact_bounded_integer(qualified, index):
    with pytest.raises(ValueError, match="query_index"):
        EXPORTER.public_view_bytes(qualified[4]["episodes"][0], index)


def test_export_has_sorted_visible_hash_names_and_private_query_order(qualified, tmp_path, monkeypatch):
    root, _, path, _, execution = qualified
    written = []
    write_bytes = Path.write_bytes

    def observe(path, value):
        if path.parent.name == "public":
            written.append(path.stem)
        return write_bytes(path, value)

    monkeypatch.setattr(Path, "write_bytes", observe)
    output = tmp_path / "export"
    result = EXPORTER.export_qualified(path, output, library=root)
    assert result["views"] == 16 and result["episodes"] == 4
    assert written == sorted(set(written))
    assert {child.name for child in output.iterdir()} == {"public", "private"}
    manifest = json.loads((output / "private/manifest.json").read_bytes())
    assert [row["path"] for row in manifest["public_files"]] == sorted(row["path"] for row in manifest["public_files"])
    for mapping, episode in zip(manifest["episodes"], execution["episodes"]):
        assert mapping["view_ids"] == [sha(EXPORTER.public_view_bytes(episode, index)) for index in mapping["source_indices"]]
    for file in (output / "public").iterdir():
        payload = file.read_bytes()
        assert file.name == sha(payload) + ".json"
        visible = json.loads(payload)
        assert set(visible) == {"train", "test"}
        assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    assert EXPORTER.verify_export(output, library=root)["status"] == "verified_projection"
    assert manifest["training_admitted"] is False and manifest["racket_replayed"] is False


@pytest.mark.parametrize("change", ["source", "execution_bytes", "status", "program_map", "unprotected"])
def test_native_receipt_failures_publish_nothing(qualified, tmp_path, change):
    root, source, path, qualification, execution = qualified
    if change == "source":
        source.write_text("# changed after qualification\n")
    elif change == "execution_bytes":
        file = path.with_name("execution.json")
        file.write_bytes(file.read_bytes() + b" ")
    else:
        if change == "status":
            qualification["status"] = "accepted"
        elif change == "program_map":
            qualification["programs"] = {}
        else:
            execution["racket"]["protected"] = False
        rewrite_receipts(qualified)
    output = tmp_path / "rejected"
    with pytest.raises(ValueError):
        EXPORTER.export_qualified(path, output, library=root)
    assert not output.exists()


@pytest.mark.parametrize("change", ["boolean_input", "boolean_label", "ragged", "duplicate_input", "duplicate_view", "shortened_queries"])
def test_invalid_projection_data_publish_nothing(qualified, tmp_path, change):
    root, _, path, _, execution = qualified
    episode = execution["episodes"][0]
    if change == "boolean_input":
        episode["test"][0]["input"][0][0] = True
    elif change == "boolean_label":
        episode["test"][0]["output"][0][0] = False
    elif change == "ragged":
        episode["train"][0]["input"].append([1])
    elif change == "duplicate_input":
        episode["test"][0]["input"] = deepcopy(episode["train"][0]["input"])
    elif change == "duplicate_view":
        execution["episodes"][1]["train"] = deepcopy(episode["train"])
        execution["episodes"][1]["test"] = deepcopy(episode["test"])
    else:
        episode["test"].pop()
        qualified[3]["jobs"][0]["queries"] = 3
        execution["checks"][0]["label_count"] = 6
    rewrite_receipts(qualified)
    output = tmp_path / "rejected"
    with pytest.raises(ValueError):
        EXPORTER.export_qualified(path, output, library=root)
    assert not output.exists()


def test_source_edit_during_serialization_prevents_publication(qualified, tmp_path, monkeypatch):
    root, source, path, _, _ = qualified
    original = EXPORTER.public_view_bytes

    def changed(episode, query_index=0):
        result = original(episode, query_index)
        source.write_text("# changed during serialization\n")
        return result

    monkeypatch.setattr(EXPORTER, "public_view_bytes", changed)
    output = tmp_path / "rejected"
    with pytest.raises(ValueError, match="source|contract|current/ready"):
        EXPORTER.export_qualified(path, output, library=root)
    assert not output.exists()


def test_existing_output_is_preserved(qualified, tmp_path):
    root, _, path, _, _ = qualified
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_bytes(b"unchanged")
    with pytest.raises(FileExistsError):
        EXPORTER.export_qualified(path, output, library=root)
    assert sentinel.read_bytes() == b"unchanged"


@pytest.mark.parametrize("change", ["public_bytes", "public_extra", "public_directory", "manifest_order", "source"])
def test_saved_bundle_verifier_rejects_tampering(qualified, tmp_path, change):
    root, source, path, _, _ = qualified
    output = tmp_path / "export"
    EXPORTER.export_qualified(path, output, library=root)
    if change == "public_bytes":
        first = next((output / "public").glob("*.json"))
        first.write_bytes(first.read_bytes() + b" ")
    elif change == "public_extra":
        (output / "public/leak.json").write_bytes(b'{"seed": 17}')
    elif change == "public_directory":
        (output / "public/seed-17").mkdir()
    elif change == "manifest_order":
        manifest = output / "private/manifest.json"
        value = json.loads(manifest.read_bytes())
        value["episodes"][0]["view_ids"].reverse()
        manifest.write_bytes(raw(value))
    else:
        source.write_text("# source changed after export\n")
    with pytest.raises(ValueError):
        EXPORTER.verify_export(output, library=root)


@pytest.mark.parametrize('change', ['empty', 'missing_setting', 'one_seed', 'duplicate_seed', 'boolean_seed', 'semantic_veto'])
def test_incomplete_or_invalid_qualification_is_not_a_preview(qualified, tmp_path, change):
    root, _, path, q, execution = qualified
    if change == 'semantic_veto':
        catalog = root / 'catalog/puzzles.jsonl'
        rows = [json.loads(line) for line in catalog.read_text().splitlines()]
        rows[0]['semantic_veto'] = True
        catalog.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    else:
        indices = {'empty': [], 'missing_setting': [0, 1], 'one_seed': [0, 2]}.get(change, [0, 1, 2, 3])
        q['jobs'] = [q['jobs'][i] for i in indices]
        for key in ('episodes', 'checks'):
            execution[key] = [execution[key][i] for i in indices]
        if change == 'duplicate_seed':
            q['jobs'][1]['seed'] = execution['episodes'][1]['seed'] = 0
        if change == 'boolean_seed':
            q['jobs'][0]['seed'] = execution['episodes'][0]['seed'] = False
        q['programs'] = native._check_execution(execution, q['jobs'], q['source_binding'], q['contract'])
        rewrite_receipts(qualified)
    with pytest.raises(ValueError):
        EXPORTER.export_qualified(path, tmp_path / 'rejected', library=root)
    assert not (tmp_path / 'rejected').exists()


def test_relocated_packet_routes_export_and_verify_without_ambient_imports(qualified, tmp_path):
    import os
    import shutil
    import subprocess
    import sys
    from arcpuzzles import Catalog

    root, _, path, q, execution = qualified
    outer = tmp_path / 'relocated-packet'
    work = outer / 'WORK'
    repo = work / 'repo'
    shutil.copytree(root, repo)
    shutil.copytree(HOME / 'src', repo / 'src', ignore=shutil.ignore_patterns('__pycache__'))
    (repo / 'shared/runtime').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HOME / 'shared/runtime/reviewer_support.py', repo / 'shared/runtime/reviewer_support.py')
    shutil.copyfile(HOME / 'src/arcpuzzles/review_full_packet_files/preview_public.py', work / 'preview_public.py')
    shutil.copyfile(HOME / 'src/arcpuzzles/review_workspace_files/review.py', outer / 'review.py')
    (outer / 'START-HERE.md').write_text('fixture\n')
    (work / 'PACKET-MANIFEST.json').write_text(json.dumps({'layout': {'workspace': 'WORK', 'entry_files': {
        name: sha((outer / name).read_bytes()) for name in ('START-HERE.md', 'review.py')}}}, sort_keys=True, ensure_ascii=False, separators=(',', ':')))
    checks = work / 'checks/qualified'
    checks.mkdir(parents=True)
    q['source_binding'] = native._ready(Catalog(repo), TASK_ID)[1]
    (checks / 'qualification.json').write_bytes(raw(q))
    (checks / 'execution.json').write_bytes(raw(execution))
    env = dict(os.environ, PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH', None)
    for command in [
        ['--help'],
        ['export', '--qualification', '../checks/qualified/qualification.json', '--out', '../checks/preview'],
        ['verify', '--bundle', '../checks/preview'],
    ]:
        result = subprocess.run([sys.executable, str(outer / 'review.py'), 'preview-public', *command],
                                cwd=tmp_path, env=env, capture_output=True, text=True, timeout=20)
        assert result.returncode == 0, result.stderr
        if command != ['--help']:
            assert json.loads(result.stdout)['views'] == 16
    assert len(list((work / 'checks/preview/public').glob('*.json'))) == 16
    assert not (repo / 'checks').exists()


def test_supported_query_count_is_not_hardcoded_to_four(qualified, tmp_path):
    root, _, path, q, execution = qualified
    for job, episode, check in zip(q['jobs'], execution['episodes'], execution['checks']):
        grid = [[job['seed'] // 10, job['seed'] % 10, 7, 9]]
        output = grid if job['settings']['side'] == 'left' else [list(reversed(grid[0]))]
        episode['test'].append({'input': grid, 'output': output})
        job['queries'] = 5
        check['label_count'] = 8
    execution['racket_evaluations'] = 32
    rewrite_receipts(qualified)
    result = EXPORTER.export_qualified(path, tmp_path / 'five-queries', library=root)
    assert result['views'] == 20


def test_preview_retains_raw_receipts_and_random_order_answer_mapping(qualified, tmp_path):
    root, _, path, _, execution = qualified
    output = tmp_path / 'random-order'
    EXPORTER.export_qualified(path, output, library=root, presentation_seed=19)
    manifest = json.loads((output / 'private/manifest.json').read_bytes())
    assert manifest['schema'] == 'arcpuzzles-qualified-sequential-projection-v2'
    assert manifest['presentation_seed'] == 19
    assert (output / 'private/execution.json').read_bytes() == path.with_name('execution.json').read_bytes()
    for mapping, episode in zip(manifest['episodes'], execution['episodes']):
        assert sorted(mapping['source_indices']) == [0, 1, 2, 3]
        for index, identifier in zip(mapping['source_indices'], mapping['view_ids']):
            assert (output / 'public' / f'{identifier}.json').read_bytes() == EXPORTER.public_view_bytes(episode, index)
    assert any(row['source_indices'] != [0, 1, 2, 3] for row in manifest['episodes'])
    assert EXPORTER.verify_export(output, library=root)['views'] == 16


def test_legacy_source_order_preview_still_verifies(qualified, tmp_path):
    root, _, path, _, _ = qualified
    values = EXPORTER._read_qualification(root, path)
    views, manifest = EXPORTER._projection(*values, schema=EXPORTER.LEGACY_SCHEMA)
    output = tmp_path / 'legacy'
    (output / 'public').mkdir(parents=True)
    (output / 'private').mkdir()
    for identifier, payload in views.items():
        (output / 'public' / f'{identifier}.json').write_bytes(payload)
    (output / 'private/qualification.json').write_bytes(values[2])
    (output / 'private/execution.json').write_bytes(values[3])
    (output / 'private/manifest.json').write_bytes(EXPORTER._raw(manifest))
    assert EXPORTER.verify_export(output, library=root)['views'] == 16
