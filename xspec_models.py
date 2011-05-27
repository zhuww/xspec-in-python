import copy
from round import TexStyle
from resetdefault import resetdefaults

import sys,os

XSPEC_MODULE_PATH = os.path.split(sys.modules['xspec'].__file__)[0]

class parameter(object):
    """A parameter class used to store the value of a particular parameter."""
    @resetdefaults
    def __init__(self,value=None,name='',unit=''):
        if len(value) == 6:
            (self.initvalue,self.delta,self.min,self.bot,self.top,self.max)=(x for x in value)
            self.name=name
            self.unit=unit
            self.bindto = ''
            self.frozen = 0
        else:
            raise Parameter_Init_Length_MissMatch
    def __set__(self, obj, value):
        print 'set %s to %s' % (self, value)
        self.setvalue(value)
    def setvalue(self,value):
        if isinstance(value, (list, tuple)):
            if len(value) == 6:
                (self.initvalue,self.delta,self.min,self.bot,self.top,self.max)=(x for x in value)
            elif value[0] == '=':
                self.bindto = value[0]+' '+value[1]
            elif len(value) == 1:
                self.initvalue = value[0]
            elif len(value) == 2:
                self.initvalue = value[0]
                self.delta = value[1]
        elif isinstance(value, (float, int)):
            self.initvalue = value
        elif isinstance(value, (parameter)):
            #self = copy.deepcopy(value)
            self = value
            print 'here copy commence: ', id(self), id(value)
        else:
            raise Parameter_Value_Length_MissMatch
    def freeze(self):
        #self.delta=-1.*abs(float(self.delta))
        self.frozen = 1
    def thaw(self):
        self.frozen = 0
    def unbind(self):
        self.bindto = ''
    @resetdefaults
    def bind(self,target=''):
        self.bindto = '= '+str(target)
    def __str__(self):
        try:
            return '%s %s' % ( TexStyle(self.bestvalue), self.unit)
        except:
            return '%s %s (inital value)' % (self.initvalue, self.unit)
    def __repr__(self):
        if self.bindto:
            return self.bindto
        elif self.frozen:
            return '%s  %s  %s  %s  %s %s' % (self.initvalue,-1.*abs(float(self.delta)),self.min,self.bot,self.top,self.max)
        else:
            return '%s  %s  %s  %s  %s %s' % (self.initvalue,self.delta,self.min,self.bot,self.top,self.max)
    

class basemodel(object):
    """ A base class used as the building block of a xspec model classes. In this class the basic model components and arismatic operations were defined. """
    _repr_expr=''
    __parameter_names__ = []
    def __init__(self):
        self.parameters=[]
        self.parents=[(self,0)]
    def __add__(self, other):
        selfparalength=len(self.parameters)
        otherparalength=len(other.parameters)
        third=basemodel()
        third.parameters=self.parameters+other.parameters
        third.parents=self.parents[:]
        if len(other.parents) > 1:
            for parent in other.parents:
                third.parents.append((parent[0],parent[1]+selfparalength))
        else:
            third.parents.append((other,selfparalength))
        third._repr_expr=self._repr_expr+'+'+other._repr_expr
        third.parlength=len(third.parameters)
        return third
    def __mul__(self, other):
        selfparalength=len(self.parameters)
        otherparalength=len(other.parameters)
        third=basemodel()
        third.parameters=self.parameters+other.parameters
        third.parents=self.parents[:]
        if len(other.parents) > 1:
            for parent in other.parents:
                third.parents.append((parent[0],parent[1]+selfparalength))
        else:
            third.parents.append((other,selfparalength))
        if '+' in self._repr_expr:
            third._repr_expr='('+self._repr_expr+')'+'*'+other._repr_expr
        elif '+' in other._repr_expr:
            third._repr_expr=self._repr_expr+'*'+'('+other._repr_expr+')'
        else:
            third._repr_expr=self._repr_expr+'*'+other._repr_expr
        third.parlength=len(third.parameters)
        return third
    def __rmul__(self,multiplier):
        if multiplier > 1:
            new=basemodel()
            new=copy.deepcopy(self)
            new.parameters=copy.deepcopy(self.parameters)
            new.update()
            length=len(new.parameters)
            for i in range(multiplier-1):
                for j in range(length):
                    new.parameters.append(copy.deepcopy(new.parameters[j]))
                    new.parameters[-1].group=i+1
            return new
        else:
            return self
    def update(self):
        for pars in [x for x in self.parameters if x.group == 0]:
            object.__setattr__(self, pars.name, pars)
    def updateparents(self):
        for (parent,offset) in self.parents:
            for i in range(parent.parlength):
                parent.parameters[i]=self.parameters[i+offset]
            parent.update()
    def __setattr__(self, name, value):
        if name in self.__parameter_names__ and name in self.__dict__.keys():
            self.__dict__[name].setvalue(value)
        else:
            self.__dict__[name] = value
    def __str__(self):
        return self._repr_expr
    def __repr__(self):
        return '%s model at %s' % (str(self),id(self))
    #def __call__(self,*args):
        #new=self.__class__(*args)
        #return new

