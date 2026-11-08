import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_packet import build_full_packet
import arcpuzzles.review_full_packet as full_packet


def _questions(root):
    folder = root / "REVIEW/questions"
    folder.mkdir(parents=True)
    for name in ("generator-shortcuts", "qwen9-data-value"):
        (folder / f"{name}.json").write_text(json.dumps({
            "schema": "arcpuzzles-review-question-v1", "id": name,
            "version": 1, "owner": "ARCpuzzles", "text": name,
        }))


def test_full_packet_inventory_and_manifest(library, tmp_path):
    _questions(library)
    home = library / "generators/aaaa00000003"
    (home / "notes.md").write_text("why these inputs\n")
    (home / "workspace").mkdir()
    (home / "workspace/probe.py").write_text("print('probe')\n")
    (library / "README.md").write_text("portable fixture\n")
    (library / "REVIEW/README.md").write_text("review guide\n")
    contract = library / 'docs/SEMANTIC_GATE_CONTRACT.md'
    contract.parent.mkdir(exist_ok=True)
    contract.write_text('semantic hook contract\n')
    first = build_full_packet(Catalog(library), library / "REVIEW", tmp_path / "one.zip")
    second = build_full_packet(Catalog(library), library / "REVIEW", tmp_path / "two.zip")
    assert first["packet_id"] == second["packet_id"]
    assert first["generator_count"] == 3
    assert first["eligible_count"] == 3
    with zipfile.ZipFile(first["zip"]) as archive:
        manifest = json.loads(archive.read("PACKET-MANIFEST.json"))
        assert manifest["schema"] == "arcpuzzles-full-packet-v2"
        assert manifest["all_ids"] == ["aaaa00000001", "aaaa00000002", "aaaa00000003"]
        assert manifest["main_ids"] == manifest["all_ids"]
        assert "repo/generators/aaaa00000003/notes.md" in archive.namelist()
        assert "repo/generators/aaaa00000003/workspace/probe.py" in archive.namelist()
        assert archive.read("repo/REVIEW/README.md") == b"review guide\n"
        assert archive.read('repo/docs/SEMANTIC_GATE_CONTRACT.md') == b'semantic hook contract\n'
        assert {q["id"] for q in manifest["questions"]} == {"generator-shortcuts", "qwen9-data-value"}
        for path, digest in manifest["files"].items():
            assert hashlib.sha256(archive.read(path)).hexdigest() == digest


def test_pack_full_rejects_missing_source(library, tmp_path):
    _questions(library)
    (library / "generators/aaaa00000003/generator.py").unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        build_full_packet(Catalog(library), library / "REVIEW", tmp_path / "bad.zip")
    assert not (tmp_path / "bad.zip").exists()


def test_packet_keeps_exact_cited_compressed_witness_and_rejects_drift(library, tmp_path):
    _questions(library)
    folder = library / 'generators/aaaa00000003/counterexamples/finding'
    folder.mkdir(parents=True)
    witness = folder / 'counterexample.zip'
    witness.write_bytes(b'exact cited compressed evidence')
    relative = witness.relative_to(library).as_posix()
    (folder / 'audit_assets.json').write_text(json.dumps({'files':[
        {'path':relative, 'sha256':hashlib.sha256(witness.read_bytes()).hexdigest()}]}))
    built = build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'witness.zip')
    with zipfile.ZipFile(built['zip']) as packet:
        assert packet.read('repo/' + relative) == witness.read_bytes()
    witness.write_bytes(b'changed')
    with pytest.raises(ValueError, match='changed retained witness'):
        build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'drift.zip')


def test_pack_full_rejects_missing_mapped_runtime_helper(library, tmp_path):
    _questions(library)
    mapping = library / "catalog/runtime_files.json"
    rows = json.loads(mapping.read_text())
    rows.append({"path": "shared/tools/missing.py", "target": "scripts/missing.py"})
    mapping.write_text(json.dumps(rows))
    with pytest.raises(FileNotFoundError, match="runtime"):
        build_full_packet(Catalog(library), library / "REVIEW", tmp_path / "bad.zip")


def test_packet_omits_private_and_generated_paths(library, tmp_path):
    _questions(library)
    for path in (".git/config", "var/review/log.txt", "secrets/key.txt",
                 "generators/aaaa00000003/__pycache__/private.pyc"):
        target = library / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("private")
    result = build_full_packet(Catalog(library), library / "REVIEW", tmp_path / "safe.zip")
    with zipfile.ZipFile(result["zip"]) as archive:
        names = archive.namelist()
        assert not any(part in name for name in names for part in (".git/", "var/", "secrets/", "__pycache__/"))


def test_pack_full_rejects_task_index_with_wrong_identity(library, tmp_path):
    _questions(library)
    indexes = library / "REVIEW/task_indexes"
    indexes.mkdir()
    (indexes / "aaaa00000003.json").write_text(json.dumps({"schema": "arcpuzzles-task-review-index-v2",
        "task_id": "aaaa00000002", "decisions": [], "audits": []}))
    with pytest.raises(ValueError, match="task index"):
        build_full_packet(Catalog(library), library / "REVIEW", tmp_path / "bad.zip")


def test_full_packet_can_embed_a_hash_pinned_offline_racket_archive(library, tmp_path, monkeypatch):
    _questions(library)
    archive = tmp_path / full_packet.RACKET_ARCHIVE_NAME
    archive.write_bytes(b"fixture Racket archive")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    monkeypatch.setattr(full_packet, "RACKET_ARCHIVE_SHA256", digest)

    built = build_full_packet(Catalog(library), library / "REVIEW", tmp_path / "kit.zip",
                              racket_archive=archive)

    with zipfile.ZipFile(built["zip"]) as packet:
        manifest = json.loads(packet.read("PACKET-MANIFEST.json"))
        name = "vendor/" + full_packet.RACKET_ARCHIVE_NAME
        assert packet.read(name) == archive.read_bytes()
        assert manifest["files"][name] == digest
        assert "setup_racket.py" in packet.namelist()
        assert "run_with_racket.py" in packet.namelist()

    archive.write_bytes(b"changed")
    with pytest.raises(ValueError, match="Racket archive SHA-256"):
        build_full_packet(Catalog(library), library / "REVIEW", tmp_path / "bad-kit.zip",
                          racket_archive=archive)


def test_review_packet_omits_retired_resource_guard_even_if_present_in_checkout(library, tmp_path):
    _questions(library)
    helper = library / 'shared/tools/arc_review_guard.py'
    helper.parent.mkdir(parents=True, exist_ok=True)
    helper.write_text('raise RuntimeError("retired guard must not run")\n')
    for name in ('test_review_resource_guard.py', 'test_review_resource_restore.py'):
        retired_test = library / 'tests' / name
        retired_test.parent.mkdir(parents=True, exist_ok=True)
        retired_test.write_text('raise RuntimeError("retired guard test must not ship")\n')
    built = build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'guard.zip', workspace_layout=True)
    with zipfile.ZipFile(built['zip']) as archive:
        manifest = json.loads(archive.read('WORK/PACKET-MANIFEST.json'))
        assert 'resource_guard.py' not in archive.namelist()
        assert 'WORK/repo/shared/tools/arc_review_guard.py' not in archive.namelist()
        assert 'resource_guard.py' not in manifest['layout']['entry_files']
        assert 'repo/shared/tools/arc_review_guard.py' not in manifest['files']
        for name in ('test_review_resource_guard.py', 'test_review_resource_restore.py'):
            assert f'WORK/repo/tests/{name}' not in archive.namelist()
            assert f'repo/tests/{name}' not in manifest['files']
