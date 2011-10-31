from multiagent.multiagent import MultiAgentPlanner

import pdb

class LoiteringPlanner(MultiAgentPlanner):
  """ planner that knows how to loiter in the absence of requests
  note: each agent's loiter location is computed independently
  """
  def __init__(self,planner,region):
    MultiAgentPlanner.__init__(self,region)
    self.planner = planner

  def getPlan(self):
    self.plan = self.planner.getPlan()
    return self.plan

  def add_request(self,*args,**kws):
    MultiAgentPlanner.add_request(self,*args,**kws)
    self.planner.add_request(*args,**kws)
  def remove_request(self,*args,**kws):
    MultiAgentPlanner.remove_request(self,*args,**kws)
    self.planner.remove_request(*args,**kws)

  def _plan(self,locations):
    self.planner._plan(locations)
    for i in range(len(locations)):
      if self.planner.plan[i][0] == (None,None):
        self.planner.plan[i][0] = (self.getLoiterLoc(locations[i]),-1)
    self.plan = self.planner.getPlan()
        
  def next(self,locations):
    ret = self.planner.next(locations)
    for i in range(len(locations)):
      if ret[i] == (None,None):
        ret[i] = (self.getLoiterLoc(locations[i]),-1)
    return ret
    
  def getLoiterLoc(self,location,all_locations=None):
    """ where should the agent at @param location move to loiter
    @returns location"""
      
class StayPutLoiteringPlanner(LoiteringPlanner):
  def getLoiterLoc(self,location,all_locations=None):
    return location

class SNMedieanLoiteringPlanner(LoiteringPlanner):
  """ this class loiters at the median* of the region 
  actually, it is the median _amongst nodes_.  It does not consider the
  reward (i.e. probability) along edges
  """

  def getLoiterLoc(self,location,all_locations=None):
    nodelabel = self.region.edge_endpoints(location.e)[int(location.d)]
    T = self.region.getEdgeCoverSearchTree(nodelabel)
    pdb.set_trace()
    return self.region.nodeToLocation(T.median())

class MultiAgentLoiteringPlanner(LoiteringPlanner):
  """ this type of planner allows the loitering locations to be computed
  simultaneously """
  def _plan(self,locations):
    self.planner._plan(locations)
    for i in range(len(locations)):
      loiterers = []
      if self.planner.plan[i][0] == (None,None):
        loiterers.append((i,locations[i]))
    if loiterers:
      loiterlocs = self.getLoiterLoc([loc for j,loc in loiterers],locations)
      for j in range(len(loiterers)):     
        self.planner.plan[loiterers[j][0]][0] = (loiterlocs[j],-1)
    self.plan = self.planner.getPlan()

  def next(self,locations):
    ret = self.planner.next(locations)
    loiterers = []
    for i in range(len(locations)):
      if ret[i] == (None,None):
        loiterers.append((i,locations[i]))
    if loiterers:
      loiterlocs = self.getLoiterLoc([loc for j,loc in loiterers],locations)
      for j in range(len(loiterers)):
        ret[loiterers[j][0]] = (loiterlocs[j],-1)
    #but if we're there already, don't do anything
    #TOL = 1e-6
    #for i in range(len(locations)):
    #  if ret[i][1] == -1 and self.region.distance(locations[i],ret[i])<TOL:
    #    ret[i] = (None,None)
    return ret

class MAStayPutLoiteringPlanner(MultiAgentLoiteringPlanner):
  def getLoiterLoc(self,locationsall_locations=None):
    return locations

class MASNMedeanLoiteringPlanner(MultiAgentLoiteringPlanner):
  """ this class loiters at the multimedian* of the region 
  actually, it is the median _amongst nodes_.  It does not consider the
  reward (i.e. probability) along edges
  """
  def getLoiterLoc(self,locations,all_locations=None):
    nodelabels = [self.region.edge_endpoints(location.e)[int(location.d)]
                  for location in locations]
    #try:
    F = self.region.getEdgeCoverSearchForest(nodelabels)
    ret = [self.region.nodeToLocation(m) for m in F.multimedian(nodelabels)]
    return ret
      

    #except Exception err:
  #pdb.set_trace()

