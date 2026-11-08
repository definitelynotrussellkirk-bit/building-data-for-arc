"""A real Ctrl-C must stop the command without losing an already written response."""
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import zipfile

BASE = Path(__file__).resolve().parent
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, "w") as archive:
    archive.writestr(zipfile.ZipInfo("signal-fixture.txt", (2020, 1, 1, 0, 0, 0)),
                     "Synthetic response written before an interrupt.")
expected = buffer.getvalue()
with tempfile.TemporaryDirectory(prefix="signal-test-", dir=BASE) as temporary:
    root = Path(temporary)
    packet = root / "packet.zip"
    with zipfile.ZipFile(packet, "w") as archive:
        archive.writestr("expected.bin", expected)
    mountpoint, output = root / "mount", root / "output"
    mountpoint.mkdir()
    output.mkdir()
    payload = ("from pathlib import Path; import signal; "
               "Path('review_response_signal.zip').write_bytes(Path('expected.bin').read_bytes()); "
               "print('SIGNAL_READY', flush=True); signal.pause()")
    command = [sys.executable, str(BASE / "packet_tmpfs.py"), str(packet),
               "--mountpoint", str(mountpoint), "--output-dir", str(output),
               "--", sys.executable, "-c", payload]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True,
                               env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        ready = process.stdout.readline()
        assert ready == "SIGNAL_READY\n", ready
        os.killpg(process.pid, signal.SIGINT)
        stdout, stderr = process.communicate(timeout=15)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
    stem = os.environ.get("SIGNAL_LOG_STEM", "integration-signal")
    (BASE / f"{stem}.stdout.log").write_text(ready + stdout)
    (BASE / f"{stem}.stderr.log").write_text(stderr)
    with (BASE / "verification_commands.jsonl").open("a") as log:
        log.write(json.dumps({"phase": stem, "argv": command,
                              "signal": "SIGINT sent to this test's new process group after SIGNAL_READY",
                              "exit_code": process.returncode}) + "\n")
    exported = output / "review_response_signal.zip"
    assert exported.is_file(), "Ctrl-C lost the already generated response before export"
    assert exported.read_bytes() == expected
    assert process.returncode == 130, process.returncode
    assert list(mountpoint.iterdir()) == []
    print(json.dumps({"case": "integration-sigint", "verified": True,
                      "command_exit_code": process.returncode,
                      "exported_bytes_verified": True}))