#class bbody(basemodel):
    #_repr_expr='bbody'
    #defaultparameters="""0.2       0.01     0.0001       0.01        100        200
                  #1       0.01          0          0      1e+24      1e+24"""
    #def __init__(self, kT=0.1):
        #basemodel.__init__(self)
        #for lines in self.defaultparameters.split('\n'):
            #self.parameters.append(parameter(lines.split()))
        #for par in self.parameters:
            #par.model=repr(self)
        #self.kT=self.parameters[0]
        #self.norm=self.parameters[1]
        #self.kT.name='kT'
        #self.kT.unit='keV'
        #self.norm.name='norm'
        #self.norm.unit=''
        #self.kT.initvalue=kT
        #self.parlength=len(self.parameters)
    #def update(self):
        #try:
            #self.kT=self.parameters[0]
        #except:pass
        #try:
            #self.norm=self.parameters[1]
        #except:pass

class bbody(basemodel):
    _repr_expr='bbody'
    defaultparameters="""0.2       0.01     0.0001       0.01        100        200
                  1       0.01          0          0      1e+24      1e+24"""
    def __init__(self, kT=0.1):
        basemodel.__init__(self)
        lines = self.defaultparameters.split('\n')
        self.kT = parameter(lines[0].split(), name='kT', unit='keV')
        self.norm = parameter(lines[1].split(), name='norm', unit='')
        self.__parameter_names__ = ['kT', 'norm']
        self.parameters.append(self.kT)
        self.parameters.append(self.norm)
        for par in self.parameters:
            par.model=repr(self)
            par.group=0
        self.parameters[0].initvalue=kT
        self.parlength=len(self.parameters)
    def update(self):
        try:
            object.__setattr__(self,'kT',self.parameters[0])
        except:pass
        try:
            object.__setattr__(self,'norm',self.parameters[1])
        except:pass

class wabs(basemodel):
    _repr_expr='wabs'
    defaultparameters="""1      0.001          0          0     100000      1e+06"""
    def __init__(self, nH=0.1):
        basemodel.__init__(self)
        for lines in self.defaultparameters.split('\n'):
            self.parameters.append(parameter(lines.split()))
        for par in self.parameters:
            par.model=repr(self)
            par.group=0
        self.nH=self.parameters[0]
        self.nH.name='nH'
        self.nH.unit='$10^{22}$cm$^{-2}$'
        self.nH.initvalue=nH
        self.__parameter_names__ = ['nH']
        self.parlength=len(self.parameters)
    def update(self):
        try:
            object.__setattr__(self,'nH',self.parameters[0])
        except:pass


class const(basemodel):
    _repr_expr='constant'
    defaultparameters="""1       0.01          0          0      1e+10      1e+10"""
    def __init__(self, constant=1.):
        basemodel.__init__(self)
        for lines in self.defaultparameters.split('\n'):
            self.parameters.append(parameter(lines.split()))
        for par in self.parameters:
            par.model=repr(self)
            par.group=0
        self.parameters[0].name='const'
        self.parameters[0].unit=''
        self.constant=self.parameters[0]
        self.parameters[0].initvalue=constant
        self.__parameter_names__ = ['const']
        self.parlength=len(self.parameters)
    def update(self):
        try:
            object.__setattr__(self,'constant',self.parameters[0])
        except:pass


class dummy(basemodel):
    _repr_expr=''
    __parameter_names__ = []
    def __init__(self):
        basemodel.__init__(self)



def parsemodel(name):
    parsestring = """
class %(name)s(basemodel):
    _repr_expr='%(name)s'
    def __init__(self):
        self.pardata1 = open(XSPEC_MODULE_PATH+'/%(name)s.dat1', 'r').readlines()
        self.pardata2 = open(XSPEC_MODULE_PATH+'/%(name)s.dat2', 'r').readlines()
        basemodel.__init__(self)
        for lines in self.pardata1:
            self.parameters.append(parameter(lines.split()))
        for par in self.parameters:
            par.model=repr(self)
            par.group=0
        for lines in self.pardata2:
            linestr=lines.split()
            (numbkey, index, comp, modelname, parname, unit) = linestr[:6]
            self.__dict__[parname] = self.parameters[int(index)-1]
            self.__dict__[parname].name=parname
            self.__parameter_names__.append(parname)
            try:float(unit)
            except:self.__dict__[parname].unit=unit
        self.parlength=len(self.parameters)
    #def update(self):
        #for pars in [x for x in self.parameters if x.group == 0]:
            #object.__setattr__(self, pars.name, pars)
""" % {'name':name}
    exec(parsestring)
    clsobj = locals()[name]
    globals().update({name:clsobj})



#for model in ['powerlaw', 'nsa', 'sedov', 'vsedov', 'nsa', 'vnei', 'vpshock']:
    #eval("%(model)s = load_model('%(model)s')" % {'model':model})

#class InnerModel(basemodel):pass

for model in ['powerlaw', 'nsa', 'sedov', 'vsedov', 'nsa', 'vnei', 'vpshock', 'cflux', 'bbodyrad']:
    parsemodel(model)
