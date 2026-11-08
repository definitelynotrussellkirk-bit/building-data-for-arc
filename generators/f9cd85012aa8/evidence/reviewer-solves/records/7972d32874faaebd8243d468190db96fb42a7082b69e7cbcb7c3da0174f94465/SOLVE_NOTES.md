# Final-generator visible-only solve work log

Assignment: review-4e0087825fba4aeb. Task: f9cd85012aa8.

## Exposure, boundaries, and preparation

This episode is not blind. I have earlier visible-example solve exposure from the previous generator revision, and the root reviewer reviewed source before this phase. The truthful finish declaration is earlier exposure `yes`. I did not receive source or a repair explanation, inspect the generator or canonical rule, or read any reference solution, audit, private label, or private answer in this delegated episode. I did not reopen previous solver code or prior solution notes. Earlier visible hypotheses remain in my conversational memory and may influence my interpretation.

I independently wrote the current code after fresh preparation and inspection of the new public demonstrations. The present single invocation performs opaque retention, preparation, authorship, checking, and finishing while the root pauses concurrent filesystem work.

Two earlier `python3 solve_episode.py prepare` invocations exited 1 with the identical traceback below. An initial opaque-move recovery successfully prepared the seven-example challenge, but a subsequent ordinary check failed before solver execution with the second traceback below. These are three genuine infrastructure failures; none is an intentionally failed solve or a visible-example mismatch. Their commands, exit codes, and full tracebacks are retained in agent_commands.json.

### Both preparation failures

```text
Traceback (most recent call last):
  File "/workspace/scratch/1963dbdb6b7d/WORK/solve_episode.py", line 22, in <module>
    raise SystemExit(main(ROOT, sys.argv[1:]))
                     ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/scratch/1963dbdb6b7d/WORK/repo/src/arcpuzzles/review_solve.py", line 431, in main
    value = prepare_solve(packet_root, kind)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/scratch/1963dbdb6b7d/WORK/repo/src/arcpuzzles/review_solve.py", line 122, in prepare_solve
    summary, _ = _frozen(root, kind)
                 ^^^^^^^^^^^^^^^^^^^
  File "/workspace/scratch/1963dbdb6b7d/WORK/repo/src/arcpuzzles/review_solve.py", line 105, in _frozen
    raise ValueError("Generator or reference source changed after solve preparation")
ValueError: Generator or reference source changed after solve preparation
```

### Check blocked before execution

```text
Traceback (most recent call last):
  File "/workspace/scratch/1963dbdb6b7d/WORK/solve_episode.py", line 22, in <module>
    raise SystemExit(main(ROOT, sys.argv[1:]))
                     ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/scratch/1963dbdb6b7d/WORK/repo/src/arcpuzzles/review_solve.py", line 433, in main
    value = check_solve(packet_root, args.solution, note=args.note, timeout=args.timeout,
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/scratch/1963dbdb6b7d/WORK/repo/src/arcpuzzles/review_solve.py", line 237, in check_solve
    summary, episode = _frozen(root, kind)
                       ^^^^^^^^^^^^^^^^^^^
  File "/workspace/scratch/1963dbdb6b7d/WORK/repo/src/arcpuzzles/review_solve.py", line 105, in _frozen
    raise ValueError("Generator or reference source changed after solve preparation")
ValueError: Generator or reference source changed after solve preparation
```

At the root's explicit direction, active public and private preparation directories were moved opaquely outside WORK to new retention destinations. No contents were inspected. Opaque private copies are not deliverables and must not be packaged. No source was edited by this solver.

## Current public source binding

- generator_hash: `5d56b67a76405569e229b852ae2b6af7f4fc5491cf2e2a476a319437e254746e`
- instance_hash: `a5b9109d8fac2c3601a93e155fea48eeaeb9fe4cba6732b156298c9707850ea2`
- challenge_sha256: `1a5d39f46708d3ae0228fd2ebb350b3a2e421efe260447894def1afbcda0cffd`

## New visible demonstrations

I inspected fresh prepare output with dimensions before every array. An own Python inspection of the public challenge calculates the following coordinate extrema and output counts; it uses only visible training pairs.

| Example | Input dimensions | Output dimensions | Color-6 bounding box (top,left,bottom,right) | Output nonzero cells |
|---|---|---|---|---|
| 0 | 9 rows x 10 columns | 9 rows x 10 columns | (0, 6, 1, 9) | 8 |
| 1 | 19 rows x 8 columns | 19 rows x 8 columns | (7, 3, 10, 6) | 16 |
| 2 | 9 rows x 10 columns | 9 rows x 10 columns | (2, 6, 5, 7) | 8 |
| 3 | 18 rows x 9 columns | 18 rows x 9 columns | (1, 2, 4, 4) | 12 |
| 4 | 7 rows x 8 columns | 7 rows x 8 columns | (0, 5, 2, 6) | 6 |
| 5 | 18 rows x 7 columns | 18 rows x 7 columns | (6, 2, 10, 4) | 15 |
| 6 | 8 rows x 9 columns | 8 rows x 9 columns | (3, 3, 4, 5) | 6 |

Each output keeps the input canvas size and contains only zero and color 6. All color-6 cells lie within a filled rectangle with the input color-6 extrema. Other colored objects vanish. The examples cover horizontal and vertical narrow rectangles, larger rectangles, shape gaps, contact with the outer boundary, and distractors with differing colors and sizes. The target is neither always the largest nor always the smallest object by cell count. Selecting color 6 and completing its rectangle accounts for the stable selection cue and every completion.

## Genuine solver revision 1

I freshly authored a solver that initializes a zero canvas of the input dimensions, scans input cells equal to 6 to find coordinate minima and maxima, and fills that inclusive rectangle with 6. The rule reads the original input, preserves location and canvas size, and removes distractors by starting from zero. An absent color-6 object would yield a zero canvas; none of the visible training examples tests that fallback.

This is one genuine hypothesis and a normal solve intent, not a diagnostic negative. No code revision was made because of the prior infrastructure failures. I now check this revision against the newly bound public episode.
