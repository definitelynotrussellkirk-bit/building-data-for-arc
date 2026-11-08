# Workspace

The selected implementation is `../generator.py`; workspace tools are never
automatically selected as generators. `lesson_probe.py` is a reusable measurement
tool, and `NEXT_REVIEW.md` records the handoff for future agents.

## Run in an extracted review packet

Run these commands from the packet root, where `run_with_racket.py` lives. The
wrapper enters `repo/` and prepares the repository's Python and Racket paths.
Choose a new output path for each retained run.

```bash
python3 setup_racket.py
python3 run_with_racket.py python3 -m pytest generators/2c6496d261a6/tests -q
python3 run_with_racket.py python3 generators/2c6496d261a6/workspace/lesson_probe.py --lessons-per-band 100 --out ../checks/lesson-probe-new.json
```

The default measurement samples 100 ordinary lessons in each of default, easy,
medium, and hard, with three demonstrations and two queries per lesson. It uses
the actual episode runner and persistent Racket bridge; it records source hashes,
seeds, sample indices, uniqueness, witnesses, canonical fits, and rival survivors.
No failed sample is silently replaced. The first generated separating example
for each canonical-fitting shortcut includes actual Racket and rival outputs.

To measure the imported generator with the repaired evaluator:

```bash
python3 run_with_racket.py python3 generators/2c6496d261a6/workspace/lesson_probe.py --lessons-per-band 100 --generator ../.review/baseline/repo/generators/2c6496d261a6/generator.py --out ../checks/lesson-probe-baseline-new.json
```

`passed` and `probe_completed` report successful computation, under the explicit
`pass_criterion`. Read `all_lessons_identifiable` and each rival's surviving-lesson
counts for the semantic result. A valid diagnostic run on a weak generator may
exit zero with `all_lessons_identifiable=false`.

The probe isolates the runtime from the selected source and records both the
sampling and evaluator hashes. It does not score private solve labels, upgrade
approval, or prove identifiability beyond the declared finite rival family.
