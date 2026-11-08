# Proposed busiest-activated-column endpoint treatment

The episode-fixed parameter is `endpoint_treatment`:

- `preserve` is the exact canonical authority: fill every black center whose
  immediate vertical neighbors are green, leaving the green endpoints unchanged.
- `highlight_busiest` first performs that fill (stage A), counts the newly red
  centers in each column (the input-dependent intermediate), chooses the leftmost
  uniquely busiest activated column, and recolors its green cells blue (stage B).

Inputs are sampled independently of the private setting. The family supports
2–6 demonstrations and exactly four distinct queries. The fourth query is a
substantive 30×30 scene with target chains, crossed frequency controls, blocked
and wrong-color gaps, boundary contact, and content across the canvas.

Focused checks and protected-Racket evidence are retained under `evidence/`.
Owner qualification and acceptance remain required; this prototype is not
training-admitted.
