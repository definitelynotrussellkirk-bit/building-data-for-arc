# Post-repair visible-only solve

This is an authored work summary, not a token-level conversation trace. Earlier exposure: yes; I worked on this task's generator and canonical rule before preparing this episode. During this solve I opened only the visible challenge and used a Python component probe. I did not consult generator source, reference code, private labels, or earlier solutions during the solving phase.

## Public observations and revision 1
Training examples have dimensions 22×25→22×25, 22×23→22×23, and 22×25→22×25. Their nonzero network cells are preserved. A Python probe found that every four-neighbor zero component touching a grid edge becomes color3, while every component without edge access becomes color2. Interior component sizes are [54,6,10], [28,30,28], and [57,4,12]; exterior totals are383,313,383. The middle example has two disconnected exterior components, so starting a fill from only one corner is insufficient.

The submitted solution independently enumerates zero components, records whether each reaches any edge, and fills each whole component. It preserves foreground cells and returns fresh rows. The small enclosed pockets require four-neighbor connectivity. This is the first actual submitted solution; no negative example or failed attempt was invented.

Query inputs have dimensions24×25 and22×25. Their output dimensions and correctness are not supplied to the reviewer. The check reports visible-example agreement and execution only; masked-query correctness is unknown.
