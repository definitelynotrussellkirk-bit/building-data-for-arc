# 4ebdc8d865ce target-degree family

This native prototype keeps the exact canonical program as
`target_degree=0` and adds `target_degree=1`, which recolors endpoints rather
than isolated cells.

The common input grammar contains orthogonally isolated cells, diagonal-only
contacts, horizontal and vertical pairs, endpoints in components larger than
two cells, degree-2/3/4 cells, and both boundary and interior targets.  Inputs
are matched across settings.  Demonstration and query prefixes are independent;
2–6 demonstrations and 1–4 queries are supported.  The fourth query is a dense
30×30 boundary case.

Sequential dependency:

1. **A** computes each foreground cell's orthogonal color-2 neighbor count.
2. The input-dependent intermediate is the per-cell degree map.
3. **B** recolors exactly cells whose derived degree equals the episode-fixed
   `target_degree`.

`self_audit.py` replays labels through protected Racket, checks finite rivals,
public projection, matched inputs, count boundaries, and the wrong-intermediate
causal witness.
