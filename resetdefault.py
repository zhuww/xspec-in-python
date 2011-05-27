from copy import deepcopy
def resetdefaults(f):
    fdefaults = f.func_defaults
    def refresher(*args, **kwds):
        f.func_defaults = deepcopy(fdefaults)
        return f(*args, **kwds)
    return refresher

#@resetdefaults
#def packitem(item, pkg=[]):
    #pkg.append(item)
    #return pkg

#packitem('abc')
#packitem('abc')
#print packitem('abc')

#def dummy(item=[]):pass
#print dummy.func_defaults
