# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here. The selected implementation is `../generator.py`; workspace files are never automatically selected as label authority.

## Source-bound review probe

`review_probe.py` is a deterministic future-agent check for this generator. It loads the canonical row from `shared/data/canonical/puzzles.jsonl`, executes labels through the packet's actual Racket runner, then checks:

- every canonical train/test pair;
- deterministic generation in easy, medium, and hard bands;
- Python diagnostic-mirror parity with Racket output;
- the five-profile teaching schedule and lesson identifiability;
- exact override observation and invalid-key rejection;
- difficulty-band separation; and
- a retained concrete counterexample for every declared shortcut rival.

From the packet root, run:

```bash
python3 run_with_racket.py \
  python3 generators/8a82ec149798/workspace/review_probe.py \
  --repo-root . \
  --out ../checks/review_probe_after.json \
  --require-clean
```

The wrapper changes into `repo/`, so paths after `run_with_racket.py` are repo-relative. The probe is evidence only: the canonical Racket program remains label authority.
