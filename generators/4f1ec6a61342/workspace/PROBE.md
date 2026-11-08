# Independent chamber probe

`probe_chambers.py` uses standard-library Python and the public
`reviewer_support.canonical_pairs` / `find_root` helpers. It imports the selected
generator, never its chamber-discovery or output-labeling helpers. Its own
four-neighbor flood fill checks rectangular observed rooms, exterior walls,
allowed colors, dimensions, chamber multiplicity, the control, and exactly one
room containing exactly the observed target number of red cells. All red seeds
are erased; the matching room is painted 8; all color-5 cells remain 5. The
control becomes 0 except when it is itself color 5, in which case it remains 5.
Public canonical answers cross-check this independent oracle.

## Full run from the packet root

```bash
python repo/generators/4f1ec6a61342/workspace/probe_chambers.py \
  --seeds 17 --sample-index 0 --windows 100 --start 0 \
  --out analysis_tmp/chamber-probe.json \
  --failures-jsonl analysis_tmp/chamber-probe-failures.jsonl
```

Both output paths must be new. The JSONL retains **every exact failure**,
including grids and labels for ambiguous lessons; `--capexamples` controls only
the number embedded in the summary JSON. Omitting JSONL retains counts and the
capped examples only. Reusing an existing report path fails without overwriting
it. Use a different path for each source revision or command.

Four integer domains are parsed directly from `AXES`: height 7..18, width
9..20, chambers 2..6, target 1..6. Domain drift is a contract failure. For each
seed the probe tries their entire Cartesian product in each difficulty band:
4,320 combinations per band, 12,960 total. Every pinned case is independently
measured. It does not infer room seed counts from generator metadata.

The default direct lesson census takes 100 consecutive four-sample windows per
seed in each band. Window starts are 0..99; samples span 0..102. It holds out
each of the four samples once, leaving three demonstrations and one query.
That gives 400 rotations per band / 1,200 total per seed. The report records
all starts, seeds, sample indices, draw counts, rotations and unique input
counts. Unique inputs cover both Cartesian and window draws. Window draws are
cached once per sample; overlapping windows therefore intentionally reuse them.

Rivals are discovered dynamically from the generator's actual nonempty
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` dictionaries. Every declaration
is scored separately, even when the same callable appears in both. The probe
does not embed a copied list of rival names. A rival is `refuted` when any
demonstration disagrees with the oracle, `survived_all` when it matches all four
pairs, and `ambiguous` when it fits all three demonstrations but disagrees on
the query. Ambiguity, missing/malformed declarations, exceptions, mutations,
contract failures and canonical-oracle disagreements cause nonzero exit.
Every `CANONICAL_SHORTCUTS` declaration must fit every public canonical pair;
a failed fit is a defect. `LESSON_COMPETITORS` may be canonically refuted.
`survived_all` is reported for inspection; agreement on all sampled pairs alone
does not establish that a rival is wrong or that a lesson is ambiguous.

## Portable staged runtime

The same script works when copied into a staged runtime, or when selecting that
runtime explicitly:

```bash
python /path/to/probe_chambers.py --root /path/to/staged-runtime \
  --seeds 17 23 --windows 100 \
  --out /path/to/new-report.json --failures-jsonl /path/to/new-failures.jsonl
```

It resolves the staged generator at
`puzzle_generators/per_puzzle/4f1ec6a61342/generator.py` and dependencies from
the staged runtime itself. In a library it resolves
`generators/4f1ec6a61342/generator.py` and `shared/runtime`. `--generator` can
select an explicit file. `--root` binds canonical data to that tree rather than
the current working directory. Generator, probe, imported local runtime files
and canonical-ledger SHA-256 values, Python version, command, working directory,
elapsed time and evidence scope are recorded. Changing source bytes while the
probe runs is a failure.

## Short diagnostic runs and limits

The companion `test_probe_chambers.py` imports the probe relative to its own
file and checks complete expected grids, including control-5 preservation,
non-wall control clearing, red-seed erasure, blank cells, unchanged walls and
input immutability. Run from the library or portable runtime with both files
beside each other:

```bash
python -m unittest discover -s /path/to/probe-workspace \
  -p test_probe_chambers.py -v
```

Use `--skip-cartesian --windows 1` for a quick smoke test. Such reports mark
`full_requested_coverage: false`; only runs that include the Cartesian suite
and at least 100 windows per seed/band mark it true. Default coverage uses one
seed and one pinned Cartesian sample index. Additional seeds are configurable,
and separate runs can vary `--sample-index` and `--start`.

This tool measures **direct-generator, independent Python-oracle proxy
evidence**. It does not run Racket, exercise production lesson materialization,
or upgrade any safety or admission label. A public Racket-backed lesson census
is separate evidence. Finite declared-rival refutation cannot establish unique
program induction or rule correctness outside the stated chamber contract.
