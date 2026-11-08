"""The review wrapper must run task-local tests from a relocated packet."""
import json
from pathlib import Path
import shutil
import subprocess
import sys


def test_relocated_wrapper_exposes_generator_runtime_and_repo_cwd(tmp_path):
    source = Path(__file__).resolve().parents[1] / "src/arcpuzzles/review_full_packet_files/run_with_racket.py"
    packet = tmp_path / "packet with spaces"
    runtime = packet / "repo/shared/runtime"
    runtime.mkdir(parents=True)
    (runtime / "example_generator_runtime.py").write_text("VALUE = 17\n")
    (packet / "repo/src").mkdir()
    (packet / "setup_racket.py").write_text(
        "from pathlib import Path\ndef ensure_racket(): return Path('/usr/bin/true')\n")
    shutil.copy2(source, packet / "run_with_racket.py")
    code = "import example_generator_runtime,os,json;print(json.dumps([example_generator_runtime.VALUE,os.getcwd()]))"
    result = subprocess.run([sys.executable, str(packet / "run_with_racket.py"), sys.executable, "-c", code],
        cwd=tmp_path, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == [17, str(packet / "repo")]


def test_help_explains_script_paths_without_installing_racket(tmp_path):
    source = Path(__file__).resolve().parents[1] / "src/arcpuzzles/review_full_packet_files/run_with_racket.py"
    shutil.copy2(source, tmp_path / 'run_with_racket.py')
    (tmp_path / 'setup_racket.py').write_text("def ensure_racket(): raise RuntimeError('must not install for help')\n")
    result = subprocess.run([sys.executable, str(tmp_path / 'run_with_racket.py'), '--help'],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert 'generators/TASK/workspace/lesson_probe.py' in result.stdout
    assert 'repo/repo' in result.stdout


def test_wrapper_reports_cwd_and_binds_library_root(tmp_path):
    source = Path(__file__).resolve().parents[1] / "src/arcpuzzles/review_full_packet_files/run_with_racket.py"
    packet = tmp_path / 'packet'; (packet / 'repo').mkdir(parents=True)
    (packet / 'setup_racket.py').write_text("from pathlib import Path\ndef ensure_racket(): return Path('/usr/bin/true')\n")
    shutil.copy2(source, packet / 'run_with_racket.py')
    result = subprocess.run([sys.executable, str(packet / 'run_with_racket.py'), sys.executable,
                            '-c', "import os;print(os.environ['ARCPUZZLES_HOME'])"],
                            cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(packet / 'repo')
    assert 'effective cwd: ' + str(packet / 'repo') in result.stderr
