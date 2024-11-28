from hierarchical_ltl_stap.utils import plot_workspace, create_parser, prGreen, prRed,vis_graph, depth_to_leaf
from hierarchical_ltl_stap.specification import Specification
import time
import matplotlib.pyplot as plt
import networkx as nx 
def main(args = None):
    parser = create_parser() #创建参数器
    args = parser.parse_known_args()[0] #获得命令行参数
    #获得工作空间头文件
    if args.domain == "supermarket":
        from hierarchical_ltl_stap.workspace_supermarket import Workspace
    start_time = time.time() # Record the start time
    # =========================
    # 步骤一：获得任务的分层specification及各个叶子节点到root的路径深度
    # =========================
    specs = Specification()  #初始化specification
    specs.get_task_specification(task=args.task, case=args.case) #获得对应的任务
    hierarchy_graph = specs.build_hierarchy_graph(args.vis) #获得分层LTL的图
    #获得叶子节点和非叶子节点
    leaf_specs = [ node for node in hierarchy_graph.nodes() if hierarchy_graph.out_degree(node) == 0]  #如果没有出度，则为叶子节点
    non_leaf_specs= [ node for node in hierarchy_graph.nodes() if node not in leaf_specs]
    depth_specs = {}
    for spec in hierarchy_graph.nodes():
        depth = depth_to_leaf(hierarchy_graph, spec) #获得节点的深度
        #按照深度存储spec
        if depth in depth_specs.keys():
            depth_specs[depth].append(spec)
        else:
            depth_specs[depth] = [spec]     
    depth_specs = {k: depth_specs[k] for k in sorted(depth_specs)} #按深度排序
    path_to_root = dict()   
    #获得每个叶子节点到root的路径 
    for spec in leaf_specs:
        path_to_root[spec] = nx.shortest_path(hierarchy_graph, source="p0", target=spec)[::-1]   
    #打印路径
    if args.print_step:    
        prRed(f"Specs: {specs.hierarchy}")
        prRed(f"Depth: {depth_specs}")
        prRed(f"Path to root: {path_to_root}")
        spec_time = time.time() # Record the end time
        prGreen("Take {:.2f} secs to generate {} specs".format(spec_time - start_time, hierarchy_graph.number_of_nodes()))    

    #=================
    #步骤二：工作空间
    #==================
    #根据命令行的输入的参数，建立工作空间
    if args.domain == "supermarket" or args.domain == "bosch": #supermarket以及bosch，根据参数
        workspace = Workspace(args.domain_file, args.num_robots, args.run)
    elif args.domain == "ai2thor":
        leaf_specs_ltl = [specs.hierarchy[-1][leaf_spec] for leaf_spec in leaf_specs] #取 hierarchy 列表的最后一个元素，即最后一层的规范。这通常是最底层的叶子节点规范
        workspace = Workspace(leaf_specs_ltl, args.num_robots)
    if args.vis:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        plot_workspace(workspace, ax)
        vis_graph(workspace.graph_workspace, f'data/workspace', latex=False, buchi_graph=False)
    workspace_time = time.time() # Record the end time
    if args.print_step:    
        prGreen("Take {:.2f} secs to generate workspace".format(workspace_time - spec_time))    
        prRed(f"Workspace has {workspace.graph_workspace.number_of_nodes()} nodes and {workspace.graph_workspace.number_of_edges()} edges")
    #==========================
    #步骤三：建立布奇自动机、分解集、偏序集
    #==========================               

if __name__ == "__main__":
    main()