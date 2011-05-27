"""An xspec tcl script generator in python. 
Author: Weiwei Zhu
email:zhuwwpku@gmail.com
"""
import os,sys,copy
from datetime import *
#from publishstyle import *
from round import *
#import MJD
import cPickle
#from fileio import *
from xspec_models import *
from resetdefault import resetdefaults
from math import *

#I am trying to implement a set of objects and methods to perform spectra fitting.
old_stdout = sys.stdout

def uniquename():
    """Create an unique name for the working directory or the save files. The name start with when the python code was run %y-%m-%d_%Hh%Mm%Ss and then followed by '%s_%s_%s_%s' % (when,who,where,which), 'which' points to the process id.""" 
    who=os.environ['LOGNAME']
    where=os.uname()[1]
    which=os.getpid()
    when=datetime.now().strftime("%y-%m-%d_%Hh%Mm%Ss")
    what=__file__
    return "%s_%s_%s_%s" % (when,who,where,which)



def simpleformat(parlist):
    return str(parlist).replace('[','').replace(']','').replace(',','')

class data(object):
    """Data class that can be fitted using the fit() class. It takes a list of spectrum groups to initialize:
        dataset = data([[spec1, spec2],[spec3],[spec4]]).
        In this example, spec1 and spec2 belongs to the first spectra group, and spec3 and spec4 are the second and third group."""

    def justifyname(self,file):
        if file[0] == '/' or file[0:1] == '~/':pass
        else:
            basepath=os.getcwd()
            file = basepath+'/'+file
        if os.access(file,os.R_OK):return file
        else:raise '%s can not be found' % file 
        

    def __init__(self,filelist=None):
        """Take a list (two layer) of spectrums (the file name and path of them) and make a data instance."""
        if filelist == None: filelist=[]
        self.filelist=filelist
        #self.ignore_tag="""ig bad \nig **:0.0-0.3 **:10.0-**\n"""
        self.ignore_tag="""ig bad\n"""
        self.num_of_groups=len(filelist)
        self.scriptlog=""
        self.specindex = []
        self.group_offset = []
        self.datalist = []
        k=1
        for grp in range(len(self.filelist)):
            self.specindex.append([])
            self.group_offset.append(k)
            for spec in range(len(self.filelist[grp])):
                self.filelist[grp][spec]=self.justifyname(self.filelist[grp][spec])
                self.specindex[-1].append(k)
                file=self.filelist[grp][spec]
                if file[0] == '/' or file[0:1] == '~/':
                    fullpathfile=file
                else:
                    basepath=os.getcwd()
                    fullpathfile=basepath+'/'+file
                self.datalist.append([grp+1,k,fullpathfile,"ig **:0.0-0.3 **:10.0-**\n"])
                k+=1

        
    def addspec(self, specfile):
        """Add a new spectrum file to the last data group."""
        specfile=self.justifyname(specfile)
        self.filelist[-1].append(specfile)
        print "spectrum %s added to group %i" % (specfile, len(self.filelist))
    @resetdefaults
    def newgroup(self,newgroup=[]):
        """Append new sepctra group."""
        for spec in range(len(newgroup)):
            newgroup[spec]=self.justifyname(newgroup[spec])
        self.filelist.append(newgroup)
        self.num_of_groups+=1
        print "group %i added" % (len(self.filelist))

    def ignore(self, Emin, Emax, group=None, spec=None):
        '''Ignore all channels between Emin and Emax '''
        if spec:
            self.datalist[spec-1][3]+= 'ignore %i:%s-%s\n' % (self.datalist[spec-1][1], Emin,Emax)
        elif group:
            for data in self.datalist:
                if data[0] == group:
                    data[3]+= 'ignore %i:%s-%s\n' % (data[1],Emin,Emax)
        else:
            for data in self.datalist:
                data[3]+= 'ignore %i:%s-%s\n' % (data[1],Emin,Emax)

    def notice(self, Emin, Emax, group=None,spec=None):
        '''Notice energy range Emin-Emax. '''
        if spec:
            self.datalist[spec-1][3]+= 'notice %i:%s-%s\n' % (self.datalist[spec-1][1], Emin,Emax)
        elif group:
            for data in self.datalist:
                if data[0] == group:
                    data[3]+= 'notice %i:%s-%s\n' % (data[1],Emin,Emax)
        else:
            for data in self.datalist:
                data[3]+= 'notice %i:%s-%s\n' % (data[1],Emin,Emax)

    def notice_only(self, Emin, Emax, group=None, spec=None):
        '''This method ignores everything outside of the Emin-Emax range. It also overright the ignore tag of the spectrum.'''
        if spec:
            self.datalist[spec-1][3] = 'ignore %i:0.0-%s %s-**\n' % (self.datalist[spec-1][1], Emin,Emax)
        elif group:
            for data in self.datalist:
                if data[0] == group:
                    data[3] = 'ignore %i:00-%s %s-**\n' % (data[1],Emin,Emax)
        else:
            for data in self.datalist:
                data[3] = 'ignore %i:0.0-%s %s-**\n' % (data[1],Emin,Emax)

    def __add__(self,other):
        filelist = self.filelist + other.filelist
        third=data(filelist)
        datalist = self.datalist + other.datalist
        for i in range(len(third.datalist)):
            ignore_tag = datalist[i][3]
            ignore_tag = ignore_tag.replace(ignore_tag[7], str(i+1))
            third.datalist[i][3]= ignore_tag
        return third
    def load(self):
        """print the xspec command lines for loading the spectra."""
        res=""
        for data in self.datalist:
            res+="data %i:%i %s\n%s" % tuple(data)
        res+=self.ignore_tag
        return res
    def __str__(self):
        return 'a %s instance at %s' % (self.__class__,id(self))
    #def __repr__(self):pass

