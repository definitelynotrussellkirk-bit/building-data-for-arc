from pathlib import Path
import json
import pytest
from arcpuzzles import check_jobs as jobs

def test_run_id_cannot_escape_store(tmp_path):
    with pytest.raises(ValueError): jobs.status(tmp_path,'../outside')

def test_unfinished_dead_supervisor_is_not_a_stage_failure_or_safe_resume(tmp_path):
    root=tmp_path
    directory=root/'var/check-runs'/('a'*32);directory.mkdir(parents=True)
    (directory/'state.json').write_text(json.dumps({'status':'running','pid':99999999,'attempt':1}))
    result=jobs.status(root,'a'*32)
    assert result['status']=='parent_interrupted_unclean'
    assert not result['resumable']

def test_completed_stage_failure_retains_stage_meaning(tmp_path):
    directory=tmp_path/'var/check-runs'/('b'*32);directory.mkdir(parents=True)
    (directory/'state.json').write_text(json.dumps({'status':'stage_failed','resumable':True,'stage_exit_code':1}))
    result=jobs.status(tmp_path,'b'*32)
    assert result['status']=='stage_failed' and result['stage_exit_code']==1


def test_actual_detached_failure_wait_and_resume_reuses_checkpoint(library):
    from test_check_resume import install_battery
    from arcpuzzles import Catalog
    install_battery(library)
    first=jobs.start(Catalog(library),'aaaa00000001',timeout=10,phase='after')
    run_id=first['run_id']
    failed=jobs.wait(library,run_id,seconds=10)
    assert failed['status']=='stage_failed' and failed['stage_exit_code']==1
    assert failed['resumable']
    directory=Path(failed['directory'])
    original=(directory/'check/checks/aaaa00000001_after_lint.log').read_bytes()
    restarted=jobs.resume(library,run_id)
    assert restarted['run_id']==run_id
    completed=jobs.wait(library,run_id,seconds=10)
    assert completed['status']=='completed' and not completed['resumable']
    assert completed['attempt']==2
    assert (directory/'check/checks/aaaa00000001_after_lint.log').read_bytes()==original
    assert (directory/'check/attempts/0001/checks/aaaa00000001_after_override.log').read_text().strip()=='failure'
    assert 'SKIP-lint' in (directory/'supervisor.log').read_text()
