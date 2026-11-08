# Fresh post-repair solve on version 3.4.0

Earlier rule exposure: yes. I reviewed and repaired this family earlier. During this solve I opened only the newly prepared challenge.json; I did not consult generator source, reference code, private query labels or previous solution explanations. This is an exposed solve record, not independent blind discovery.

## Visible observations

Train0 input/output are9rows×9columns. The wide object has row widths3,2,1. Its width2row comes to rest above the red line, while its one-cell tail replaces a red cell. This rules out both stopping the lowest cell and anchoring at the widest/upper supporting row. The disconnected singleton sharing its column travels independently to the floor. The separate thin bar also reaches the floor and loses its red-line cell.

Train1 input/output are7rows×7columns. Its singleton reaches the last row, leaving a hole in the red row at the same column. Train2 input/output are11rows×11columns. A4/2/1profile behaves like the3/2/1profile; the detached singleton below it also reaches the floor. The line holes take precedence over blue cells after translation.

The query inputs are10rows×14columns and15rows×15columns; outputs are unknown. I infer maximal four-connected blue components above the full red row, preserve each shape under vertical translation, use the lowest row containing at least two cells as support, send every other component to the floor, and apply holes last.

## Implementation and stopping policy

I wrote a fresh standalone component search and translation implementation. It imports no task or reference helpers. This is the first attempted revision for this prepared episode. The official check will report visible agreement and query execution; private correctness remains withheld. The previous source-bound exposed solve is retained separately under checks/prior-solve. These notes are an authored work log, not a token-level model trace.
