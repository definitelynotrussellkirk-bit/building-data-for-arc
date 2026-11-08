# Reproducible review probes

These tools belong to task 5da2f80a4a4f; they do not change shared tools or audited task sources. They use Python 3.12+, the repository dependencies, and the packet's offline Racket runtime. Output directories must not already exist. Run these commands from the **packet root**, which contains repo/ and run_with_racket.py.

## Main support / counterexample probe

```sh
python3 setup_racket.py
python3 run_with_racket.py python3 generators/5da2f80a4a4f/workspace/review_probe.py \
  --out ../checks/fresh_probe --samples-per-band 256 --exhaustive --pytest
```

To compare with the packet's frozen pre-review source, add:

```text
--baseline-generator ../.review/baseline/repo/generators/5da2f80a4a4f/generator.py
```

The tool constructs a clean temporary runtime, copies itself into that runtime, executes canonical Racket, and retains runtime_manifest.json and execution.json. report.json records per-band counts, relative geometry support, key shapes conditional on frame shape, palette/scale/profile counts, unique grids and outputs, and rival disagreements. counterexamples.json contains exact seeded inputs and both outputs. failures.json must be empty for success. --pytest runs the selected task's staged test file and saves pytest.log.

--exhaustive means all legal offsets for the 22 declared variable shape combinations at each palette count 2/3/4, using one seeded key pattern per case. It does not enumerate every matrix or every random seed. By default, the sampler census has 256 examples per band. The fixed seed derivation is versioned in the source. Finite rival/lesson checks cannot prove universal identifiability.

Once adopted into a repository without the packet wrapper, run this script with Python from any directory, ensuring the repository dependencies and RACKET_PATH/PATH are configured. It derives the repository root from its own location. Omit the optional baseline path when no frozen baseline is available.

## Findings-only audit reproducer

```sh
python3 run_with_racket.py python3 generators/5da2f80a4a4f/workspace/audit_probe.py \
  --out ../checks/audits/fresh_audit
```

Requires both original audit targets 5faf9d5e3e6d and 91fd8c09b08e in the catalog. It stages them separately, reproduces an unseen transform-code episode, reproduces a reflection validator hole and inert override cases, checks all canonical pairs, and checks 192 clean reflection samples with actual Racket.

**Exit 0 means the findings were reproduced and the clean controls passed, not that the audited targets are issue-free.** Future fixes to those targets should make the old finding assertions fail. report.json includes exact scenes, source hashes, and a separately labeled structural key-coverage census that is not itself Racket-backed.

## Acceptance commands

```sh
python3 run_with_racket.py python3 -m arcpuzzles check 5da2f80a4a4f \
  --battery --phase after --out ../checks/fresh_battery
python3 run_with_racket.py python3 -m pytest -q tests
python3 run_with_racket.py python3 -m arcpuzzles generate 5da2f80a4a4f \
  --count 16 --seed 42 --allow-unapproved --out ../checks/fresh_episodes.jsonl
```

The explicit unapproved flag is for research validation only. Do not repin approval evidence or alter the rule to make a check pass. The existing task test file carries the regressions because runtime staging follows the catalog's static file map; a newly named test needs to be deliberately staged.

## Current parametric extension verifier

A source-local prototype for an episode-level `key_transform` parameter lives in
`workspace/parametric/`. It is separate from the canonical generator and rule.
From the outer extracted packet directory, run:

```sh
python3 review.py run python3 \
  generators/5da2f80a4a4f/workspace/parametric/verify.py \
  --out ../checks/parametric/identity-transpose-fresh
```

The verifier checks the `identity` and `transpose` settings with exact Racket,
retains public challenges and a disagreement witness, and fails if either
three-demo episode leaves both parameter values alive. See
`workspace/parametric/README.md` for the bounded input contract and limitations.

## Current strict-scalar reproducer

`counterexamples/strict-scalar-contract.json` records representative invalid
public values accepted by the pre-review source and rejected by the current
contract. The selected task tests replay every retained case; the full baseline
87-warning detector log remains review evidence rather than task source.
