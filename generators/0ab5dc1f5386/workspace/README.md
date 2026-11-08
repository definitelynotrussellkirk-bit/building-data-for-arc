# Workspace

`reference_probe.py` is the reusable independent semantic probe for task `0ab5dc1f5386`.

It provides:

- canonical row/pair loading and normalized rule-hash calculation;
- an intended Python oracle independent of `generator.py`;
- five explicit rival outputs (`rotate_to_fit`, `last_match`, `reuse_shape`, `flatten_shape`, and `occurrence_use`);
- profile and loose-crop inspection helpers;
- optional real-Racket execution through the protected bridge.

The selected implementation remains `../generator.py`; workspace code is never automatically selected. Do not use canonical loading or Racket helpers during a visible-only solve episode because they expose answers. Task-local tests import this probe so generator declarations are checked against an independent implementation rather than against themselves.
