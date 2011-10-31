from planners.planner import *
from myutils.mwmatching import maxWeightMatching
from region.mygraph import WeightedMygraph

class MultiAgentPlanner(Planner):
  """ a MultiAgentPlanner is just like a planner, but locations are replaced 
  by arrays of locations, plans by arrays of plans, next by array of next
  etc """

  def next(self,locations,request_ids=None):
    """ gives the next element of the plan
    @param locations: [location] list of agent locations
    @param request_ids: [id] list of current request ids, give the first after
    NOTE:currently unused
    @returns [(location,id)] with len(ret) = len(locations)
    """
    if self.replan:
      self.plan = self._plan(locations)
    print self.plan
    try:
      return [plan and plan[0] or (None,None) for plan in self.getPlan()]
    except:
      pdb.set_trace()

  def remove_request(self,request_id):
    """ removes the specified request
    if the specified request is part of the current plan but not the head,
    we replan"""
    self.replan = True
    try:
      self.requests = [(l,id) for l,id in self.requests if id <> request_id]
      for plan in self.getPlan():
        if not plan:
          # should be at least (None,None)
          pdb.set_trace()
        # in the old code this was not necessarily necessary
        # for now this is the easy way to do it
        if request_id == plan[0][1]:
          plan.pop(0)
          if not plan:
            plan.append((None,None))
            self.replan = True
        else:
          newplan = []
          for l,id in plan:
            if id == request_id:
              self.replan = True
            else:
              newplan.append((l,id))
          plan = newplan
          # currently this does nothing.  perhaps we should be saving plan?
    except Exception, err:
      pdb.set_trace()


  def _plan(self,locations):
    """ does the actual planning
    @param locations: [location]
    @returns [(location,id)] or [(None,None)]
    updates self.plan
    """

class SimpleMultiAgentPlanner(MultiAgentPlanner):
  """ This class makes a multi-agent planner out of a single agent planner
  by running them sequentially, and iteratively removing requests once
  planners ask for them """

  def __init__(self,region,plannertype):
    """ a planner factory is a void method that creates a new planner """
    MultiAgentPlanner.__init__(self,region)
    self.plannertype = plannertype

  def _plan(self,locations):
    factories = [self.plannertype(self.region) for loc in locations]
    self.plan = [None]*len(locations)
    requests = [(l,id) for l,id in self.requests]
    for i in range(len(factories)):
      factory = factories[i]
      for (l,id) in requests:
        factory.add_request(l,id)
      self.plan[i] = factory._plan(locations[i])
      requests = [r for r in requests if r not in self.plan[i]]
    return self.plan

class AuctioningMultiAgentPlanner(MultiAgentPlanner):
  """ This class makes a multi-agent planner out of a single agent IBidding 
  planner by iteratively running it in a winner-take-all fashion."""

  def __init__(self,region,plannertype):
    """ a planner factor is a void method that creates a new 
    IBidding planner """
    MultiAgentPlanner.__init__(self,region)
    self.plannertype = plannertype

  def _plan(self,locations):
    self.plan = [None]*len(locations)
    requests = [(l,id) for l,id in self.requests]
    while None in self.plan and requests:
      bestplan = None
      bestplannerindex = 0
      bestbid = -1e6
      for i in range(len(locations)):
        if self.plan[i] is None:
          planneri = self.plannertype(self.region)
          for (l,id) in requests:
            planneri.add_request(l,id)
          plan = planneri._plan(locations[i])
          bid = planneri.getBid()
          if bid > bestbid:
            bestplan,bestplannerindex,bestbid = plan,i,bid
      self.plan[bestplannerindex] = bestplan
      requests = [r for r in requests if r not in bestplan]
    self.plan = [p or [(None,None)] for p in self.plan]
    ids = [[id for l,id in plan if id is not None] for plan in self.plan]
    for i in range(len(ids)-1):
      for j in range(i+1,len(ids)):
        if set.intersection(set(ids[i]),set(ids[j])):
          pdb.set_trace()
      
    return self.plan

