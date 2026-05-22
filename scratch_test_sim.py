import sys
import builtins

orig_import = builtins.__import__

def my_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == 'transformers':
        import traceback
        traceback.print_stack()
    return orig_import(name, globals, locals, fromlist, level)

builtins.__import__ = my_import

try:
    from src.aegisdesk.core.pipeline import execute_rag_pipeline
except Exception as e:
    pass
