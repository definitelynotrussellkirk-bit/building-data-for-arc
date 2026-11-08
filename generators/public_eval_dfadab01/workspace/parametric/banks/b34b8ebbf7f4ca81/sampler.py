"""Complement the retained lane bank with true overlapping-stamp compositions.

Canonical generation stays unchanged. The first two teaching scenes show opposite
later glyphs overwriting the square frame. Query zero retains the exact old bank;
the other queries exercise several overlap offsets. Seed and index, never hidden
settings, determine geometry. All labels still come from the retained interpreter.
"""
from pathlib import Path
import importlib.util
import hashlib
import sys

path=Path(__file__).resolve().with_name('prototype.py')
name='_dfad_overlap_base_'+hashlib.sha256(str(path).encode()).hexdigest()
spec=importlib.util.spec_from_file_location(name,path)
P=importlib.util.module_from_spec(spec);sys.modules[name]=P;spec.loader.exec_module(P)

def scene(seed: int, index: int, *, query: bool=False) -> list[list[int]]:
    original=P.scene(seed,index,query=query)
    if query and index%4==0:
        return original
    transposed=original[0][4]!=2
    g=list(map(list,zip(*original))) if transposed else original
    r=len(g)-10
    # Replace only the small auxiliary chain, not either teaching mass contest.
    # The original foreground legend at columns 0..4 remains intact.
    g[r][8]=2
    g[r][12]=0
    dr,dc=(1,1) if not query or index%4==1 else (2,2) if index%4==2 else (1,2)
    g[r+dr][8+dc]=3 if index%2==0 else 5
    return list(map(list,zip(*g))) if transposed else g