def loadmodel(modelfile):
    """To load in a model from a model file saved from xspec."""
    file= open(modelfile, 'r')
    array=file.readlines()
    modelline=0
    for lines in array:
        linestr=lines.split()
        if linestr[0]=='model':
            modelstr=lines[7:-1].replace(' ','')
            break
        else:
            modelline+=1
    file.close()
    models=[model for model in modelstr.replace('(',',').replace('+',',').replace(')',',').replace('*',',').split(',')  if not model=='']
    comp=[]
    for i in range(len(models)):
        comp.append(eval(models[i]+'()'))
        modelstr=modelstr.replace(models[i],'comp[%i]' % i,1)
    try:
        index=0
        while 1:
            index=modelstr.index('(',index+1)
            if not index==0:
                if not modelstr[index-1]=='+' and not modelstr[index-1]=='*':
                    modelstr=modelstr[:index]+'*'+modelstr[index:]
                    index+=1
    except(ValueError):pass
    try:
        index=0
        while 1:
            index=modelstr.index(')',index+1)
            if not index==len(modelstr)-1: 
                print index
                if not modelstr[index+1]=='+' and not modelstr[index+1]=='*':
                    modelstr=modelstr[:index+1]+'*'+modelstr[index+1:]
                    index+=1
    except(ValueError):pass
    model=eval(modelstr)
    model.parlength=len(model.parameters)
    print model,modelstr,model.parameters
    fileparlength=len(array[modelline+1:])
    num_of_groups = fileparlength / model.parlength
    if fileparlength % model.parlength == 0 and not num_of_groups == 0:
        model=num_of_groups*model
        i=0
        for line in array[modelline+1:]:
            model.parameters[i].setvalue(line.split())
            i+=1
        model.comp=comp
        return model
    else:
        print fileparlength, model.parlength, num_of_groups
        raise ParameterLengthError


