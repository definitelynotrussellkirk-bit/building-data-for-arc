"""Real private-namespace smoke test using a tiny synthetic packet only."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

BASE = Path(__file__).resolve().parent
HELPER = BASE / "packet_tmpfs.py"


def zip_bytes(entries):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in entries:
            archive.writestr(zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0)), data)
    return buffer.getvalue()


expected = zip_bytes([("fixture.txt", b"Synthetic response; not an official ARCpuzzles return.\n")])
fixture_code = """from pathlib import Path
import hashlib, json, os, sys, tempfile
root = Path.cwd()
assert Path(os.environ['TMPDIR']).parent == root
assert Path(tempfile.gettempdir()).parent == root
assert os.environ['TMP'] == os.environ['TEMP'] == os.environ['TMPDIR']
output = root / 'WORK/review_response_fixture.zip'
output.write_bytes((root / 'expected-response.bin').read_bytes())
print(json.dumps({'private_tmpdir_verified': True, 'fixture_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))
raise SystemExit(int(os.environ.get('FIXTURE_EXIT', '0')))
"""
with tempfile.TemporaryDirectory(prefix="integration-", dir=BASE) as temporary:
    root = Path(temporary)
    packet = root / "synthetic-packet.zip"
    packet_bytes = zip_bytes([
        ("expected-response.bin", expected), ("fixture_command.py", fixture_code),
        ("WORK/review_response_supplied.zip", expected), ("unrelated.zip", expected),
    ])
    packet.write_bytes(packet_bytes)
    mountpoint = root / "mount"
    mountpoint.mkdir()
    for number, label, payload, status in (
        (3, "integration-success", [sys.executable, "fixture_command.py"], 0),
        (4, "integration-no-output", [sys.executable, "-c", "print('Synthetic no-output command')"], 0),
        (5, "integration-command-failure", [sys.executable, "fixture_command.py"], 7),
    ):
        output = root / label
        output.mkdir()
        command = [sys.executable, str(HELPER), str(packet), "--mountpoint", str(mountpoint),
                   "--output-dir", str(output), "--", *payload]
        result = subprocess.run(command, capture_output=True, text=True,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "FIXTURE_EXIT": str(status)})
        stem = f"{number:02d}-{label}"
        (BASE / f"{stem}.stdout.log").write_text(result.stdout)
        (BASE / f"{stem}.stderr.log").write_text(result.stderr)
        with (BASE / "verification_commands.jsonl").open("a") as log:
            log.write(json.dumps({"phase": label, "argv": command, "exit_code": result.returncode,
                                  "environment_overrides": {"FIXTURE_EXIT": str(status),
                                  "PYTHONDONTWRITEBYTECODE": "1"}}) + "\n")
        assert result.returncode == status, (label, result.returncode, result.stderr)
        summary = json.loads(result.stdout.splitlines()[-1])
        actual = sorted(p.name for p in output.iterdir())
        if label == "integration-no-output":
            assert actual == [], actual
            assert summary["status"] == "no_response_zips_generated", summary
        else:
            assert actual == ["review_response_fixture.zip"], actual
            assert (output / actual[0]).read_bytes() == expected
            assert summary["command_exit_code"] == status, summary
        assert list(mountpoint.iterdir()) == [], "Private mount leaked into the parent namespace"
        assert not os.path.ismount(mountpoint)
        assert packet.read_bytes() == packet_bytes, "Synthetic input was modified"
        print(json.dumps({"case": label, "verified": True, "command_exit_code": result.returncode,
                          "exported": actual, "source_unchanged": True,
                          "fixture_sha256": hashlib.sha256(expected).hexdigest()}))
