import importlib.util
from pathlib import Path
import subprocess
from unittest.mock import patch
import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'src/arcpuzzles/review_full_packet_files/setup_racket.py'

def probe():
    spec = importlib.util.spec_from_file_location('review_racket_probe', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize('status,output,expected', [
    (-9, '', 'returncode=-9, signal=SIGKILL'),
    (137, '', 'returncode=137'),
    (0, 'wrong', 'returncode=0'),
])
def test_failure_reports_actual_status(status, output, expected):
    module = probe()
    with patch.object(module.subprocess, 'run', return_value=subprocess.CompletedProcess(['racket'],status,output,'')):
        with pytest.raises(RuntimeError, match=expected) as error:
            module._probe(Path('racket'))
    if status >= 0:
        assert 'signal=' not in str(error.value)
    assert 'OOM' not in str(error.value)

def test_timeout_retains_partial_observations():
    module = probe()
    with patch.object(module.subprocess, 'run', side_effect=subprocess.TimeoutExpired(['racket'],20,output=b'partial',stderr=b'warning')):
        with pytest.raises(RuntimeError, match='timed out after 20s') as error:
            module._probe(Path('racket'))
    assert 'partial' in str(error.value) and 'warning' in str(error.value)

def test_success_still_requires_exact_marker():
    module = probe()
    with patch.object(module.subprocess, 'run', return_value=subprocess.CompletedProcess(['racket'],0,'RACKET_READY\n','')):
        assert module._probe(Path('racket')) is None
