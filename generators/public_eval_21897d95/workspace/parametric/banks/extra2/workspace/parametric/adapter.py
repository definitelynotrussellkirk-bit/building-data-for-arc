"""Native claims; all labels are independently replayed by protected Racket."""
from pathlib import Path
import importlib.util
HERE=Path(__file__).resolve().parent
_s=importlib.util.spec_from_file_location('_region_arrows_'+str(HERE),HERE/'engine.py');engine=importlib.util.module_from_spec(_s);_s.loader.exec_module(engine)
def setting(settings):
 if type(settings) is not dict or set(settings)!={'ink'} or type(settings['ink']) is not str or settings['ink'] not in engine.SETTINGS:raise ValueError('expected exactly ink=payload|source_color')
 return settings['ink']
def program(settings):
 return (HERE/('canonical.rkt' if setting(settings)=='payload' else 'source_color.rkt')).read_text()
def generate(seed,settings,demos,queries):
 mode=setting(settings);engine.integer(seed,0,2**63-1,'seed');engine.integer(demos,2,6,'demos');engine.integer(queries,1,4,'queries')
 def pairs(kind,count):
  out=[]
  for i in range(count):
   g=engine.scene(seed,i,kind);out.append({'input':g,'output':engine.solve(g,mode)})
  return out
 return {'train':pairs('demo',demos),'test':pairs('query',queries),'program_solution':program(settings)}
