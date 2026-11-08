# Reusable authoring tools and implementation evidence

`check_output_profile_support.py` compares the full/partial/empty output-mass
profiles in the actual canonical record with each generated difficulty band.
It reuses real reference labels from a completed shared lesson census (JSON or
gzip), or explicit task-authored observation wrappers around public apply receipts.
The comparison core is generic; `largest4_color3_to8` is an explicit task adapter.
Do not apply this adapter's color or clipping assumptions to unrelated rules.

From the extracted packet's WORK/repo directory, after setting up the local
runtime, a replay is:

```sh
../.venv/bin/python3 generators/8738d400fb96/workspace/check_output_profile_support.py \
  --canonical ../checks/output-profile/canonical-observations.json \
  --canonical-ledger shared/data/canonical/puzzles.jsonl \
  --generated ../checks/lesson-census.json.gz \
  --adapter largest4_color3_to8 \
  --out ../checks/output-profile/replayed-support.json
```

Use your checkout's Python interpreter; the script itself uses only the standard
library. The canonical ledger can also be found from the installed task's own
checkout, including the portable task-test layout. An explicit path is preferable
when authoring outside that layout. The required complete canonical identities,
grids and labels come from that file rather than wrapper cardinality claims.
The parser checks source bindings, population completeness, counts, input/output
hashes, runtime manifests, rule identities and reference-execution outcomes.

Exit0 means every canonical output profile was observed in each requested band.
Exit1 means a required profile was not observed. Exit2 means incomplete,
malformed or inconsistent evidence. A rare profile can be missed in a finite
sample; a supported mass class is not proof of correct labels, useful frequency
or complete semantic teaching. No receipt is a cryptographic attestation.

The original baseline has only full outputs in the retained fifteen Racket-labelled
inputs. The final300-lesson census has450full/225partial/225empty pairs per band.
Both results are retained under checks/output-profile/. Existing failed checks
and malformed-mapping reproductions remain under checks/final-review/.

`../tests/oracle.py` is an independent flood-fill/translation oracle. Task tests
use public reviewer_support canonical-data helpers and work in the isolated
portable runtime. `IMPLEMENTATION_PLAN.md` and `PROGRESS.md` record the design,
changes of direction, failures and limits. Counterexamples live beside this
workspace under ../counterexamples/.

Large evidence JSONs are retained losslessly as gzip where needed. See
checks/EVIDENCE_STORAGE.json and checks/RESTORE_EVIDENCE.md for original paths,
lengths and hashes. Recorded commands keep the actual original output paths.