class MultiAgentGraphPlanner(MultiAgentPlanner,GraphPlanner):
  """ Adapts Graph Planner to be a MultiAgentPlanner """

  def _plan(self,locations):
    label = self.startnodelabel
    for node in self.requestgraph.nodes():
      if node.startswith(label):
        self.requestgraph.remove_node(node)
    startnodes = []
    for i in range(len(locations)):
      startnodes.append(self.requestgraph.add_node(locations[i],label+str(i)))
    for node in startnodes:
      self.requestgraph.add_node_attribute(node,('reward',0))
    multitour = self.driver.solve(self.requestgraph,
                                  startnodelabels=startnodes)
    self.plan = []
    #print multitour
    for subplan in multitour:
      #pdb.set_trace()
      if not subplan or subplan[0] is None:
        self.plan.append([(None,None)])
      else:
        sp = []
        for n in subplan:
          if n and not n.startswith(label):
            sp.append((self.requestgraph.location(n),n))
        self.plan.append(sp or [(None,None)])
    return self.plan

  #tricky multiple inheritance issue
  def add_request(self,location,request_id,priority=1.0):
    MultiAgentPlanner.add_request(self,location,request_id)
    nodeid = self.requestgraph.add_node(location,request_id)
    self.requestgraph.add_node_attribute(nodeid,('reward',priority))
    #print self.requestgraph.nodes()

  def remove_request(self,request_id):
    MultiAgentPlanner.remove_request(self,request_id)
    self.requestgraph.remove_node(request_id)
    #print self.requestgraph.nodes()

class MultiAgentGraphSolver(object):
  def __init__(self,region):
    self.region = region

  def solve(self,graph,startnodelabels=None):
    """ the actual planning code 
    @param graph: a graph of requests to visit
    @type graph: mygraph, probably SpacialMygraph

    @param startnodelabels: [id] list of starting nodes

    @returns [[node]], sorted by startnodelabels"""

class SimpleNNSolver(MultiAgentGraphSolver):
  """ This class does the most obvious implementation of Multi-Agent NN
    by iteratively removing the NN from the graph 
    This class is included as an example.  An easier way to create the 
    same planner would be to use SimpleMultiAgentPlanner(NNPlanner) """

  def solve(self,graph,startnodelabels):
    """ This class does the most obvious implementation of Multi-Agent NN
    by iteratively removing the NN from the graph
    @param graph: a completely connected, spacialmygraph
    @param startnodelabels: [id]
    @returns [[node]] or [[None]] with len(ret) = len(startnodelabels)
    """
    graphcopy=graph.copy()
    startnodelocs = [graph.location(node) for node in startnodelabels]
    for label in startnodelabels:
      graphcopy.remove_node(label)
    ret = []
    for label in startnodelabels:
      mindist = 1e6
      minnode = None
      startloc = graph.location(label)
      for node in graphcopy.nodes():
        dist = self.region.distance(startloc,graphcopy.location(node))
        if dist<mindist:
          minnode = node
          mindist = dist
      ret.append([minnode])
      if minnode is not None:
        graphcopy.remove_node(minnode)
    for i in range(len(ret)):
      for j in range(i):
        if ret[i][0] is not None and ret[j][0] is not None and set.intersection(set(ret[i]),set(ret[j])):
          pdb.set_trace()
    return ret

class SimpleNNPlanner(MultiAgentGraphPlanner,CompletelyConnectedPlanner):
  """ this class is included as an example MultiAgentGraphPlanner
  it is exactly equivalent to SimpleMultiAgentPlanner(NNPlanner) """
  def __init__(self,region):
    CompletelyConnectedPlanner.__init__(self,SimpleNNSolver(region),region)                                     
      
class MatchingNNSolver(MultiAgentGraphSolver):
  """ This class does a reasonable implementation of Multi-Agent NN
    by solving the min weight bipartite matching"""
  def solve(self,graph,startnodelabels):
    """ This class does a better implementation of Multi-Agent NN
    by solving the min weight bipartite matching
    @param graph: a completely connected, spacialmygraph
    @param startnodelabels: [id]
    @returns [[node]] or [[None]] with len(ret) = len(startnodelabels)
    """
    pygraph = graph.toPygraph()
    bigraph = WeightedMygraph()
    bigraph.add_nodes(graph.nodes())
    othernodes = [n for n in graph.nodes() if n not in startnodelabels]
    for sn in startnodelabels:
      for on in othernodes:
        edge = bigraph.add_edge(sn,on)
        bigraph.set_edge_weight(edge,pygraph.edge_weight(sn,on))
    matching = dict(bigraph.getMinMatching())
    return [[matching.get(sn,None)] for sn in startnodelabels]

class MatchingNNPlanner(MultiAgentGraphPlanner,CompletelyConnectedPlanner):
  def __init__(self,region):
    CompletelyConnectedPlanner.__init__(self,MatchingNNSolver(region),region)  
        
  
