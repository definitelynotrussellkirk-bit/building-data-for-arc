# Solve work log

## Exposure and replay note

This workspace was rehydrated after a tooling reset. I had already seen a different
visible episode from this same reviewer-authored task and independently inferred the
same transformation, but I have not opened the task's generator, Racket rule, private
query labels, reference solution, notes, or audit evidence. I therefore report prior
exposure honestly at finish even though no reference was consulted.

## Hypothesis from the fresh visible episode

The input contains solid non-gray rectangular pieces and hollow gray (`8`) frames.
Each complete frame is an exact rectangular border. Its interior dimensions identify
the solid colored piece that belongs inside it. The output erases every source piece,
keeps complete frames in place, and fills each frame interior with the color of the
piece having exactly the same height and width.

Training example 2 supplies the decisive negative witness in this episode: the would-be
right frame has its top edge overwritten by the color-5 block. Its gray component is
not a complete border, so both that damaged frame and the corresponding source piece
disappear. The intact left frame is filled with the `4x2` color-2 piece.

## Test-first implementation

1. Added `WORK/checks/blind-tdd/test_visible.py`, loading the solution exactly like
   the packet worker (without inserting the module into `sys.modules`).
2. Ran it against the initial skeleton and retained the expected
   `NotImplementedError` in `WORK/checks/blind-tdd/red.stderr`.
3. Implemented four-connected monochrome components, exact hollow-border validation,
   solid-rectangle validation, orientation-preserving dimension matching, and output
   reconstruction on a zero background.
4. Avoided postponed annotations and dataclasses because the previous packet-worker
   reproduction showed that combination can fail under Python 3.13 when a temporary
   module is not pre-registered in `sys.modules`.

## Remaining uncertainty

All visible lessons use one uniquely sized piece per complete frame. If multiple pieces
shared the same dimensions, shape alone would not identify their pairing; the solver
uses deterministic color/reading order. No rotation or reflection is applied because
`2x3` and `3x2` are visibly distinct roles in the examples.
