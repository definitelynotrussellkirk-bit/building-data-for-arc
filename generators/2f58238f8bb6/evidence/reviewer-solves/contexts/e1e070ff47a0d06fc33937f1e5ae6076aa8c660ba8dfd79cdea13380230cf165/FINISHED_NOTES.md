# Visible-example solve notes

## Access and exposure record

This solver received a clean visible-only task context and read only
`solve/challenge.json` and `solve/README.md` as puzzle evidence. No generator,
rule source, canonical data, private labels, reference solution, or previous
solution notes were consulted. The overall episode is **not blind**: the parent
reviewed the rule before dispatching this solver. Accordingly, the required
finish record is `earlier-exposure=yes`, `reference-consulted=no`.

These notes are an authored experimental summary, not a transcript or private
reasoning record.

## Hypothesis and revision 1

Read the nonzero cells of the top row from left to right as commands. Crop the
nonzero object below the top row to its bounding rectangle. Every command acts
independently on that original crop:

| Command | Transformation |
| --- | --- |
| 1 | Identity |
| 2 | Rotate 90 degrees clockwise |
| 3 | Rotate 180 degrees |
| 4 | Reflect left to right |

Concatenate the resulting copies horizontally in command order, with one zero
column between copies and their top edges aligned. Pad shorter copies below
with zeros. Ignore zero gaps between top-row commands.

The repeated 4 commands in visible examples 0 and 2 support repeated independent
reflections. The rectangular crops and their rotated copies determine the
clockwise direction, top alignment, and variable output width. Example 1 also
shows that zero gaps in the command row do not become output gaps.

Revision 1 implements this single hypothesis in pure Python. No earlier
solution revision or failed attempt occurred in this solver episode.

## Experimental results

The official checker completed revision 1 successfully: **3 of 3 visible
examples passed**, with `execution_status=completed` and
`reported_label=unknown`. No solution change was needed after this check; there
was one genuine solution revision and no failed attempt. The exact command and
returned record are saved in `solve/commands.json`.

A second solver independently reviewed only the same two permitted visible
files and agreed with the transformation and layout. The implementation
separates header and object spatially, so a shared command/object color does
not affect object extraction.

Stopped after the single hypothesis passed all available visible examples.
Private query correctness remains unknown; execution success does not establish
it. The finish command records earlier exposure as yes and reference consultation
as no, preserving the distinction between this solver's clean context and the
parent's prior rule exposure.
