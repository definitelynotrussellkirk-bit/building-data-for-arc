"""Episode-fixed sequence direction over matched geometric bar scenes."""
from pathlib import Path
import importlib.util
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("_bars291dc1e1_sampler",HERE/"sampler.py")
BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)

def setting(settings):
    if type(settings) is not dict or set(settings)!={"stack_order"}:raise ValueError("settings must contain exactly stack_order")
    return BASE.stack_order(settings["stack_order"])

def program(settings):return (HERE/("canonical.rkt" if setting(settings)=="forward" else "reverse.rkt")).read_text()
def mirror(grid,settings):return BASE.solve(grid,setting(settings))
def analyze(grid,settings):return BASE.analyze(grid,setting(settings))
def first_stage(grid,settings):return BASE.first_stage(grid,setting(settings))

def generate(seed,settings,demos=3,queries=4):
    order=setting(settings);BASE.integer(seed,0,2**63-1,"seed");BASE.integer(demos,3,6,"demos");BASE.integer(queries,1,4,"queries")
    train,test=BASE.lesson_inputs(seed)
    def pairs(inputs):return [{"input":[r[:] for r in g],"output":BASE.solve(g,order)} for g in inputs]
    return {"train":pairs(train[:demos]),"test":pairs(test[:queries]),"program_solution":program(settings)}
