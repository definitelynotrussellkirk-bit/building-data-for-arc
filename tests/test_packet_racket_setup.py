"""Host-runtime selection must not require the Linux bundle on another platform."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def setup(tmp_path, monkeypatch):
    source = (Path(__file__).resolve().parents[1]
              / "src/arcpuzzles/review_full_packet_files/setup_racket.py")
    spec = importlib.util.spec_from_file_location("packet_racket_setup", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    packet = tmp_path / "packet with spaces"
    (packet / "vendor").mkdir(parents=True)
    monkeypatch.setattr(module, "ROOT", packet)
    return module


@pytest.mark.parametrize("system,machine", [("Darwin", "arm64"), ("Linux", "aarch64")])
def test_unsupported_bundle_platform_uses_and_probes_system_racket(setup, monkeypatch,
                                                                 system, machine):
    (setup.ROOT / "vendor" / setup.ARCHIVE).write_bytes(b"not a host-compatible archive")
    binary = setup.ROOT / "system bin" / "racket"
    monkeypatch.setattr(setup.platform, "system", lambda: system)
    monkeypatch.setattr(setup.platform, "machine", lambda: machine)
    monkeypatch.setattr(setup.shutil, "which", lambda name: str(binary) if name == "racket" else None)
    monkeypatch.setattr(setup, "_digest", lambda path: pytest.fail("must not inspect incompatible bundle"))
    probes = []

    def run(argv, **options):
        probes.append((argv, options))
        return SimpleNamespace(returncode=0, stdout="RACKET_READY\n", stderr="")

    monkeypatch.setattr(setup.subprocess, "run", run)
    assert setup.ensure_racket() == binary.resolve()
    assert len(probes) == 1
    assert probes[0][0][0] == str(binary.resolve())
    assert probes[0][0][1] == "-e"
    assert probes[0][1]["timeout"] == 20


@pytest.mark.parametrize("machine", ["x86_64", "AMD64"])
def test_supported_linux_still_rejects_bundle_hash_mismatch(setup, monkeypatch, machine):
    (setup.ROOT / "vendor" / setup.ARCHIVE).write_bytes(b"corrupt archive")
    (setup.ROOT / "PACKET-MANIFEST.json").write_text(json.dumps({
        "files": {"vendor/" + setup.ARCHIVE: setup.UPSTREAM_SHA256}}))
    monkeypatch.setattr(setup.platform, "system", lambda: "Linux")
    monkeypatch.setattr(setup.platform, "machine", lambda: machine)
    monkeypatch.setattr(setup.shutil, "which", lambda name: pytest.fail("must verify supported bundle"))
    with pytest.raises(RuntimeError, match="manifest/upstream SHA-256"):
        setup.ensure_racket()
    assert not (setup.ROOT / ".review").exists()


@pytest.mark.parametrize("archive_present", [False, True])
def test_missing_usable_runtime_reports_clear_error(setup, monkeypatch, archive_present):
    if archive_present:
        (setup.ROOT / "vendor" / setup.ARCHIVE).write_bytes(b"incompatible bundle")
    monkeypatch.setattr(setup.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(setup.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="system racket.*available"):
        setup.ensure_racket()


def test_system_runtime_must_pass_probe_on_unsupported_platform(setup, monkeypatch):
    (setup.ROOT / "vendor" / setup.ARCHIVE).write_bytes(b"incompatible bundle")
    monkeypatch.setattr(setup.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(setup.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(setup.shutil, "which", lambda name: str(setup.ROOT / "racket"))
    monkeypatch.setattr(setup.subprocess, "run", lambda *args, **kwargs:
                        SimpleNamespace(returncode=1, stdout="", stderr="unusable runtime"))
    with pytest.raises(RuntimeError, match="Racket probe failed: unusable runtime"):
        setup.ensure_racket()


def test_system_runtime_remains_supported_when_bundle_absent(setup, monkeypatch):
    binary = setup.ROOT / "racket"
    monkeypatch.setattr(setup.platform, "system", lambda: "Linux")
    monkeypatch.setattr(setup.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(setup.shutil, "which", lambda name: str(binary))
    monkeypatch.setattr(setup.subprocess, "run", lambda *args, **kwargs:
                        SimpleNamespace(returncode=0, stdout="RACKET_READY\n", stderr=""))
    assert setup.ensure_racket() == binary.resolve()
