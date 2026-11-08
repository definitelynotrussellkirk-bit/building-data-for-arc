"""Regression tests for archive identity, explicit omissions, and disk precedence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "workspace/zip_backed_package.py"
TASK = "613be474907a"
HOME = f"repo/generators/{TASK}/"
COLD = "repo/shared/cold.py"
WARM = "repo/shared/helper.py"
CANONICAL = "repo/shared/data/canonical/puzzles.jsonl"
INDEX = "checks/archive-package/index.json"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


@pytest.fixture
def utility():
    assert SOURCE.is_file(), "ZIP-backed packaging utility is not implemented"
    spec = importlib.util.spec_from_file_location("zip_backed_package", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def packet(tmp_path):
    outer = tmp_path / "outer"
    work = outer / "WORK"
    files = {HOME + "generator.py": b"# selected source\n",
             HOME + "workspace/README.md": b"task notes\n",
             CANONICAL: b"{}\n", WARM: b"helper = 7\n",
             COLD: b"exact archived bytes: \x00\xff\r\n",
             "repo/src/frozen.py": b"native_version = 1\n",
             "repo/src/arcpuzzles/review_full_return.py": b"# fixture native marker\n",
             "PARAMETRIC-RULES.md": b"issued authority\n"}
    manifest = {"files": {name: digest(raw) for name, raw in files.items()},
                "layout": {"workspace": "WORK", "entry_files": {
                    "START-HERE.md": digest(b"start"), "review.py": digest(b"# launcher")}}}
    manifest_raw = encoded(manifest)
    baseline = {name: digest(raw) for name, raw in files.items()
                if name.startswith(HOME) or name == CANONICAL}
    contract = {"task_id": TASK, "packet_id": digest(manifest_raw),
                "baseline_sha256": baseline}
    for name, raw in {**files, "PACKET-MANIFEST.json": manifest_raw,
                      "ASSIGNMENT.json": encoded(contract)}.items():
        if name != COLD:
            target = work / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    for name in baseline:
        target = work / ".review/baseline" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(files[name])
    archive = tmp_path / "issued.zip"
    with zipfile.ZipFile(archive, "x") as z:
        for name, raw in files.items():
            z.writestr("WORK/" + name, raw)
        z.writestr("WORK/PACKET-MANIFEST.json", manifest_raw)
        z.writestr("START-HERE.md", b"start")
        z.writestr("review.py", b"# launcher")
    return archive, outer, work


def initialize(utility, packet):
    archive, outer, work = packet
    with utility.archive_view(archive, outer, initialize=True):
        pass
    return digest((work / INDEX).read_bytes())


def native_builder():
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
    from arcpuzzles.review_full_return import build_full_return
    return build_full_return


def test_missing_source_reads_exact_archive_without_changing_disk(utility, packet):
    archive, outer, work = packet
    token = initialize(utility, packet)
    with utility.archive_view(archive, outer, index_sha256=token) as view:
        assert (view / COLD).is_file()
        assert (view / COLD).read_bytes() == b"exact archived bytes: \x00\xff\r\n"
        assert not (work / COLD).is_file()
        assert not (view / "repo/unknown.py").is_file()
        with pytest.raises(FileNotFoundError):
            (view / "repo/unknown.py").read_bytes()


@pytest.mark.parametrize("name", [WARM, COLD, "repo/src/frozen.py", "PARAMETRIC-RULES.md"])
def test_present_changed_source_cannot_be_hidden_by_archive(utility, packet, name):
    archive, outer, work = packet
    token = initialize(utility, packet)
    (work / name).write_bytes(b"tampered present source")
    with pytest.raises(ValueError):
        with utility.archive_view(archive, outer, index_sha256=token):
            pass


@pytest.mark.parametrize("name", [WARM, HOME + "generator.py", HOME + "workspace/README.md", CANONICAL])
def test_later_deletion_is_not_authorized_as_an_omission(utility, packet, name):
    archive, outer, work = packet
    token = initialize(utility, packet)
    (work / name).unlink()
    with pytest.raises(ValueError):
        with utility.archive_view(archive, outer, index_sha256=token):
            pass


def test_changed_selected_source_is_read_from_disk(utility, packet):
    archive, outer, work = packet
    token = initialize(utility, packet)
    (work / (HOME + "generator.py")).write_bytes(b"# legitimate proposed edit\n")
    with utility.archive_view(archive, outer, index_sha256=token) as view:
        assert (view / (HOME + "generator.py")).read_bytes() == b"# legitimate proposed edit\n"


@pytest.mark.parametrize("mutation", ["delete", "change"])
def test_baseline_must_remain_physical_and_hash_bound(utility, packet, mutation):
    archive, outer, work = packet
    token = initialize(utility, packet)
    baseline = work / ".review/baseline" / (HOME + "generator.py")
    baseline.unlink() if mutation == "delete" else baseline.write_bytes(b"wrong baseline")
    with pytest.raises(ValueError):
        with utility.archive_view(archive, outer, index_sha256=token):
            pass


def test_archive_replacement_is_rejected(utility, packet):
    archive, outer, work = packet
    token = initialize(utility, packet)
    with archive.open("ab") as stream:
        stream.write(b"changed archive identity")
    with pytest.raises(ValueError):
        with utility.archive_view(archive, outer, index_sha256=token):
            pass


def test_bootstrap_verifies_every_issued_member_hash(utility, packet):
    archive, outer, work = packet
    with zipfile.ZipFile(archive) as z:
        payload = {info.filename: z.read(info) for info in z.infolist()}
    payload["WORK/" + COLD] = b"corrupted omitted source"
    with zipfile.ZipFile(archive, "w") as z:
        for name, raw in payload.items():
            z.writestr(name, raw)
    with pytest.raises(ValueError):
        initialize(utility, packet)
    assert not (work / INDEX).exists()


def test_edited_inventory_cannot_authorize_a_later_deletion(utility, packet):
    archive, outer, work = packet
    token = initialize(utility, packet)
    index = work / INDEX
    data = json.loads(index.read_text())
    data["fallback"].append(WARM)
    index.chmod(0o644)
    index.write_bytes(encoded(data))
    (work / WARM).unlink()
    with pytest.raises(ValueError):
        with utility.archive_view(archive, outer, index_sha256=token):
            pass


@pytest.mark.parametrize("name", [COLD, WARM])
def test_symlink_never_gets_fallback(utility, packet, name):
    archive, outer, work = packet
    token = initialize(utility, packet)
    target = work / name
    if target.exists():
        target.unlink()
    target.symlink_to(work / "absent-destination")
    with pytest.raises(ValueError):
        with utility.archive_view(archive, outer, index_sha256=token):
            pass


def test_assignment_changes_are_rejected(utility, packet):
    archive, outer, work = packet
    token = initialize(utility, packet)
    path = work / "ASSIGNMENT.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError):
        with utility.archive_view(archive, outer, index_sha256=token):
            pass


def test_native_builder_detects_existing_extra_source(utility, packet):
    archive, outer, work = packet
    token = initialize(utility, packet)
    (work / "repo/undeclared.py").write_bytes(b"extra source")
    with utility.archive_view(archive, outer, index_sha256=token) as view:
        with pytest.raises(ValueError, match="Undeclared new source"):
            native_builder()(view, work / "return.zip")
    assert not (work / "return.zip").exists()


def test_native_builder_checks_omitted_source_and_reaches_required_docs(utility, packet):
    archive, outer, work = packet
    token = initialize(utility, packet)
    with utility.archive_view(archive, outer, index_sha256=token) as view:
        with pytest.raises(ValueError, match="Missing review document: REVIEW.md"):
            native_builder()(view, work / "return.zip")
    assert not (work / "return.zip").exists()


@pytest.mark.parametrize("name", [WARM, COLD])
def test_native_builder_sees_present_tampering_after_view_open(utility, packet, name):
    archive, outer, work = packet
    token = initialize(utility, packet)
    with utility.archive_view(archive, outer, index_sha256=token) as view:
        (work / name).write_bytes(b"tampered after preflight")
        with pytest.raises(ValueError, match="Changed or missing shared packet source"):
            native_builder()(view, work / "return.zip")


@pytest.mark.parametrize("name", [WARM, HOME + "generator.py"])
def test_native_builder_sees_materialized_deletion_after_view_open(utility, packet, name):
    archive, outer, work = packet
    token = initialize(utility, packet)
    with utility.archive_view(archive, outer, index_sha256=token) as view:
        (work / name).unlink()
        with pytest.raises(ValueError, match="Changed.*source"):
            native_builder()(view, work / "return.zip")


@pytest.mark.parametrize("name", ["START-HERE.md", "review.py"])
def test_bootstrap_verifies_layout_entry_hashes(utility, packet, name):
    archive, outer, work = packet
    with zipfile.ZipFile(archive) as z:
        payload = {info.filename: z.read(info) for info in z.infolist()}
    payload[name] = b"changed entrypoint"
    with zipfile.ZipFile(archive, "w") as z:
        for member, raw in payload.items():
            z.writestr(member, raw)
    with pytest.raises(ValueError, match="entry.*hash mismatch"):
        initialize(utility, packet)


def test_cli_refuses_native_module_loaded_from_another_checkout(utility, packet, monkeypatch):
    archive, outer, work = packet
    token = initialize(utility, packet)
    native_builder()  # Load the real native validator from this test checkout.
    monkeypatch.setattr(sys, "argv", ["zip_backed_package.py", "--archive", str(archive),
                         "--workspace", str(outer), "--index-sha256", token,
                         "--out", str(work / "return.zip")])
    with pytest.raises(ValueError, match="Native validator import.*local"):
        utility.main()
    assert not (work / "return.zip").exists()
