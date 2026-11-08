"""Manifest-bound check evidence for returns above the member limit."""
import gzip
import io
import json
import tarfile
import zipfile

import pytest

from arcpuzzles import review_evidence_bundle as bundles
from arcpuzzles.cli import main
from arcpuzzles.review_full_return import build_full_return, validate_full_return
from arcpuzzles.review_return import MAX_EXPANDED, MAX_MEMBERS

from test_review_solve import packet  # noqa: E402  (shared fixture packet builder)


def _files(n=3):
    return {f"checks/run/{i:04d}.log": f"stage {i} failed\n".encode() for i in range(n)}


def test_pack_is_deterministic_and_verifies():
    first, second = bundles.pack(_files()), bundles.pack(_files())
    assert first == second
    manifest = bundles.read_manifest(first[bundles.MANIFEST])
    assert manifest["count"] == 3 and manifest["expanded_bytes"] == sum(len(v) for v in _files().values())
    bundles.verify(first[bundles.ARCHIVE], manifest)


def _rebuild(members, manifest_files):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as archive:
        for info, data in members:
            archive.addfile(info, io.BytesIO(data) if data is not None else None)
    archive_bytes = gzip.compress(raw.getvalue(), mtime=0)
    manifest = {"schema": bundles.SCHEMA, "archive": bundles.ARCHIVE,
                "archive_sha256": bundles._sha(archive_bytes), "count": len(manifest_files),
                "expanded_bytes": sum(r["bytes"] for r in manifest_files), "files": manifest_files}
    return archive_bytes, manifest


def _entry(path, data):
    return {"path": path, "bytes": len(data), "sha256": bundles._sha(data)}


