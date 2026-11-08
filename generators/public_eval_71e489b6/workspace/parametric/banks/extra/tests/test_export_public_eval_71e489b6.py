import importlib.util
import hashlib
from pathlib import Path
import pytest
from reviewer_support import public_challenge_bytes

HOME=Path(__file__).resolve().parents[1]

@pytest.fixture
def exporter():
    path=HOME/'workspace/parametric/public_export.py'
    assert path.is_file(), 'validated batch exporter is missing'
    spec=importlib.util.spec_from_file_location('export_'+HOME.name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def views():
    rows=[{'train':[{'input':[[1]],'output':[[2]]},{'input':[[3]],'output':[[4]]}],
           'test':[{'input':[[i]]}]} for i in (5,6,7,8)]
    return sorted(rows,key=lambda v:hashlib.sha256(public_challenge_bytes(v)).hexdigest(),reverse=True)


def test_batch_physically_writes_in_content_id_order(exporter,tmp_path,monkeypatch):
    written=[];real=Path.write_bytes
    def track(path,data):
        written.append(path.name)
        return real(path,data)
    monkeypatch.setattr(Path,'write_bytes',track)
    out=tmp_path/'public'
    report=exporter.export_batch(views(),out)
    expected=sorted(hashlib.sha256(public_challenge_bytes(v)).hexdigest()+'.json' for v in views())
    assert written==expected, 'sorting the receipt alone does not sort physical publication'
    assert sorted(p.name for p in out.iterdir())==expected
    assert report['count']==4 and exporter.verify_batch(out)['count']==4
    for v in views():
        raw=public_challenge_bytes(v)
        assert (out/(hashlib.sha256(raw).hexdigest()+'.json')).read_bytes()==raw


def test_duplicate_and_late_invalid_payload_are_rejected_before_write(exporter,tmp_path):
    valid=views()[0]
    with pytest.raises(ValueError):exporter.export_batch([valid,valid],tmp_path/'duplicates')
    assert not (tmp_path/'duplicates').exists()
    malformed={**views()[1],'test':[{'input':[[7]],'output':[[8]]}]}
    with pytest.raises(ValueError):exporter.export_batch([valid,malformed],tmp_path/'malformed')
    assert not (tmp_path/'malformed').exists()


def test_tamper_and_existing_destination_are_rejected(exporter,tmp_path):
    out=tmp_path/'public';exporter.export_batch(views(),out)
    with pytest.raises(ValueError):exporter.export_batch(views(),out)
    file=next(out.iterdir());file.write_bytes(file.read_bytes()+b' ')
    with pytest.raises(ValueError):exporter.verify_batch(out)
