#from region.region import *

#from region import mygraph
import region.mygraph as mygraph

import pdb

class Planner(object):
  """ a planner is someone who, given a region, can take a list of requests
  (id, location) and create a sequence in which to service them

  the attribute "plan" contains this sequence, but it is allowed to go stale.
  Calling next will force a replan if "plan" is out of date.

  Since we aren't allowing pre-emption and we don't have observations,
  the only time when we would consider replanning is when a request arrives"""
  request_ids = 0

  def __init__(self,region):
    self.region = region
    self.replan = True
    self.plan = [] #id location pairs
    self.requests = []

  def add_request(self,location,id=None):
    """ add the specified request
    @returns id, the id of the added request
    """
    if location is None:
      pdb.set_trace()
    if id is None:
      id = self.request_ids
    id = str(id)
    self.request_ids += 1
    self.requests.append((location,id))
    self.replan = True
    return id

  def getPlan(self):
    return self.plan

  def nrequests(self):
    """returns the number of outstanding requests"""
    return len(self.requests)

  def remove_request(self,request_id):
    """ removes the specified request
    if the specified request is part of the current plan but not the head,
    we replan"""
    self.requests = [(l,id) for l,id in self.requests if id <> request_id]
    plan = self.getPlan()
    if plan and request_id == plan[0][1]:
      self.planPop()
    else:
      newplan = []
      for l,id in plan:
        if id == request_id:
          self.replan = True
        else:
          newplan.append((l,id))
      self.setPlan(newplan)

  def next(self,location,request_id=None):
    """ return the next request to visit from the particular location.
    if replan is False we use self.plan without updating
    
    @returns (location, id) 
    the id -1 is a special id that indicates a loitering location
    """
    self.plan = self.getPlan()
    if self.replan:
      self.plan = self._plan(location)
    if not self.plan:
      return (None,None)
    #if self.plan[0][0] and location == self.plan[0][0]:
    #  pdb.set_trace()
    #  self.plan.pop()
    return self.plan and self.plan[0] or (None,None)

  def _plan(self,location):
    """ does the actual work, 
    @returns None (but sets self.plan to [(location,id)])"""

class NNPlanner(Planner):
  """ your basic nearest neighbor policy """
  def _plan(self,location):
    mindist = 10e6
    if len(self.requests) == 0:
      self.plan = []
    else:
      for l,id in self.requests:
        dist = self.region.distance(location,l)
        if dist < mindist:
          retl, retid = l,id
          mindist = dist
      self.plan = [(retl,retid)]
    return self.plan

class GraphPlanner(Planner):
  startnodelabel = 'start'

  def __init__(self,driver,graph,region):
    """
    @param driver: a graph solver
    @param graph: a graph
    @param region: the region
    """
    Planner.__init__(self,region)
    self.driver = driver
    self.requestgraph = graph#CompletelyConnected(self.region)

  def add_request(self,location,id=None):
    id = Planner.add_request(self,location,id)
    self.requestgraph.add_node(location,id)

  def remove_request(self,request_id):
    Planner.remove_request(self,request_id)
    self.requestgraph.remove_node(request_id)

  def _plan(self,location):
    label = self.startnodelabel
    if label in self.requestgraph.nodes():
      self.requestgraph.remove_node(label)
    self.requestgraph.add_node(location,label,isroot=True)
    if self.nrequests() > 50:
      print location
      print [str(self.requestgraph.location(req)) for req in self.requestgraph.nodes()]
      pdb.set_trace()

    tour = self.driver.solve(self.requestgraph,startnodelabel=label)
    self.plan = []
    for n2 in tour:
      if n2<>label:
        self.plan.append((self.requestgraph.location(n2),n2))
    return self.plan
    
class CompletelyConnectedPlanner(GraphPlanner):
  """ and Ampl Planner wraps an ampl driver to meet the Planner interface """
  def __init__(self,driver,region):
    """
    @param driver: a graph solver
    """
    GraphPlanner.__init__(self,driver,mygraph.CompletelyConnected(region), 
                          region)

class ISolver(object):
  def solve(self):
    """ this is the core of a planner.  Takes some data structure and
    gives back a plan """


class GraphSolver(ISolver):
  def solve(self, graph,startnodelabel=None):
    """ the actual planning code 
    @param graph: a graph of requests to visit
    @type graph: mygraph, probably SpacialMygraph

    @param startnodelabel: the label of the starting node

    @returns [node]"""

class IBiddingPlanner(Planner):
  def getBid(self):
    """ gets the bid value associated with self.plan
    larger is better
    e.g. -subsidy for stopping-problem based planners """

class IBiddingSolver(ISolver):
  def getBid(self):
    """ gets the bid value associated with self.plan
    larger is better
    e.g. -subsidy for stopping-problem based planners """


