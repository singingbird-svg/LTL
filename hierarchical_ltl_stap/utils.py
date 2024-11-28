import argparse
import networkx as nx
from matplotlib.patches import Polygon
import numpy as np 
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import subprocess
#建立参数器
def create_parser():
    parser = argparse.ArgumentParser(description='LTL_STAP')
    parser.add_argument('--task', default="man", type=str)
    parser.add_argument('--case', default=0, type=int)
    parser.add_argument('--vis', action='store_true', help='Enable visualization')
    parser.add_argument('--print_search', action='store_true', help='Enable print search to terminal')
    parser.add_argument('--print_path', action='store_true', help='Enable print path to terminal')
    parser.add_argument('--print_task', action='store_true', help='Enable print task to terminal')
    parser.add_argument('--print_step', action='store_true', help='Enable print step-wise info to terminal')
    parser.add_argument('--log', action='store_true', help='Enable save log')
    parser.add_argument('--dot', action='store_true', help='Enable dot graph')
    parser.add_argument('--simul', action='store_true', help='Enable simultaneous execution')
    parser.add_argument('--event', action='store_true', help='Enable event based execution')
    parser.add_argument('--domain_file', default="./src/domain_default.json")
    parser.add_argument('--heuristic_weight', default=0, type=int)
    parser.add_argument('--num_robots', default=6, type=int)
    parser.add_argument('--domain', default="supermarket", type=str)
    parser.add_argument('--heuristics',action='store_true', help='Enable heuristics when searching')
    parser.add_argument('--heuristics_order',action='store_true', help='Enable heuristics of temporal order when searching')
    parser.add_argument('--heuristics_switch',action='store_true', help='Enable heuristics of essential switch when searching')
    parser.add_argument('--heuristics_automaton',action='store_true', help='Enable heuristics of automaton when searching')
    parser.add_argument('--cost', default='min', type=str, help='types of cost representation')
    parser.add_argument('--run', default=-1, type=int, help='test instance for batch test')
    return parser

#可视化
def vis_graph(graph, title, latex = False, buchi_graph=False):
    graph_copy = graph.copy() #以便修改时不影响原图
    if buchi_graph:
        for node in graph_copy.nodes(): #将节点的 label 属性修改为节点的 name 属性和原有的 label 合并，便于可视化
            graph_copy.nodes[node]['label'] =  graph_copy.nodes[node]['name'] + '  ' + str(graph_copy.nodes[node]['label'])
    nx.nx_agraph.write_dot(graph_copy, title+'.dot')    #将图写入dot文件    
    #如果 latex 为 False，则执行一个 Shell 命令，将 .dot 文件转换为 PNG 图像
    if not latex:
        # Run a Linux command
        command = "dot -Tpng {0}.dot >{0}.png".format(title)
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
    else: #如果 latex 为 True，图将被转换为 LaTeX 格式，之后编译为 PDF
        command = "dot2tex --preproc --texmode math {0}.dot  | dot2tex > {0}.tex && pdflatex {0}.tex".format(title)
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

#找从root点到leaf的路径的深度
def depth_to_leaf(G, start_node):
    #递归
    def dfs(node, visited): #深度优先搜索
        visited.add(node)
        
        if G.out_degree(node) == 0: #如果node就是叶子节点
            return 0
        
        max_depth = 0
        
        for neighbor in G.successors(node): #对于node所有的前继节点
            if neighbor not in visited: #如果neighbor还没被访问
                depth = dfs(neighbor, visited)
                max_depth = max(max_depth, depth + 1) #确保逐层向上
        return max_depth        
                    
    return  dfs(start_node, set())  #set()  创建了一个空集合, 被用来初始化 visited 变量

#输出

def prRed(skk): print("\033[91m {}\033[00m" .format(skk))
 
 
def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))
 
 
def prYellow(skk): print("\033[93m {}\033[00m" .format(skk))
 
 
def prLightPurple(skk): print("\033[94m {}\033[00m" .format(skk))
 
 
def prPurple(skk): print("\033[95m {}\033[00m" .format(skk))
 
 
def prCyan(skk): print("\033[96m {}\033[00m" .format(skk))
 
 
def prLightGray(skk): print("\033[97m {}\033[00m" .format(skk))
 
 
def prBlack(skk): print("\033[98m {}\033[00m" .format(skk))

#绘图
def plot_workspace(workspace, ax):
    if workspace.name() == "supermarket":
        plot_supermarket(workspace, ax)
    elif workspace.name() == "bosch":
        plot_bosch(workspace, ax)
        
