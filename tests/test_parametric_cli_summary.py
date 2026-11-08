"""Display-only qualification summaries preserve complete native receipts."""
import json
from pathlib import Path

from arcpuzzles import cli
from arcpuzzles import parametric_promotion as promotion
from test_parametric_promotion import candidate, fake_execution


def test_qualification_summary_preserves_receipt_and_default_output(candidate, monkeypatch, capsys, tmp_path):
    catalog, tid, _ = candidate
    monkeypatch.setattr(promotion, '_execute', fake_execution)
    for summary in (False, True):
        out = tmp_path / str(summary)
        args = ['--library', str(catalog.root), 'parametric', 'qualify', tid, '--out', str(out)]
        assert cli.main(args + (['--summary'] if summary else [])) == 0
        printed = json.loads(capsys.readouterr().out)
        receipt = json.loads((out / 'qualification.json').read_text())
        assert printed['status'] == 'qualified'
        assert Path(printed['receipt']) == out / 'qualification.json'
        assert printed['training_admitted'] is False
        assert receipt['source_binding'] and len(receipt['jobs']) == 4
        if summary:
            execution = json.loads((out / 'execution.json').read_text())
            assert 'source_binding' not in printed and 'jobs' not in printed
            assert printed['settings_count'] == 2
            assert printed['job_count'] == 4
            assert printed['demos'] == receipt['jobs'][0]['demos']
            assert printed['queries'] == receipt['jobs'][0]['queries']
            assert printed['protected_racket'] is execution['racket']['protected']
            assert printed['racket_evaluations'] == execution['racket_evaluations']
            assert printed['programs'] == receipt['programs']
            assert printed['execution']['sha256'] == receipt['execution']['sha256']
            assert Path(printed['execution']['path']) == out / 'execution.json'
            assert printed['limits'] == receipt['limits']
        else:
            assert printed == {**receipt, 'receipt': str(out / 'qualification.json')}
