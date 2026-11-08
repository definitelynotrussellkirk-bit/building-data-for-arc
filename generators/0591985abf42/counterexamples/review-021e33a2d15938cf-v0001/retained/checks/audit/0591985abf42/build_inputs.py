from __future__ import annotations
import importlib.util, json
from pathlib import Path
ROOT=Path('/mnt/data/arcpuzzles_review_035633')
path=ROOT/'repo/generators/0591985abf42/generator.py'
spec=importlib.util.spec_from_file_location('audit_0591985abf42', path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
inputs=[mod.generate(1,i,difficulty='medium') for i in range(5)]
for i,g in enumerate(inputs):
    assert not mod.self_check(g,difficulty='medium'), (i,mod.self_check(g,difficulty='medium'))
(ROOT/'checks/audit/0591985abf42/input.json').write_text(json.dumps(inputs,separators=(',',':'))+'\n')
