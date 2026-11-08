# Blind solve work log

Task: 49754d8fa42e. Earlier rule exposure: no. Reference consultation: no.
Only the preparation tool's visible presentation, challenge.json and starter
solution/notes have been inspected. No generator, rule, task notes, audits,
reference solution or private query output has been opened.

## Revision 1 — nonzero color counts select a symbol

The input sizes are 4x8, 10x7, 5x5, 8x8 and 5x5; every visible output
is 3x3. Output symbols are a plus, a T, and a lower/right L, always using 5.
The single-foreground-color examples identify 2 with T and 3 with L.
The multicolor cases suggest selecting the most frequent nonzero color:

| Example | Nonzero counts | Predicted symbol |
| --- | --- | --- |
| 0 | 1:12, 2:10, 3:2, 6:2, 9:1 | plus |
| 1 | 1:2, 2:24, 3:17 | T |
| 2 | 3:9 | L |
| 3 | 1:24, 2:23, 3:1 | plus |
| 4 | 2:14 | T |

Example 1 has 27 zeros, more than any foreground color, so global mode
including background is contradicted. The scattered single-color examples
also favor color statistics over copying a spatial shape from the input.
The one-cell margin in example 3 supports exact counts, not rough area.

Implementation counts foreground cells and maps the winner to the taught
symbol. Ties and winners outside {1,2,3} are not taught; the implementation
uses lowest color for ties and rejects unknown winning colors. Neither
condition occurs in these visible inputs or the two visible query inputs.
Both queries have most frequent foreground color 3, so this hypothesis
predicts the L for both; private correctness remains unknown.

Command from packet root: python3 review.py blind check --intent solve
--note 'Most frequent nonzero color selects the taught 3x3 symbol; test all five visible pairs.'
No deliberate negative and no manufactured failed attempt was created.
