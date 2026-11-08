"""Native resources are confined to this directory; no catalog or gold lookup."""
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent

def _load(name):
    spec=importlib.util.spec_from_file_location(__name__+"_"+name,HERE/(name+".py"))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

model=_load("family")
public_io=_load("public_io")
public_view=public_io.view

def program(settings):
    if type(settings) is not dict or set(settings)!={"finish"} or settings["finish"] not in ("dock","bridge_top"):
        raise ValueError("Expected exactly finish=dock|bridge_top")
    return (HERE/("canonical.rkt" if settings["finish"]=="dock" else "bridge_top.rkt")).read_text()

def generate(seed,settings,demos=3,queries=4):
    text=program(settings)
    if type(seed) is not int:raise ValueError("seed must be an integer")
    if type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or not 1<=queries<=4:
        raise ValueError("Supported counts are 2..6 demos and 1..4 queries")
    finish=settings["finish"]
    label=lambda g:{"input":g,"output":model.solve(g,finish)}
    train=[label(model.scene(seed,i)) for i in range(demos)]
    order=list(range(4));model.stream(seed,"presentation").shuffle(order)
    bank=[label(model.scene(seed,i,True)) for i in order]
    return {"train":train,"test":bank[:queries],"program_solution":text,
            "private":{"query_source_indices":order[:queries],"settings":dict(settings)}}
