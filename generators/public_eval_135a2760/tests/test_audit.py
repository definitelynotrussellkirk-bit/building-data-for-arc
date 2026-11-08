import importlib.util
import hashlib
from pathlib import Path
import pytest

def test_audit_rejects_changed_source(tmp_path):
    path=Path(__file__).resolve().parents[1]/'workspace/parametric/audit.py'
    assert path.is_file(), 'reusable source-pinned audit is missing'
    spec=importlib.util.spec_from_file_location('periodic_audit_test',path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    source=tmp_path/'rule.rkt'; source.write_text('a')
    binding={'files':[{'path':'rule.rkt','sha256':hashlib.sha256(b'a').hexdigest()}]}
    mod.check_binding(tmp_path,binding)
    source.write_text('b')
    with pytest.raises(ValueError,match='Source drift'): mod.check_binding(tmp_path,binding)
