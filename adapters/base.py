__author__ = 'joelvogt'

def function_adapter_mapper(func, adapter):
    def onCall(*args, **kwargs):
        return adapter(func(*args, **kwargs))
    return onCall