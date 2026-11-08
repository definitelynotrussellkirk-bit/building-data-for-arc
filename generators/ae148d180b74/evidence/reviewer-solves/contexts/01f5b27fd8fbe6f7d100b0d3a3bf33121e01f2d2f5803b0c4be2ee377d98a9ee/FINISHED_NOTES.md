# Blind solve ae148d180b74 — visible-only work log

This is a reviewer-authored work log, not a token-level model trace. Before this
solve I read packet-level instructions only; no generator, reference rule, notes,
private labels, or prior solutions were opened. Earlier rule exposure: no.

## Revision 1 — shortest marked path
All three visible pairs retain background, walls (5), and markers (2 and 3), and
paint the zeros on a connecting four-neighbor path with 8. The two branched mazes
leave their dead-end side corridors at 0, so filling all reachable space is not
supported. I used a breadth-first search through 0/2/3 and painted the predecessor
chain, leaving the endpoints intact. No deliberately wrong revision was created.

The visible-only probe in visible_probe.json measured unique shortest routes in
all training pairs: distances 10, 19, 19; the output contains exactly distance-1
eights (9, 18, 18). Query 0 also has a unique shortest route, distance 11. Query 1
has 120 shortest routes, distance 10. The examples cannot identify a traversal
ordering or whether equal-length paths should be combined. I chose deterministic
up/down/left/right traversal from 2 toward 3 as a provisional single-path tie-break.
This is an assumption, not a conclusion from the demonstrations. I did not look
at labels to choose a tie-break. The unique-path examples reject neither other
single-route tie-breaks nor a union-of-shortest-paths rule.

No natural failed revisions occurred. The retained first attempt is the best
visible-data-supported hypothesis with the above limitation. Stop after checking
visible examples and executing both queries; hidden correctness is not available.
