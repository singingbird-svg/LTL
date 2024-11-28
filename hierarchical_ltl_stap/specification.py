#建立分层LTL specifications及图
import networkx as nx 
from .utils import vis_graph

task1 = "<> (d5 && default && X ((carrybin U dispose) && <> default)) && [](carrybin -> !publicc)  && \
            <> (d5 && emptybin && X (d5 && default))"
task2 = "<> (p && carry U (d10 && X !carry)) && \
            <> (p && carry U (d7 && X !carry)) && \
            <> (p && carry U (d5 && X !carry)) && [] (carry -> !publicc)"
task3 = "<> (d5 && carry U (d3 && X !carry)) && [] (carry -> !publicc) && \
            <> (d11 && guide U (m6 && X !guide)) && \
            <> (m1 && photo) && \
            <> (m4 && photo) && \
            <> (m6 && photo) && \
            [] (!(m1 || m2 || m3 || m4 || m5 || m6) -> !camera)"
            
class Specification():
    def __init__(self) -> None:
        self.hierarchy = []
        
    def get_task_specification(self, task, case):
        if task == "man": #监控任务
            return self.get_manipulation_specification(case)
        elif task == "nav": #导航任务
            return self.get_navigation_specification(case)
        else:
            exit            
    
    #获得导航任务的speciofication
    def get_navigation_specification(self, case):
        self.hierarchy = []
    # hierarchy version
        if case == 18:
            # hierarchical version of combined task 1 and 2
            level_one = dict()
            level_one["p0"] = '<>p100 && <> p200'  #task1 and task2
            self.hierarchy.append(level_one)
            
            level_two = dict()
            level_two["p100"] = '<> p101 && <> p102'
            level_two["p200"] = '<> p201 && <> p202 && <> p203'
            self.hierarchy.append(level_two)            

            level_three = dict()
            level_three["p101"] = "<> (d5 && default && X ((carrybin U dispose) && <> default)) && [](carrybin -> !publicc)"
            level_three["p102"] = "<> (d5 && emptybin && X (d5 && default))"
            level_three["p201"] = "<> (p && carry U (d10 && X !carry)) && [] (carry -> !publicc)"
            level_three["p202"] = "<> (p && carry U (d7 && X !carry)) && [] (carry -> !publicc)"
            level_three["p203"] = "<> (p && carry U (d5 && X !carry)) && [] (carry -> !publicc)"
            self.hierarchy.append(level_three)  
        elif case == 22:
            #flat version       
            level_one["p0"] = "<> p100"
            self.hierarchy.append(level_one)
            
            level_two = dict()
            # level_two['p100'] = task1 + ' && ' + task2
            level_two['p100'] = "<> (d5 && default && X ((carrybin U dispose) && <> default)) && [](carrybin -> !publicc)  && \
            <> (d5 && emptybin && X (d5 && default)) && \
            <> (p && carry U (d10 && X !carry)) && \
            <> (p && carry U (d7 && X !carry)) && \
            <> (p && carry U (d5 && X !carry)) && [] (carry -> !publicc)"
            self.hierarchy.append(level_two)   
        return self.hierarchy       
    
    def get_manipulation_specification(self, case):
        """_summary_

        Args:
            case (_type_): _description_

        Returns:
            _type_: _description_
        """
        self.hierarchy = []
        return self.hierarchy  
    
    '''
    self.hierarchy = [
    {"p0": "<> p100 && <> p200"},  # level 0
    {"p100": "<> p101 && <> p102", "p200": "<> p201 && <> p202 && <> p203"},  # level 1
    {"p101": "<> (d5 && default && X ((carrybin U dispose) && <> default))", ...}  # level 2
    ]'''
    #建立hierarchy_graph
    def build_hierarchy_graph(self, vis = False):
        hierarchy_graph = nx.DiGraph(name='hierarchy')
        #对于分层LTL中的每一层
        for level in self.hierarchy:
            #对于每一层的
            for phi in level.keys(): #p100, p200等
                hierarchy_graph.add_node(phi, label=phi) #为每一层添加节点
        #对于每一层
        for idx in range(1, len(self.hierarchy)):
            cur_level = self.hierarchy[idx]
            high_level = self.hierarchy[idx - 1]
            for high_phi, spec in high_level.items(): #遍历高层次的phi和它的specification
                for cur_phi in cur_level.keys(): #遍历低层次的phi
                    if cur_phi in spec:#如果它在上层任务的specification,说明 high_phi 和 cur_phi 之间存在依赖关系，添加一条从 high_phi 到 cur_phi 的边。
                        hierarchy_graph.add_edge(high_phi, cur_phi)
        if vis:
            vis_graph(hierarchy_graph, 'data/spec_hierarchy', latex=True)
        return hierarchy_graph