class fit(object):
    """A fit class that takes a data set and fit it with a model. It works like:\nafit = fit(datainstance,model). \nOr more specificly:\n abs=wabs()\nbb=bbody()\nabsbb=abs*bb\nbbfit = fit(datainstance,absbb)"""
    random_steps=100
    def _fillinparameters(self):
        """If necessary, multiply the parameters list to fit the number of data groups."""
        model=self.data.num_of_groups*self.model
        for par in model.parameters:
            self.parameters.append(copy.deepcopy(par))
    @resetdefaults
    def __init__(self,data,model=dummy(),modelfile=''):
        self.parameters=[]
        self.scriptlog=""
        self.data=data
        if modelfile=='':
            self.model=model
            self._fillinparameters()
        else:
            self.model=loadmodel(modelfile)
            for par in self.model.parameters:
                self.parameters.append(copy.deepcopy(par))
            ratio=len(self.parameters) / self.model.parlength
            if ratio == 1:
                """Only one set of model parameters were provided for the data, needed to multiply them to fit the number of data groups."""
                self._fillinparameters()
            elif ratio == self.data.num_of_groups:
                """Enough model parameters have been provided by the model file, no need to inflate the parameter list."""
                pass
            else:
                raise Parameter_Init_Length_MissMatch
        self.tempdir='.'+uniquename()
        self.fitted=False
        self.didcalflux=False
        self.fitforparlist=[]
                

    def findpar(self, **kargs):
        """Find the index of centain parameters in the parameter list of the fit instance. \nExample:\nafit.findpar(name='kT', group=[0,1], model=bb)"""
        def testkeymatch(par, key, value):
            if par.__dict__.has_key(key):
                if isinstance(value, list):
                    if value.__contains__(par.__dict__[key]):return True
                    else:return False
                elif isinstance(value, basemodel):
                    if repr(value) == par.model:return True
                    else:return False
                else:
                    if par.__dict__[key] == value:return True
                    else:return False
            else:
                print 'Key %s does not exist for par %s of model %s in group %i' % (key, par.name, par.model, par.group)
                return False
            

        res=[]
        for i in range(len(self.parameters)):
            if all([testkeymatch(self.parameters[i],key,kargs[key]) for key in kargs.keys()]):res.append(i+1)
            else:pass
        return res


    def freeze(self, fixparindexlist=None):
        """A function that mimics the freeze command in xspec, take a list of parameters and freeze them all to their current values."""
        if fixparindexlist == None:fixparindexlist=[]
        if isinstance(fixparindexlist,str):
            fixparindexlist=self.findpar(fixparindexlist)
            self.freeze(fixparindexlist)
        elif isinstance(fixparindexlist,int):
            self.parameters[fixparindexlist-1].freeze()
            print 'freeze %i\n' % (fixparindexlist)
        elif isinstance(fixparindexlist,list):
            freezecmd='freeze '
            for everypar in fixparindexlist:
                self.parameters[everypar-1].freeze()
                freezecmd+=' %i ' % everypar
            freezecmd+='\n'
            print freezecmd
        else:
            raise  """Usage: model.freeze([list of parameters to freeze]) """
        self.scriptlog+="""freeze(%s)\n""" % (fixparindexlist)


    def thaw(self, fixparindexlist=None):
        """A function that mimics the thaw command in xspec, take a list of parameters and thaw them if they were frozen."""
        if fixparindexlist == None:fixparindexlist=[]
        if isinstance(fixparindexlist,str):
            fixparindexlist=self.findpar(fixparindexlist)
            self.thaw(fixparindexlist)
        elif isinstance(fixparindexlist,int):
            self.parameters[fixparindexlist-1].thaw()
            print 'thaw %i\n' % (fixparindexlist)
        elif isinstance(fixparindexlist,list):
            thawcmd='thaw '
            for everypar in fixparindexlist:
                self.parameters[everypar-1].thaw()
                thawcmd+=' %i ' % everypar
            thawcmd+='\n'
            print thawcmd
        else:
            raise  """Usage: model.thaw([list of parameters to thaw]) """
        self.scriptlog+="""thaw(%s)\n""" % (fixparindexlist)

    def settozero(self,parlist=None):
        """Set the initial value of a parameter to zero. Now it's been simplified to `parameter=0`."""
        if parlist == None:parlist=[]
        if isinstance(parlist,int):
            self.settozero([parlist])
        elif isinstance(parlist,list):
            for eachpar in parlist:
                self.setpar(eachpar,0.)
                self.freeze(eachpar)
        else:raise DontUnderstandParlist, parlist

    def bind(self,bindlist=None):
        """A function that bind a list of parameters to the first one of them."""
        if bindlist == None:bindlist=[]
        if isinstance(bindlist,str):
            bindlist=self.findpar(bindlist)
            self.bind(bindlist)
        elif isinstance(bindlist,list):
            if not max(bindlist) > self.model.parlength:
                for eachpar in bindlist:
                    for j in range(1,self.data.num_of_groups):
                        nextpar=eachpar+j*self.model.parlength
                        self.parameters[nextpar-1].bind(eachpar)
                        print 'newpar %i =%i' % (nextpar,eachpar)
            else:
                for everypar in bindlist[1:]:
                    self.parameters[everypar-1].bind(bindlist[0])
                    print 'newpar %i =%i' % (everypar,bindlist[0])
        else:
            raise Must_Bond_A_List_of_Parameters
        self.scriptlog+="""bind(%s)\n""" % (bindlist)

    def unbind(self,unbindlist=None):
        """Stop binding these parameters to any other parameter."""
        if unbindlist == None: unbindlist=[]
        if isinstance(unbindlist,str):
            unbindlist=self.findpar(unbindlist)
            self.unbind(unbindlist)
        elif isinstance(unbindlist,list):
            if not max(unbindlist) > self.model.parlength:
                for eachpar in unbindlist:
                    for j in range(self.data.num_of_groups):
                        nextpar=eachpar+j*self.model.parlength
                        self.parameters[nextpar-1].unbind()
                        print 'newpar %i %s' % (nextpar, self.parameters[nextpar-1].initvalue)
            else:
                for everypar in unbindlist:
                    self.parameters[everypar-1].unbind()
                    print 'newpar %i %s' % (everypar, self.parameters[everypar-1].initvalue)
        else:
            raise Must_UnBond_A_List_of_Parameters
        self.scriptlog+="""unbind(%s)\n""" % (unbindlist)

    def setpar(self,index,initvalue=None,delta=None,min=None,bot=None,top=None,max=None):
        """A function that mimics the newpar command of xspec, use it to set the value of some parameter. It works like this: model.setpar(index,value)"""
        setparvalue=''
        values={'initvalue':initvalue,'delta':delta,'min':min, 'bot':bot, 'top':top, 'max':max}
        args=[]
        for key in ['initvalue','delta','min','bot','top','max']:
            if not values[key] == None:
                self.parameters[index-1].__dict__[key]=values[key]
                setparvalue+=",%s=%s" % (key,str(values[key]))
                args.append(values[key])
            else:
                args.append(self.parameters[index-1].__dict__[key])
        newparcmd='newpar %i' % index
        for arg in args:
            newparcmd+=' %s' % str(arg)
        newparcmd+='\n'
        print newparcmd
        self.scriptlog+="""setpar(%s%s)\n""" % (index,setparvalue)
    def __str__(self):
        return "a fit of %s with %s model" % (self.data,self.model)
    def __repr__(self):
        return "fit %s with %s model" % (self.data,self.model)
    def loaddata(self):
        """Alwasy use this function to load the data before commencing any orther action."""
        setting_model = "%s \nmodel %s\n" % (self.data.load(),self.model)
        model_parameters=''
        for i in range(len(self.parameters)):
            paraline=''
            #for j in range(len(self.parameters[i])):
                #paraline+=' %s ' % (self.parameters[i][j])
            paraline+=repr(self.parameters[i])
            paraline+='\n'
            model_parameters += paraline
        print setting_model+model_parameters
        #self.scriptlog+="""loaddata()\n"""


    def __call__(self,*args):
        """All the functions associated with this model class can be called by calling the model object with the command as parameters: a=model(...); a('loaddata','fit',...)"""
        command=args[0]
        if len(args)==1:
            eval("self.%s()" % (command))
        else:
            params=str(args[1:]).replace('[','').replace(']','')
            eval("self.%s(%s)" % (command,params))


    #@resetdefaults
    def fit(self,pars=None,steps=''):
        """Asking the fit instance to fit for the parameters as set by the 'pars' keyword input for number of steps as set by the 'steps' keyword. If no 'pars' were provided, all parameters will be fitted for uncertainties.  """
        print 'fit %s' % (steps)
        print """
set parsfile [open "%(tmpdir)s/pars" w]
foreach i { %(parlist)s } {
tclout param $i
set param $xspec_tclout
set paral [string trim $xspec_tclout]
regsub -all { +} $paral { } cpar
set lpar [split $cpar]
set par [lindex $lpar 0]
tclout sigma $i
set sigma $xspec_tclout
puts $parsfile "$par $sigma"
}
close $parsfile
cpd %(tmpdir)s/bestfit.ps/cps
setplot energy
setplot command label top " "
setplot command label file " "
setplot command time off
setplot command csize 1.3
setplot command font roman
setplot command label pos y
setplot command lwidth 3
setplot command label rotate
setplot command window 1 
setplot command viewport 0.1
#setplot command window 2 
#setplot command rescale y -1.5 1.5
pl ld del
pl ld del
""" % {'parlist':simpleformat(range(1,len(self.parameters)+1)), 'tmpdir':self.tempdir}


        if pars:
            if pars=='all':
                self.fitforparlist=range(1,len(self.parameters)+1)
                fitforparlist=simpleformat(self.fitforparlist)
            elif isinstance(pars, list):
                if max(pars) < self.model.parlength and not self.data.num_of_groups==1 :
                    increase=[self.model.parlength*(i+1) for i in range(self.data.num_of_groups-1)]
                    extpars=copy.deepcopy(pars)
                    for every in increase:
                        for each in pars:
                            extpars.append(each+every)
                else: 
                    extpars=pars
                self.fitforparlist=extpars
                fitforparlist=simpleformat(extpars)
            else:raise UnrecognizableParlist
            print """
foreach j { %s } {
err stop %i, , 1. $j
tclout err $j
set error [string trim $xspec_tclout]
regsub -all { +} $error { } cerror
set lerror [split $cerror]
set errl($j) [lindex $lerror 0]
set errr($j) [lindex $lerror 1]

tclout param $j
set param $xspec_tclout
set paral [string trim $xspec_tclout]
regsub -all { +} $paral { } cpar
set lpar [split $cpar]
set para($j) [lindex $lpar 0]
#rm "par$j"
set fileid($j) [open "%s/par$j" w]
puts $fileid($j) "$para($j) $errl($j) $errr($j)"
close $fileid($j)
}
    """ % (fitforparlist, self.random_steps,self.tempdir)


        print """
set stat [open "%s/chisq" w] 
tclout stat
set chisq $xspec_tclout
tclout dof
set dof $xspec_tclout
set ldof [split $dof]
set tdof [lindex $ldof 0]
#set prob [exec {%s/chisqpo} $tdof $chisq]
#puts $stat "$chisq $tdof $prob"
puts $stat "$chisq $tdof"
close $stat
set expo [open "%s/exposure" w]
set rate [open "%s/rate" w]
foreach j { %s } {
tclout expos $j
puts $expo "$xspec_tclout"
tclout rate $j
puts $rate "$xspec_tclout" 
}
save model %s/bestmodel
close $expo
close $rate
""" % (self.tempdir,XSPEC_MODULE_PATH,self.tempdir,self.tempdir,simpleformat(range(1,self.data.num_of_groups+1)),self.tempdir)
        self.scriptlog+="""fit(pars=%s,steps='%s')\n""" % (pars,steps)
        self.fitted=True

    def calflux(self,Elow,Eup,label=''):
        """Ask the fit instance to return the flux between same energys:\n afit.calflux(2.0,10.)\nOne can even ask the fit instance to label to returned flux.\nafit.calflux(2.0,10.,label='2-10absorbedflux') """
        print """
set flux [open "%(tmpdir)s/flux.tmp" a]
flux %(Elow)s %(Eup)s err %(steps)s 68
""" % {'tmpdir':self.tempdir,'Elow':Elow, 'Eup':Eup, 'steps':self.random_steps}
        print"""
set grpidx 1
foreach j { %s } {
tclout flux $j
puts $flux "group $grpidx:%s(%s-%s):$xspec_tclout"
incr grpidx
}
close $flux
""" % (simpleformat(self.data.group_offset),label,Elow,Eup)
        if label:
            self.scriptlog+="""calflux(%g,%g,label="%s")\n""" % (Elow,Eup,label)
        else:
            self.scriptlog+="""calflux(%g,%g)\n""" % (Elow,Eup)
        self.didcalflux=True


    def savemodel(self,modelfile=uniquename()):
        """Save the best-fit model in xspec."""
        cmd = 'save model '+modelfile+'\n'
        print cmd
        self.scriptlog+=cmd

    def cmd(self,cmd=''):
        """Run any xspec commands in xspec when the fit instance is excuting. """
        if cmd=='':pass
        else:
            cmd+='\n'
            print cmd
            self.scriptlog+=cmd

    def steppar(self, X, xarr, Y, yarr, xlog=False, ylog=False):
        """ Run the steppar command in xspec, API: fit.steppar(Npar1,[min, max, steps], Npar2, [min, max, steps], xlog=True, ylog=True)"""
        self._steppar = {}
        if len(xarr) == 2: xarr+=[30]
        if len(yarr) == 2: yarr+=[30]
        self._steppar.update({'X':X, 'Y':Y, 'xarr':xarr, 'yarr':yarr, 'xlog':xlog, 'ylog':ylog})
        mkarray = lambda xarr:[ xarr[0] +i*(xarr[1]-xarr[0])/xarr[2] for i in range(xarr[2]+1)]
        logarr = lambda xarr:[log(x, 10) for x in xarr]
        if not xlog:
            xarray = mkarray(xarr)
        else:
            xarray = [pow(10, x) for x in mkarray(logarr(xarr[:2])+[xarr[2]])]
        if not ylog:
            yarray = mkarray(yarr)
        else:
            yarray = [pow(10, x) for x in mkarray(logarr(yarr[:2])+[yarr[2]])]
        self._steppar.update({'xarray':xarray, 'yarray':yarray})
        if isinstance(X, basestring):
            X = self.findpar(name=X)
        if isinstance(Y, basestring):
            Y = self.findpar(name=Y)
        if xlog == True: 
            xlog ='log'
        else:
            xlog =''
        if ylog == True: 
            ylog ='log'
        else:
            ylog =''
        cmd = 'steppar %s %i %g %g %i %s %i %g %g %i\n' % (xlog, X, xarr[0], xarr[1], xarr[2], ylog, Y, yarr[0], yarr[1], yarr[2])
        print cmd
        self.scriptlog+=cmd
        print 'tclout steppar statistic'
        print 'set stepparout [open %s/steppar.out w ]' % (self.tempdir)
        print 'puts $stepparout "$xspec_tclout"'
        print 'close $stepparout'
        #print 'plot contour'



    def start(self,scriptfile='script.tcl',tempdir=''):
        """Preparing the script constructed using the fit instance."""
        if tempdir == '':tempdir='.'+uniquename()
        self.tempdir=tempdir
        self.basepath=os.getcwd()
        try:
            os.mkdir(tempdir)
        except:pass
        script=self.basepath+'/'+tempdir+'/'+scriptfile
        self.scriptfile=script
        #os.chdir(tempdir)
        sys.stdout = open(script,'w')
        print """
#This is script generated by the python xspec module written by Weiwei Zhu
#(zhuww@physics.mcgill.ca)
# Return TCL results for XSPEC commands.
set xs_return_result 1

# Keep going until fit converges.
query yes
"""
        self.loaddata()
        self.scriptlog="start('%s')\n" % scriptfile

    def end(self):
        print "exit"
        sys.stdout.close()
        sys.stdout=old_stdout

    def run(self, silently=False):
        '''Run the script prepared by the fit instance.'''
        self.end()
        self.scriptlog+='run()\n'
        if silently:
            os.system("xspec - %s > %s 2>&1" % (self.scriptfile, self.tempdir+'/log'))
        else:
            os.system("xspec - %s" % (self.scriptfile))
        who=os.environ['LOGNAME']
        where=os.uname()[1]
        which=os.getpid()
        when=datetime.now().strftime("%y-%m-%d_%Hh%Mm%Ss")
        self.history="The result of excuting %s on %s by %s at %s." % (self.scriptfile,where,who,when)
        if self.fitted:self.getpar()
        if self.didcalflux:self.getflux()
        if self.__dict__.has_key('_steppar'):
            stepparout = open('%s/steppar.out' % self.tempdir, 'r').read()
            chisq = [float(x) for x in stepparout.split()]
            self._steppar.update({'chisq':chisq})
        self.save()
        #os.chdir(self.basepath)

    def redo(self):
        """Redo what was done the last run of the fit instance in a new process."""
        print self.scriptlog
        commands = self.scriptlog.split('\n')
        print commands
        for command in commands[:-1]:
            eval('self.%s' % (command))
            continue

    def getpar(self):
        """Retreive the best-fit values and uncertainties of the parameters that were fitted using the fit instance. Usually run by the run method of fit."""
        os.chdir(self.tempdir)
        allpars = open("pars",'r')
        array = allpars.readlines()
        for i in range(len(self.parameters)):
            (value,sigma) = array[i].split()
            if sigma == '-1':
                self.parameters[i].bestvalue=(float(value),'(frozen)')
            else:
                self.parameters[i].bestvalue=(float(value),float(sigma))
        for i in self.fitforparlist:
            parfile = open("par%i" % (i),"r")
            array = parfile.readlines()
            if len(array) > 1:
                print "par %i should not have multiple lines of best-fit result" % (i)
            for line in array:
                line = line.split()
                (value, lower, upper)=(float(line[0]),float(line[1]),float(line[2]))
                self.parameters[i-1].initvalue=value
                if (lower,upper) == (0.,0.):
                    self.parameters[i-1].bestvalue=(value, '(fixed)')
                else:
                    self.parameters[i-1].bestvalue=(value, lower-value, upper-value)
        for i in range(len(self.parameters)):
            j = i % self.model.parlength
            if self.model.parameters[j].__dict__.has_key('bestvalue'): 
                if not isinstance(self.model.parameters[j].bestvalue,list):
                    self.model.parameters[j].bestvalue=[self.model.parameters[j].bestvalue]
                    self.model.parameters[j].bestvalue.append(self.parameters[i].bestvalue)
                else:
                    self.model.parameters[j].bestvalue.append(self.parameters[i].bestvalue)
            else:
                self.model.parameters[j].bestvalue=self.parameters[i].bestvalue
        #self.model.updateparents()
        statfile = open("chisq", "r")
        array=statfile.readlines()
        for line in array:
            line=line.split()
            if len(line) == 3:
                (chisq, dof, Pnull) = (float(line[0]),float(line[1]),float(line[2]))
            else:
                (chisq, dof) = (float(line[0]),float(line[1]))
                try:
                    from scipy.stats import chisqprob
                    Pnull = chisqprob(chisq, dof)
                except:
                    import commands
                    Pnull = commands.getoutput('%s/chisqpo %d %g' % (XSPEC_MODULE_PATH, dof, chisq))
            self.chisq=(chisq/dof, dof, Pnull)
        self.rate=[]
        ratefile = open("rate", "r")
        array=ratefile.readlines()
        for line in array:
            line=line.split()
            (rate, rateerr, modelrate) = (float(line[0]),float(line[1]),float(line[2]))
            self.rate.append((rate, rateerr, modelrate))
        self.exposure=[]
        expofile = open("exposure", "r")
        array=expofile.readlines()
        for line in array:
            line=line.split()
            self.exposure.append(float(array[0]))
        os.chdir(self.basepath)




    def getflux(self):
        """Retreive the flux."""
        os.chdir(self.tempdir)
        fluxfile = open("flux.tmp","r")
        array = fluxfile.readlines()
        self.flux={}
        self.pflux={}
        for line in array:
            grpidx,Erange,line= line.split(':')
            line=line.split()
            (flx, flxlow, flxup, crt, crtlow, crtup) = (float(line[0]),float(line[1]),float(line[2]),float(line[3]),float(line[4]),float(line[5]))
            if flxlow == 0 and flxup ==0:
                flxvalue=flx
                crtvalue=crt
            else:
                flxvalue=(flx,flxlow-flx,flxup-flx)
                crtvalue=(crt,crtlow-crt,crtup-crt)
            if not self.flux.has_key(grpidx):self.flux[grpidx]={}
            self.flux[grpidx][Erange] = flxvalue
            if not self.pflux.has_key(grpidx):self.pflux[grpidx]={}
            self.pflux[grpidx][Erange] = crtvalue
            #self.flux.append((flx,flxlow-flx,flxup-flx))
            #self.pflux.append((crt,crtlow-crt,crtup-crt))
        os.chdir(self.basepath)
        


    def save(self,savename=None):
        """Save the result of the fitting, if file name is provided then save to the file name, otherwise save to a temperate file named using the uniquename method."""
        if savename==None:
            savename='.'+uniquename()+'.sav'
        else:
            savename=savename+'.sav'
        savelist={'this':self,'data':self.data,'model':self.model}
        for parents in self.model.parents:
            key=str(parents[0])
            if key in savelist:
                if isinstance(savelist[key],list):
                    savelist[key].append(parents[0])
                else:
                    savelist[key]=[savelist[key]]
                    savelist[key].append(parents[0])
            else:
                savelist[str(parents[0])]=parents[0]
        file = open(savename, 'wb')
        cPickle.dump(savelist, file, -1)
        file.close()



def loadfit(filename):
    """A method to load a saved fit instance."""
    file = open(filename,'rb')
    obj=cPickle.load(file)
    file.close()
    return obj

@resetdefaults
def project(projectname=''):
    if projectname=='':
        projectname=uniquename()
    else:pass
    os.mkdir(projectname)
    os.chdir(projectname)


class model(fit):pass
