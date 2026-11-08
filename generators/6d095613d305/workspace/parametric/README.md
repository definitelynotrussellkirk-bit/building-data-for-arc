# Parametric traced-path emphasis — `6d095613d305`

The private episode parameter `path_emphasis` has three settings:

- `canonical`: the byte-exact source rule;
- `longer`: build both canonical traces, then recolor the uniquely longer trace to 8 away from intersections;
- `shorter`: do the same for the uniquely shorter trace.

Step A follows all row-major waypoints with horizontal-first bends and produces
two exact input-dependent trace-cell sets plus their lengths. The intermediate is
the selected longer/shorter path color and cell set. Step B consumes that set to
recolor only its non-overlap cells; a wrong selected trace changes the final
output. Inputs are matched across settings, alternate which sorted input color
has the longer trace, contain a real intersection, and support 2–6 demos plus
1–4 independent queries. The query bank includes four distinct large canvases,
including substantive 30×30 stress.

`preflight_compat.py` is a task-local authoring helper for the legacy canonical
record, whose single test pair is stored as a mapping instead of a list. It
normalizes that one collection only, preserves the original record hash, and
delegates source binding, Racket execution, and receipt construction to the
packet's stock authoring preflight.
