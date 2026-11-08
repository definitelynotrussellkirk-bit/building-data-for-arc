"""Private episode-fixed motion settings and count-stable matched inputs."""
from pathlib import Path
import importlib.util

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("_gravity88e364bc_sampler",HERE/"sampler.py")
BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)


def setting(settings):
    if type(settings) is not dict or set(settings)!={"motion"}:
        raise ValueError("settings must contain exactly motion")
    return BASE.motion(settings["motion"])


def program(settings):
    return (HERE/("canonical.rkt" if setting(settings)=="toward_head" else "toward_tail.rkt")).read_text()


def analyze(grid,settings):
    return BASE.analyze(grid,setting(settings))


def mirror(grid,settings):
    return analyze(grid,settings)["output"]


def first_stage(grid,settings):
    mode=setting(settings);result=BASE.parse(grid)
    regions=[]
    for region in result["regions"]:
        dr,dc=region["direction"]
        regions.append({**region,"direction":[dr,dc] if mode=="toward_head" else [-dr,-dc]})
    return {"legends":result["legends"],"regions":regions}


def generate(seed,settings,demos=2,queries=4):
    mode=setting(settings);BASE.integer(seed,0,2**63-1,"seed")
    BASE.integer(demos,2,6,"demos");BASE.integer(queries,1,4,"queries")
    train,test=BASE.lesson_inputs(seed)
    def pairs(inputs):
        return [{"input":[r[:] for r in g],"output":BASE.solve(g,mode)} for g in inputs]
    return {"train":pairs(train[:demos]),"test":pairs(test[:queries]),"program_solution":program(settings)}
