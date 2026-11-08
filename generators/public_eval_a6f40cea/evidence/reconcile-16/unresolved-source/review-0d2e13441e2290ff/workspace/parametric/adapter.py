"""Private native adapter; no sibling-checkout or parent-directory resources."""
import importlib.util
from pathlib import Path
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_a6_model_'+str(BASE),BASE/'model.py')
model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
VALUES=('restart_hidden','continue_visible')
def setting(settings):
    if not isinstance(settings,dict) or set(settings)!={'phase_policy'} or type(settings['phase_policy']) is not str or settings['phase_policy'] not in VALUES:raise ValueError('invalid phase policy')
    return settings['phase_policy']
def program(settings):
    value=setting(settings)
    return (BASE/('canonical.rkt' if value==VALUES[0] else 'continue.rkt')).read_text()
def generate(seed,settings,demos,queries):
    value=setting(settings)
    if type(seed) is not int or type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or queries!=4:raise ValueError('require integer seed, 2..6 demos and four queries')
    pairs=[]
    for i in list(range(demos))+list(range(6,10)):
        g=model.scene(seed,i);pairs.append({'input':g,'output':model.solve(g,value)})
    return {'train':pairs[:demos],'test':pairs[demos:],'program_solution':program(settings)}
