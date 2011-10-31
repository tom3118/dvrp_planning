from planner import CompletelyConnectedPlanner
from ampl.pyampl import (TSPSolver, EdgeOrienteeringSolver, OrienteeringSolver,
                         LatencySolver)

class TSPPlanner(CompletelyConnectedPlanner):
  def __init__(self,region):
    CompletelyConnectedPlanner.__init__(self,TSPSolver(),region)

class EdgeOrienteeringPlanner(CompletelyConnectedPlanner):
  def __init__(self,region):
    CompletelyConnectedPlanner.__init__(self,EdgeOrienteeringSolver(),region)

class OrienteeringPlanner(CompletelyConnectedPlanner):
  def __init__(self,region):
    CompletelyConnectedPlanner.__init__(self,OrienteeringSolver(),region)

class LatencyPlanner(CompletelyConnectedPlanner):
  def __init__(self,region):
    CompletelyConnectedPlanner.__init__(self,LatencySolver(),region)