def test_tampered_bytes_unlisted_members_links_and_traversal_are_rejected():
    packed = bundles.pack(_files())
    manifest = bundles.read_manifest(packed[bundles.MANIFEST])
    raw = bytearray(packed[bundles.ARCHIVE])
    raw[len(raw) // 2] ^= 0xFF
    with pytest.raises(ValueError, match="archive hash"):
        bundles.verify(bytes(raw), manifest)
    data = b"evidence"
    info = tarfile.TarInfo("checks/a.log"); info.size = len(data)
    extra = tarfile.TarInfo("checks/b.log"); extra.size = len(data)
    archive, listed = _rebuild([(info, data), (extra, data)], [_entry("checks/a.log", data)])
    with pytest.raises(ValueError, match="Unlisted"):
        bundles.verify(archive, listed)
    link = tarfile.TarInfo("checks/a.log"); link.type = tarfile.SYMTYPE; link.linkname = "/etc/passwd"
    archive, listed = _rebuild([(link, None)], [_entry("checks/a.log", b"")])
    with pytest.raises(ValueError, match="regular file"):
        bundles.verify(archive, listed)
    with pytest.raises(ValueError, match="Invalid or repeated"):
        bundles.read_manifest(json.dumps({"schema": bundles.SCHEMA, "archive": bundles.ARCHIVE,
            "archive_sha256": "0" * 64, "count": 1, "expanded_bytes": 1,
            "files": [_entry("checks/../../escape.py", b"x")]}).encode())
    with pytest.raises(ValueError, match="Only checks/"):
        bundles.pack({"solve/attempts/0001/solution.py": b"x"})


def _return_with_checks(library, tmp_path, monkeypatch, count, size=40):
    from arcpuzzles.catalog import Catalog
    from arcpuzzles import review_solve as solves
    root = packet(library, tmp_path)
    monkeypatch.setattr(Catalog, "generate", lambda self, task_id, **o: [{
        "train": [{"input": [[1]], "output": [[2]]}], "test": [{"input": [[3]], "output": [[4]]}],
        "provenance": {"generator_sha256": self.describe(task_id)["generator_sha256"]}}])
    solves.prepare_solve(root)
    (root / "solve/SOLVE_NOTES.md").write_text("notes\n")
    (root / "solve/solution.py").write_text("def solve(g):\n    return [[c + 1 for c in r] for r in g]\n")
    solves.check_solve(root, note="try")
    solves.finish_solve(root, reference_consulted=False, earlier_exposure="yes", reason="done")
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
        (root / name).write_text(name + "\n")
    runs = root / "checks/battery"
    runs.mkdir(parents=True)
    for i in range(count):
        (runs / f"stage-{i:04d}.receipt").write_bytes(b"x" * size)
    (root / "RESULTS.json").write_text(json.dumps({"completion_state": "complete", "verification_commands": [
        {"cwd": "packet_root", "argv": ["python3", "run_with_racket.py", "true"], "exit_code": 1,
         "evidence_paths": ["checks/battery/stage-0007.receipt"]}]}))
    return root


def test_return_above_the_member_limit_is_bundled_and_validates(library, tmp_path, monkeypatch, capsys):
    root = _return_with_checks(library, tmp_path, monkeypatch, MAX_MEMBERS + 20)
    returned = build_full_return(root, tmp_path / "review_response_big.zip")
    assert "Packed" in capsys.readouterr().err
    manifest = json.loads((root / "PACKET-MANIFEST.json").read_text())
    with zipfile.ZipFile(returned["zip"]) as archive:
        names = archive.namelist()
        assert len(names) <= MAX_MEMBERS
        assert not any(name.startswith("checks/") for name in names)
        validate_full_return(archive, manifest)
        intake = json.loads(archive.read("INTAKE.json"))
    assert intake["evidence_bundle"]["count"] == MAX_MEMBERS + 20
    out = tmp_path / "extracted"
    assert main(["review", "evidence-extract", returned["zip"], "--out", str(out)]) == 0
    assert (out / "checks/battery/stage-0007.receipt").read_bytes() == b"x" * 40
    assert main(["review", "evidence-extract", returned["zip"], "--out", str(out)]) == 1  # never overwrite


def test_small_return_keeps_the_legacy_layout(library, tmp_path, monkeypatch):
    root = _return_with_checks(library, tmp_path, monkeypatch, 10)
    returned = build_full_return(root, tmp_path / "review_response_small.zip")
    with zipfile.ZipFile(returned["zip"]) as archive:
        assert "checks/battery/stage-0007.receipt" in archive.namelist()
        assert bundles.ARCHIVE not in archive.namelist()
        assert "evidence_bundle" not in json.loads(archive.read("INTAKE.json"))


def test_bundle_counts_at_its_expanded_size(library, tmp_path, monkeypatch):
    # Highly compressible bytes must not slip past the expanded-size limit inside a tar.gz.
    root = _return_with_checks(library, tmp_path, monkeypatch, 300, size=MAX_EXPANDED // 250)
    with pytest.raises(ValueError, match="expanded_bytes"):
        build_full_return(root, tmp_path / "review_response_bomb.zip")


def test_verify_and_extract_refuse_oversize_nested_evidence(tmp_path):
    files = {'checks/huge.log': b'x' * (MAX_EXPANDED + 1)}
    packed = bundles.pack(files)
    manifest = bundles.read_manifest(packed[bundles.MANIFEST])
    with pytest.raises(ValueError, match='expanded_bytes'):
        bundles.verify(packed[bundles.ARCHIVE], manifest)
    zip_path = tmp_path / 'return.zip'
    with zipfile.ZipFile(zip_path, 'w') as archive:
        for name, raw in packed.items():
            archive.writestr(name, raw)
    with pytest.raises(ValueError, match='expanded_bytes'):
        bundles.extract_from_return(zip_path, tmp_path / 'out')
    assert not (tmp_path / 'out/checks/huge.log').exists()


def test_extract_rejects_symlink_parent(tmp_path):
    packed = bundles.pack({'checks/a.log': b'evidence'})
    manifest = bundles.read_manifest(packed[bundles.MANIFEST])
    out = tmp_path / 'out'
    out.mkdir()
    (out / 'actual').mkdir()
    (out / 'checks').symlink_to(out / 'actual', target_is_directory=True)
    with pytest.raises(ValueError, match='Symlink'):
        bundles.verify(packed[bundles.ARCHIVE], manifest, extract_to=out)
    assert not (out / 'actual/a.log').exists()


def test_malformed_pax_header_cannot_expand_past_tar_storage_budget():
    info = tarfile.TarInfo('pax-header')
    info.type = tarfile.XHDTYPE
    info.size = 100000
    archive_bytes = gzip.compress(info.tobuf() + b'x' * info.size + b'\0' * 1024, mtime=0)
    manifest = {'schema': bundles.SCHEMA, 'archive': bundles.ARCHIVE,
                'archive_sha256': bundles._sha(archive_bytes), 'count': 1, 'expanded_bytes': 0,
                'files': [_entry('checks/a.log', b'')]}
    with pytest.raises(ValueError, match='decompression'):
        bundles.verify(archive_bytes, manifest)


def test_nested_and_outer_bytes_share_one_extraction_budget(tmp_path):
    packed = bundles.pack({'checks/near-limit.log': b'x' * (MAX_EXPANDED - 512 * 1024)})
    path = tmp_path / 'return.zip'
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in packed.items():
            archive.writestr(name, raw)
        archive.writestr('other.log', b'y' * (1024 * 1024))
    with pytest.raises(ValueError, match='expanded_bytes'):
        bundles.extract_from_return(path, tmp_path / 'out')
    assert not (tmp_path / 'out').exists()


def test_extract_does_not_create_directory_through_symlink_ancestor(tmp_path):
    packed = bundles.pack({'checks/a.log': b'evidence'})
    path = tmp_path / 'return.zip'
    with zipfile.ZipFile(path, 'w') as archive:
        for name, raw in packed.items():
            archive.writestr(name, raw)
    actual = tmp_path / 'actual'
    actual.mkdir()
    link = tmp_path / 'link'
    link.symlink_to(actual, target_is_directory=True)
    with pytest.raises(ValueError, match='Symlink'):
        bundles.extract_from_return(path, link / 'new-output')
    assert not (actual / 'new-output').exists()
