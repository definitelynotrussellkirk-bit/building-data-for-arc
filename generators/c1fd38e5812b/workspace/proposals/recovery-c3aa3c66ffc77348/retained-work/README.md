# ARCpuzzles review repair kit

This kit contains the concrete repair recovered from the interrupted review of
assignment `review-d0e2f66d807f6bf3`, generator `c1fd38e5812b`.

The original 349,966,246-byte upload was fully inspected before the execution
workspace reset. On remount, the file service refused raw materialization over
100 MB. Rather than return only a narrative, this archive provides:

- a complete replacement generator with independent row/column profiles;
- portable task tests and a concrete counterexample;
- the blind solution and derivation notes frozen before reference inspection;
- a six-member Racket-backed parametric rule family and tests;
- all requested review, decision, question, feedback, and audit reports;
- a fail-closed patcher that checks the exact reviewed source hash, backs up
  overwritten files, records hashes and commands, and can invoke the packet's
  official verifier, audit, battery, and packager.

## Apply

Extract this kit next to an extracted copy of the original review packet, then
run:

```bash
python3 apply_repair.py --packet-root /path/to/extracted-packet
```

The expected baseline generator SHA-256 is:

```text
836fa3a06d55f5a6450ccf989f8187695e6f45d8ef81f0a6a384a853a73409af
```

The patcher refuses any other generator revision unless `--force` is supplied.
It stores backups under the task workspace and writes
`WORK/REPAIR_KIT_APPLICATION.json`.

## Verify and package

After restoring/completing the packet's blind-review state, run:

```bash
python3 apply_repair.py \
  --packet-root /path/to/extracted-packet \
  --verify --full-battery --package
```

The script stops on the first failed command and writes exact receipts to
`WORK/REPAIR_KIT_RUN.log` and `WORK/REPAIR_KIT_VERIFICATION.json`. It does not
convert a failed or interrupted command into a claimed pass.

## Why the repair matters

The old distribution allowed only “both axes uniform” or “both axes
nonuniform.” The canonical rule detects run starts independently along the
first column and first row, so that distribution left a shortcut unchallenged.
The repair adds `uniform_rows` and `uniform_cols`, keeps the earlier public and
fully-uniform shares, and pins a witness where coupled chunking produces an
extra column.

## Local reconstruction evidence

`local_harness/test_repair.py` exercises the replacement generator without the
large packet. The parametric test suite uses a Python mirror for structural and
leakage checks; inside the packet it additionally compares every materialized
program against the actual `RacketBridge`.
