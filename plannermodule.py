""" This code exposes a planner as a standalone process that can be
connected to via socket and used for planning 

"""
import config
from inputoutput import inputoutput as io
from lmcp import LMCPFactory
from dvrp import (ServicePlannerRequest,ServicePlannerConfiguration, 
                  RequestConfiguration)
#import lmcp_all
from inputoutput import lmcpio
import socket
import getopt,sys
import pdb
import region
import googleearth
from googleearth.googlesn import GoogleSN
#import desim
#from desim import infostate
import observations
from observations.beliefplanner import (TestPlanner,DensestAndMatchingPlanner,
                                        WrappedDensestAndMatchingPlanner)

from observations.planner import SNPlan
from observations.infostate import InfoState
from observations.cowpath import CowPathPlanner
import shelve
PORT=config.port

confnames = {'nagents':'TeamSize','sensor_radius':'SensorRadius',
             'speed':'AgentSpeed','arrival_rate':'ArrivalRate'}
regionname = 'Region'
notconfnames = [regionname] # these names are not added to config

class PlannerModule(object):
  """ The planner module runs a server socket that accepts a connection
  then reads the socket once for a message, writes a plan to the socket
  and then closes the connection.
  
  One message per connection"""
  def __init__(self,plannerfactory,infostate,region,host=None):
    self.infostate = infostate
    self.plannerfactory = plannerfactory
    self.region = region
    self.planner = self.plannerfactory(region)
    self.shelf = shelve.open(config.logfilename)
    self.sock = socket.socket()
    if not host:
      self.host = ('localhost',PORT)
    else:
      self.host = host
    self.sock.bind(self.host)
    self.sock.listen(5)

  def listen(self):
    """ the listen loop """
    socket, addy = self.sock.accept()
    message = socket.recv(1e6)
    obj = LMCPFactory.internalFactory.getObject(message)
    retmessage = self.handle(obj)
    #pdb.set_trace()
    socket.send(retmessage)
    socket.close()

  def logStatus(self,event):
    """ log the event and our internal state """
    logentry = dict([('0',self._logStatus(event.time))])
    logentry['event'] = event
    self.shelf[str(event.id)] = logentry

  def _logStatus(self,time):
    """ what to actually put in the log """
    return {'handlerclass':'MultiAgent',
            'locations':self.infostate.getAgentlocs(time),
            'plan':self.infostate.getPlan(),
            'belief':self.infostate.getBelief(),
            'known':[r.id for r in self.infostate.requests],
            'updatetime':self.infostate.updatetime}

  def handle(self,obj):
    """ This function takes a LMCP.object and does the right thing with it
    obj can contain ServicePlannerConfiguration or ServicePlannerRequest
    if it is a Configuration we modify config and load a new region.
    This type of message will reset the infostate, so one must resend any
    outstanding requests.
    This type of message is typically only used once at the beginning.

    if it is a plan request, we update the infostate and return a plan.
    This is the normal usage.
    """
    if isinstance(obj,ServicePlannerConfiguration.ServicePlannerConfiguration):
      #config.enableModification()
      nameprefix = '_%s__'%obj.__class__.__name__
      for k,v in confnames.items():
        attrname = nameprefix+v
        if hasattr(obj,attrname):
          setattr(config,k,getattr(obj,attrname))
      
      for k,v in obj.__dict__.items():
        if (k.startswith('__') and not k.endswith('_') and 
            k not in notconfnames):
          print k
        setattr(config,k,v)
      #config.disableModification()
      try:
        region = lmcpio.createRegion(obj.get_Region())
      except:
        region  = None
      if region is None:
        print ("expected a region in Configuration message\n"
               "falling back to plannermodule.region")
        #pdb.set_trace()
      else:
        self.region = region
        self.planner = self.plannerfactory(region)
      self.infostate = InfoState(
        self.region, sensor_radius=config.sensor_radius, nagents=config.nagents,
        locations=None, speed=config.speed)
      networkregion = lmcpio.createNetwork(self.region)
      return LMCPFactory.packMessage(networkregion,True)
    elif isinstance(obj,ServicePlannerRequest.ServicePlannerRequest):
      if True:#try:
        lmcplocs = obj.get_AgentLocations()
        lmcpevent = obj.get_NewEvent()
        dvrpevent = lmcpio.lmcpEvent2dvrpEvent(lmcpevent)
        dvrplocs = [lmcpio.lmcpLoc2dvrpLoc(l) for l in lmcplocs]
      else:#except Exception, err:
        print err
        pdb.set_trace()
      event = dvrpevent
      self.infostate.update(event,dvrplocs)
      self.logStatus(event)
      requests,belief = self.infostate.getRequests(),self.infostate.getBelief()
      plan = self.planner.plan(belief,requests,dvrplocs)
      #pdb.set_trace()
      self.infostate.setPlan(plan)
      #pdb.set_trace()
      message = lmcpio.plansToMessage(plan)#,self.infostate.region)
      return message
    elif(isinstance(obj,RequestConfiguration.RequestConfiguration)):
      try:
        networkregion = lmcpio.createNetwork(self.region)
        return LMCPFactory.packMessage(networkregion,True)
      except Exception, err:
        print err
        pdb.set_trace()
    else:
      print "unknown message-object"
      pdb.set_trace()
    return lmcpio.plansToMessage([SNPlan([],region=self.region) 
                                  for i in range(config.nagents)])



  def run(self):
    #maxiters = config.maxiters
    #iter = 0
    while(True):#iter<=10):
      self.listen()
      #iter += 1

def loadAndRun(regionfile):
  region = GoogleSN(io.CNFromXML(regionfile))
  infostate = InfoState(
    region, sensor_radius=config.sensor_radius, nagents=config.nagents,
    locations=None, speed=config.speed)
  pm = PlannerModule(TestPlanner,infostate,region)
  #pm = PlannerModule(CowPathPlanner(),infostate)
  #pm = PlannerModule(WrappedDensestAndMatchingPlanner,infostate,region)
  #pm = PlannerModule(DensestAndMatchingPlanner(region),infostate)
  pm.run()

def main():
  """ loads regionfile, parameterfile, and then starts a PlannerModule """
  print "unexpected usage"
  pdb.set_trace()
  opts,args = getopt.getopt(sys.argv[1:],"hrp")
  region = GoogleSN(io.CNFromXML('googleearth/data/vandenburg2.xml'))
  #params = io.dictFromXML('')
  params = {'sensor_radius':config.sensor_radius,
            'nagents':config.nagents,
            'locations':None,
            'speed':config.speed}
  infostate = InfoState(
    region, sensor_radius=params['sensor_radius'], nagents=params['nagents'],
    locations=params['locations'], speed=params['speed'])
  #pm = PlannerModule(DensestAndMatchingPlanner(region),infostate)
  pm = PlannerModule(TestPlanner(region),infostate)
  pm.run()
    
if __name__ == "__main__":
  main()