def plot_supermarket(workspace, ax):
    plt.rc('text', usetex=True)
    ax.set_xlim((0, workspace.width))
    ax.set_ylim((0, workspace.height))
    plt.xticks(np.arange(0, workspace.width + 1, 5))
    plt.yticks(np.arange(0, workspace.height + 1, 5))
    plot_supermarket_helper(ax, workspace.regions, 'region')
    plot_supermarket_helper(ax, workspace.obstacles, 'obstacle')
    # plt.grid(visible=True, which='major', color='gray', linestyle='--')
    plt.savefig('./data/supermarket.png', format='png', dpi=300)

def plot_bosch(workspace, ax):
    plt.rc('text', usetex=True)
    ax.set_xlim((1, workspace.width))
    ax.set_ylim((1, workspace.height))
    plt.xticks(np.arange(1, workspace.width + 1, 5))
    plt.yticks(np.arange(1, workspace.height + 1, 5))
    plot_bosch_helper(ax, workspace.regions, 'region')
    plot_bosch_helper(ax, workspace.obstacles, 'obstacle')
    # plt.axis('off')
    # plt.tick_params(axis='both', which='both', bottom=False, top=False, left=False, right=False)

    # plt.grid(visible=True, which='major', color='gray', linestyle='--')
    plt.savefig('./data/bosch_building.png', format='png', dpi=300)
    
def plot_supermarket_helper(ax, obj, obj_label):
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    plt.gca().set_aspect('equal', adjustable='box')
    # p0 dock
    # p1 grocery p2 health p3 outdors p4 pet p5 furniture p6 electronics 
    # p7 packing area
    region = {'p0': 'dock',
            'p1': 'grocery',
            'p2': 'health',
            'p3': 'outdoor',
            'p4': 'pet supplies',
            'p5': 'furniture',
            'p6': 'electronics',
            'p7': 'packing area'}
    for key in obj:
        if 'r' in key:
            continue
        # color = 'gray' if obj_label != 'region' else 'white'
        color = 'gray' if obj_label != 'region' or (key == 'p0' or key == 'p7') else 'green'
        alpha = 0.6 if obj_label != 'region' or (key == 'p0' or key == 'p7') else 0.1
        for grid in obj[key]:
            x_ = grid[0]
            y_ = grid[1]
            x = []
            y = []
            patches = []
            for point in [(x_, y_), (x_ + 1, y_), (x_ + 1, y_ + 1), (x_, y_ + 1)]:
                x.append(point[0])
                y.append(point[1])
            polygon = Polygon(np.column_stack((x, y)), closed=True)
            patches.append(polygon)
            p = PatchCollection(patches, facecolors=color, edgecolors=color, linewidths=0.2, alpha=alpha)
            ax.add_collection(p)
        # ax.text(np.mean(x) - 0.2, np.mean(y) - 0.2, r'${}_{{{}}}$'.format(key[0], key[1:]), fontsize=12)
        if key == 'p0':
            ax.text(np.mean(x) + 1, np.mean(y) - 5, r'{}'.format(region[key]), fontsize=6)
        elif key == 'p7':
            ax.text(np.mean(x) - 3.5, np.mean(y) + 1, r'{}'.format(region[key]), fontsize=6)
        elif 'o' in key:
            ax.text(np.mean(x) - 2, np.mean(y) + 1, r'{}'.format(region['p' + key[1:]]), fontsize=6)
            
def plot_bosch_helper(ax, obj, obj_label):
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    plt.gca().set_aspect('equal', adjustable='box')
 
    for key in obj:
        # color = 'gray' if obj_label != 'region' else 'white'
        color = 'gray' if obj_label != 'region' or (key == 'p0' or key == 'p7') else 'green'
        alpha = 0.6 if obj_label != 'region' or (key == 'p0' or key == 'p7') else 0.1
        for grid in obj[key]:
            x_ = grid[0]
            y_ = grid[1]
            x = []
            y = []
            patches = []
            for point in [(x_, y_), (x_ + 1, y_), (x_ + 1, y_ + 1), (x_, y_ + 1)]:
                x.append(point[0])
                y.append(point[1])
            polygon = Polygon(np.column_stack((x, y)), closed=True)
            patches.append(polygon)
            p = PatchCollection(patches, facecolors=color, edgecolors=color, linewidths=0.2, alpha=alpha)
            ax.add_collection(p)
        # ax.text(np.mean(x) - 0.2, np.mean(y) - 0.2, r'${}_{{{}}}$'.format(key[0], key[1:]), fontsize=12)
        if 'obs' not in key and 'r' not in key and 'public' not in key:
            ax.text(np.mean(x)-0.4, np.mean(y)-0.2, r'${}_{{{}}}$'.format(key[0], key[1:]), fontsize=6)
        if 'publicc' in key:
            ax.text(np.mean(x)-0.4, np.mean(y)-0.2, r'$public$', fontsize=6)
            
        # if 'obs' not in key and 'r' in key:
        #     ax.text(np.mean(x)-0.4, np.mean(y)-0.2, key, fontsize=12)    