# Visible-only solve work log

## Scope and exposure record

This final post-repair solve used only `solve/README.md`, `solve/challenge.json`, and my own Python work. I did not read the generator source, Racket rule, canonical data, reference solutions, other solver versions, prior solution notes, private query labels, check archives, audit evidence, or the episode tool implementation. The two public query inputs are visible; their correct outputs are unknown to this solve.

The overall review session has **earlier exposure: yes** because the primary reviewer previously saw the rule while repairing the packet. I am a newly delegated solver operating with fresh context; my task description disclosed that earlier exposure but did not disclose the rule, repair details, or prior solution reasoning. My own solve has **reference consulted: no**. This distinction means the episode must not be described as an entirely unexposed review session.

The parent supplied the prepared generator hash `92d329fc0fca6d59485820dc8fb544600fc521065f4b38dafe6894f85f1cb837` and instance hash `b45d4f9e1c6d92203a60ddbb6600b27758b602b21d5a9b737c8b43a47a8c5f34`. The required check reported the same identifiers. I have not independently inspected the underlying sources.

## Observations and public-data probe

I first read the public solve README. Every input has three isolated nonzero cells in its top row and three monochrome body shapes below it. Output colors follow the top-row markers from left to right. The output preserves each body's orientation and internal empty cells, crops away its external background, and arranges the crops vertically with exactly one empty row between them.

A small Python probe read only `solve/challenge.json` and printed each body's color, cell count, and bounding box. This was an observation probe, not an authored solver revision or a scored attempt.

- Example 0 places the five-cell shape before the two three-cell shapes; the tied shapes retain positional order.
- Example 1 places bodies of sizes 9, 6, and 4 in that descending order, regardless of their original vertical positions.
- Example 2 has three five-cell shapes and places them left to right because their top rows coincide.
- Example 3 has three four-cell shapes. The two bodies beginning on row 4 precede the body beginning on row 6, even though the row-6 body's left edge is left of one row-4 body. This favors sorting ties by top row, then left edge, rather than by column alone.
- Example 4 orders sizes 9, 5, and 3 and confirms centering. Crops of widths 2 and 1 both begin in column 1 of the width-4 output, consistent with integer-floor centering.

## Solver revision 1

Hypothesis: extract same-color four-neighbor connected components below the top row; sort by decreasing number of colored cells, then increasing bounding-box top row and left column; pair these objects with the marker colors in left-to-right order; stack tight crops without rotation or reflection, using one empty row between crops and horizontal offset `floor((maximum_width - crop_width) / 2)`.

The first authored solver implements that rule directly. It contains no stored example answers, query answers, seed assumptions, generator access, or external dependencies. It checks for a rectangular input and a one-to-one correspondence between markers and body components.

Required check for this revision, from the packet root:

```sh
python3 solve_episode.py check --intent solve --note 'Revision 1: visible examples imply descending body cell count, top-row/left-edge tie order, marker recoloring, centered crops, and one blank separator row; test this complete hypothesis.'
```

This log records actual observations and decisions rather than a token-level conversation trace. There were no earlier authored revisions or failed solver attempts in this fresh delegated solve.

### Actual check outcome

The command above exited 0 and reported execution completed, with **5 of 5 visible examples passed** and `reported_label: unknown`. The reported program hash was `57a675c2fa6cdca37303dc6b6c7a9b9cf5310acea5807585897fec6af1ebecd4`. The tool reported episode revision **2**; the heading "Solver revision 1" identifies my first authored revision within this newly delegated solve, not the episode's complete historical counter. I did not inspect the prior record to resolve that historical numbering, and I have not invented any additional attempts or failures. This delegated solve has one authored solver revision, one required check, and zero observed failed checks.

Both public queries are covered by the same general procedure. Their private correctness remains unknown. The tool marked `training_admitted: false`; no training-admission claim is made here.

### Stopping decision

The single visible-derived hypothesis matched every visible example, and the public queries contain the same marker/body structure. No implementation revision is warranted by the available feedback. I am finishing with `--earlier-exposure yes --reference-consulted no`, distinguishing the primary reviewer's earlier exposure during repair from this fresh delegated solver's lack of rule or reference access.

## Limits of the inference

All public body objects are monochrome connected shapes, with one distinct marker per object. The visible set cannot establish behavior for repeated marker colors, repeated body colors, diagonal-only connectivity, absent markers, background colors other than zero, or objects sharing exactly the same bounding-box origin. Those extensions are not needed for the public inputs. Query correctness remains unknown unless independently checked outside this visible-only solve.


## Provenance recovery

The original completed final-source solve, including its actual revision 2 and finish snapshot, is retained unchanged under checks/prior-solve/v3.0.2-numbering. An empty numeric attempt directory caused the count mismatch. During recovery the primary reviewer accidentally issued a check after a failed setup assertion, so the generated NotImplementedError placeholder executed. That real orchestration failure is preserved under checks/prior-solve/v3.0.2-replay-error, with its original intent solve label. It is not a failed inferred rule or an intentional teaching negative.

This is a supported replay of the unchanged successful authored solution on the identical generator and public challenge, after copying and removing the recreated old attempt directory tree. It adds no new inference and consults no reference. One solution was authored by the delegated solver; the record set contains its first visible pass, one accidental placeholder execution, and this replay. Earlier exposure remains yes for the primary reviewer; all query correctness remains unknown.

Actual supported replay: local revision 1 completed, 5/5 visible pairs passed, both queries still unknown. The successfully authored solution was unchanged.
