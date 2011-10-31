import pdb
from region.tree import Tree
from region.mygraph import mygraph, CompletelyConnected

from myutils.mwmatching import maxWeightMatching

from planner import (CompletelyConnectedPlanner, GraphSolver, IBiddingSolver,
                     IBiddingPlanner)

from region.densestsubtree import densestSubtree, treeToPlan, forestToPlan

from multiagent.multiagent import MultiAgentGraphSolver, MultiAgentGraphPlanner

from heapq import heappush, heappop

class TreePlanner(CompletelyConnectedPlanner,IBiddingPlanner):
  """ This class plans by computing the densest subtree of the MST
  of the request graph.  Then it computes a tour using the 
  minimum perfect matching of that."""

  def __init__(self,region):
    CompletelyConnectedPlanner.__init__(self,TreeSolver(region),region)

  def getBid(self):
    return self.driver.getBid()

#def ForrestPlanner(CompletelyConnectedPlanner):
#  """ 

class TreeSolver(GraphSolver,IBiddingSolver):

  def __init__(self,region):
    self.region = region
    self.bid = None
    
  def getBid(self):
    if self.bid is None:
      pdb.set_trace()
    ret = self.bid
    self.bid = None
    return ret

  def treeToPlan(tree):
    """ given a tree, we compute a shortest open tour
    @param tree: Tree, SpacialGraph,RewardGraph"""
    odd_nodes = [n for n in tree.nodes() if len(tree.neighbors(n))%2==1
                 and n<>startnodelabel]
    subgraph = tree.copy()
    mwgraph = CompletelyConnected(tree.region) 
    for node in odd_nodes:
      mwgraph.add_node(tree.location(node),id=node)
    matching = mwgraph.getMinMatching()
    marked = dict([(node,False) for node in odd_nodes])
    #add the matching to the subtree
    for n1,n2 in matching:
      if not marked[n1]:
        subtree.add_edge(n1,n2)
        marked[n1] = marked[n2] = True
      else:
        print "marked"
    #add an edge from the startnode to make the graph eulerian
    lastnode = None
    for n in subtree.nodes():
      if n<>startnodelabel and len(subtree.neighbors(n))%2==1:
        lastnode = n
        break
    if lastnode is not None:
      lastedge = subtree.add_edge(startnodelabel,lastnode)
    #compute euler tour
    tour = subtree.eulerTour(start=startnodelabel)
    if tour and lastnode is None:
      pdb.set_trace()
    #if the last node is first, reverse the tour
    if len(tour)>2 and tour[0][1]==lastnode:
      tour = tour[::-1]
    return tour
  
  def solve(self,graph,startnodelabel):
    #compute MST of graph
    tree = Tree(graph.toPygraph(),root=startnodelabel)
    for node in tree.nodes():
      if node<>startnodelabel:
        tree.add_node_attribute(node,('reward',1.0))
    #compute densest subtree of MST
    rettree,retdist,retreward = computeMinSubsidy(startnodelabel,tree)
    self.bid = retdist and retreward/retdist or 0
    #compute min matching of subtree
    subtree = mygraph()
    subtree.add_node(startnodelabel)
    for n in rettree:
      if n<>startnodelabel:
        subtree.add_node(n)
    for n in rettree:
      if n<>startnodelabel:
        try:
          subtree.add_edge(n,tree.parent(n))
        except:
          pdb.set_trace()
    odd_nodes = [n for n in subtree.nodes() if len(subtree.neighbors(n))%2==1
                 and n<>startnodelabel]
    mwgraph = CompletelyConnected(self.region) 
    for node in odd_nodes:
      mwgraph.add_node(graph.location(node),id=node)
    matching = mwgraph.getMinMatching()
    marked = dict([(node,False) for node in odd_nodes])
    #add the matching to the subtree
    for n1,n2 in matching:
      if not marked[n1]:
        subtree.add_edge(n1,n2)
        marked[n1] = marked[n2] = True
    #add an edge from the startnode to make the graph eulerian
    lastnode = None
    for n in subtree.nodes():
      if n<>startnodelabel and len(subtree.neighbors(n))%2==1:
        lastnode = n
        break
    if lastnode is not None:
      lastedge = subtree.add_edge(startnodelabel,lastnode)
    #compute euler tour
    tour = subtree.eulerTour(start=startnodelabel)
    if tour and lastnode is None:
      pdb.set_trace()
    #if the last node is first, reverse the tour
    if len(tour)>2 and tour[0][1]==lastnode:
      tour = tour[::-1]
    print rettree
    #return the node sequence
    #return  [n2 for n1,n2,e in tour[:-1]]
    return rettree
  
class DensestForestSolver(MultiAgentGraphSolver):
  def solve(self,graph,startnodelabels=None):
    sf = densestSubtree(graph,startnodelabels)
    plan =  forestToPlan(sf,self.region,startnodelabels)
    #if (sum([len([pi for pi in p if pi not in startnodelabels]) for p in plan]) < len([n for n in graph.nodes() if n not in startnodelabels]) and not 
    #    (plan[0] and plan[1])):
    #  print plan
    #  pdb.set_trace()
    return plan


class DensestForestPlanner(MultiAgentGraphPlanner,CompletelyConnectedPlanner):
  def __init__(self,region):
    CompletelyConnectedPlanner.__init__(self,DensestForestSolver(region),
                                        region)


