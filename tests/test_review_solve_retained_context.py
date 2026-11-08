import json
from pathlib import Path
import shutil

from test_review_solve import prepared
from test_review_full_return import _docs
from arcpuzzles import review_solve as solves
from arcpuzzles.review_full_return import build_full_return
from arcpuzzles.review_full_collect import collect_full_returns
from arcpuzzles.review_solve_tracker import build_solve_tracker, retain_solve_examples
from arcpuzzles.review_full_packet import canonical_json


def test_retention_keeps_frozen_source_and_unique_final_notes_without_archives(prepared, library, tmp_path):
    root = prepared
    program = root / 'solve/solution.py'
    program.write_text('def solve(grid):\n    return grid\n')
    solves.check_solve(root, program, note='Identity fails the visible pair.')
    program.write_text('def solve(grid):\n    return [[v + 1 for v in row] for row in grid]\n')
    solves.check_solve(root, program, note='Increment fits visible examples.')
    final = b'Final conclusion after the last checked revision; exposure disclosed.\n'
    (root / 'solve/SOLVE_NOTES.md').write_bytes(final)
    solves.finish_solve(root, reference_consulted=False, earlier_exposure='yes', reason='Visible fit; private score unknown')
    _docs(root)
    frozen = (root / '.review/solve-private/generator.py').read_bytes()
    returned = build_full_return(root, tmp_path / 'review_response_context.zip')
    collect_full_returns(library / 'REVIEW', tmp_path)
    # Retention must not substitute later selected source for the captured source.
    (library / 'generators/aaaa00000003/generator.py').write_text('VERSION = "changed"\n')
    feed = tmp_path / 'feed'
    built = build_solve_tracker(library / 'REVIEW', feed)
    assert built['counts']['errors'] == 0
    rows = [json.loads(line) for line in Path(built['attempts']).read_text().splitlines()]
    for row in rows:
        assert (feed / row['files']['generator_source']['path']).read_bytes() == frozen
        assert (feed / row['files']['finished_work_log']['path']).read_bytes() == final
        assert (feed / row['files']['final_work_log']['path']).read_bytes() == final
        summary = json.loads((feed / row['files']['solve_summary']['path']).read_text())
        assert summary['earlier_rule_exposure'] == 'yes'
    retain_solve_examples(library, feed)
    assert len(list((library / 'generators/aaaa00000003/evidence/reviewer-solves/contexts').glob('*/generator.py'))) == 1
    shutil.rmtree(library / 'REVIEW/assignments')
    shutil.rmtree(library / 'var/review/returns')
    shutil.rmtree(library / 'var/review/full-packets')
    shutil.rmtree(feed)
    shutil.rmtree(root)
    Path(returned['zip']).unlink()
    rebuilt = build_solve_tracker(library / 'REVIEW', tmp_path / 'restored')
    restored = [json.loads(line) for line in Path(rebuilt['attempts']).read_text().splitlines()]
    assert rebuilt['counts'] == built['counts']
    fields = ('attempt_id','program_hash','label','reported_label','earlier_rule_exposure',
              'reference_consulted_during_solve','attempt_intent','training_admitted')
    assert [{k:r[k] for k in fields} for r in restored] == [{k:r[k] for k in fields} for r in rows]
    for before, after in zip(rows, restored):
        assert {k:v['sha256'] for k,v in after['files'].items()} == {k:v['sha256'] for k,v in before['files'].items()}
        assert (tmp_path / 'restored' / after['files']['generator_source']['path']).read_bytes() == frozen
        assert (tmp_path / 'restored' / after['files']['finished_work_log']['path']).read_bytes() == final


def test_curriculum_only_task_survives_retention(library, tmp_path):
    feed = tmp_path / 'feed'
    feed.mkdir()
    annotation = {'task_id':'aaaa00000001','notes':'Current measured teaching limitation',
                  'verification_status':'reviewer_reported','training_admitted':False,'axes':{}}
    for name, rows in [('attempts.jsonl',[]),('questions.jsonl',[]),('curriculum.jsonl',[annotation])]:
        (feed/name).write_bytes(b''.join(canonical_json(r)+b'\n' for r in rows))
    hashes = {p.name:solves.digest(p.read_bytes()) for p in feed.iterdir()}
    (feed/'manifest.json').write_text(json.dumps({'schema':'arc-reviewer-solve-feed-v1','counts':{'errors':0},'files':hashes}))
    retain_solve_examples(library, feed)
    shutil.rmtree(feed)
    build_solve_tracker(library / 'REVIEW', tmp_path / 'rebuilt')
    assert [json.loads(line) for line in (tmp_path/'rebuilt/curriculum.jsonl').read_text().splitlines()] == [annotation]
