# Native parametric frame-docking family

`finish=dock_only` is the exact canonical rule. `finish=contact_projection`
first performs that rigid docking step, then finds the cyan frame cells touched
by the docked red shape and projects those sparse contact positions inward
through the hollow frame using color 4.

The causal chain is substantive: A computes the input-dependent docked red cells;
the intermediate is the exact post-dock contact set; B chooses the interior rays
from that set. `rules/wrong_order.rkt` performs B before A and is retained only
as a bounded counterfactual witness, not as an admitted setting.
