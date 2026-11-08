# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Source-bound stage receipt manifest

`receipt_manifest.py` is a small review-recovery helper for environments where
battery stages finish in separate portable runtimes. It verifies that every
expected child receipt:

- exits zero without timing out,
- carries one exact battery subject,
- has a matching `.ok` marker and retained log, and
- is recorded with artifact SHA-256 hashes.

It deliberately does **not** write a battery summary or journal row. After a
complete manifest, copy the selected exact artifacts into one prepared runtime
and run the repository's official `run_generator_battery.sh ... --resume`
reconciler. That official command remains the only source of the aggregate
battery verdict.

Example from a packet repository working directory:

```sh
python3 generators/97b3f59b5cc4/workspace/receipt_manifest.py \
  --task 97b3f59b5cc4 --phase after \
  --expected-subject SUBJECT_SHA16 \
  --source ../checks/after-lint \
  --source ../checks/after-selfcheck \
  --out ../checks/after-reconciled/receipt-manifest.json
```

Pass one `--source` per stage-output directory. The normal complete battery has
12 stages; an incomplete or mixed-source set exits nonzero.

## Prior-return reconciliation manifest

`reconcile_prior_returns.py` checks the current generator against the two
retained audit returns without replaying either historical patch. It binds the
current `generator.py`, canonical pairs, exact four-axis matrix, retired-control
rejections, three-example teaching windows, and the retained repeated-color
counterexample into one finite JSON manifest. Any failed semantic or source-
binding check changes the report status to `conflict_detected`.

```sh
PYTHONPATH=src:shared/runtime python3 \
  generators/97b3f59b5cc4/workspace/reconcile_prior_returns.py \
  --out ../checks/reconciliation-current/report.json
```

The command refuses to overwrite an existing report. Remove or archive the old
manifest deliberately before rerunning it after a source change.
