# public_eval_3dc255db

The canonical rule treats each mixed-color 8-connected component as a
spacecraft.  Its majority color is the hull and its minority cells are stored
exhaust particles.  A geometric nose is inferred from a unique extreme hull
tip, using alignment with the widest cross-sections and particle depth to
resolve otherwise plausible orientations.  Stored particles are erased and
moved from the nose in the inferred direction, clipped by the canvas.

The native family adds episode-fixed `extension`: canonical `particle_count`
or `to_edge`.  Both settings share object extraction, role classification,
direction inference, particle clearing, and color.  Only the ray-length policy
changes.  Generated examples include all four headings, varying particle
counts, singleton distractors, count-independent streams, and a dense 30x30
query.

Owner registration, exact-source review, qualification, and acceptance remain
pending.  This authoring source is not training-admitted.
