# Working notes: 0005ab5b7704

## Current decision

Built a native matched-input family with
`column_order = left_to_right | body_density_desc`. The default is the byte-exact
canonical marker-column filter. The alternative first selects yellow-header
columns and measures their nonzero body occupancy, then sorts only those selected
columns by descending occupancy before packing the body.

The sampler gives marked columns distinct positive occupancies, forces a
non-positional density order, and includes an unmarked dense distractor so
sorting all columns cannot bypass marker selection. It supports 2–6 demos and
four query prefixes, including a populated 30×30 stress case.

## Handoff

The required 32-seed audit and an additional 256-seed teaching/stress sweep found
no surviving declared shortcut. Reviewer-ready authoring evidence is under
`checks/0005ab5b7704/`; exact-source owner qualification, acceptance, and any
training admission remain pending. Associated imported notes remain in
`evidence/associated_notes.jsonl`.
