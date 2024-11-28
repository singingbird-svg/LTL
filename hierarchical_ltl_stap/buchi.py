import networkx as nx
import os
import time
import subprocess
import re
from sympy.logic.boolalg import to_dnf, And, Or, Not, Implies
#构建布奇自动机
class BuchiConstructor(object):
    def __init__(self) -> None:
        pass
    #根据formula建立布奇自动机图
    def construct_buchi_graph(self, formula):
        buchi_graph = nx.DiGraph(name="buchi_graph", formula=formula)       
        #调用外部ltl2ba
        dirname = os.path.dirname(__file__) #ltl2ba可执行文件位置
        before = time.time()
        output = subprocess.check_output(dirname + "/./../ltl2ba -f \"" + formula + "\"", shell=True).decode(
            "utf-8") #subprocess.check_output() 用于运行一个外部命令并捕获其输出（标准输出）
        '''
        如果 output 包含以下内容：
        Foo:
            Something
        Bar:
            Another thing
        Baz:
            Yet another
        则 re.findall(state_re, output) 会返回一个包含所有匹配单词的列表：['Foo', 'Bar', 'Baz']        
        '''
        state_re = re.compile(r'\n(\w+):\n\t') #正则表达式
        state_group = re.findall(state_re, output)
        #init and accept
        init = [s for s in state_group if 'init' in s]
        accept = [s for s in state_group if 'accept' in s]
        #在布奇自动机图中初始化init和accept状态
        buchi_graph.graph['init'] = init
        buchi_graph.graph['accept'] = accept   
        #遍历state_group的状态
        for state in state_group:
            buchi_graph.add_node(state, label = to_dnf('0'), name=state) #state为节点，to_dnf将内容转化为析取表达式
            state_if_fi = re.findall(state + r':\n\tif(.*?)fi', output, re.DOTALL) #用于查找 output 中与 state 相关的 if 语句
            if state_if_fi: #根据从 state_if_fi 提取的条件关系，更新一个布尔自动机图
                relation_group = re.findall(r':: (\(.*?\)) -> goto (\w+)\n\t', state_if_fi[0]) #从 state_if_fi[0]（一个字符串）中提取符合特定模式的关系。
                for symbol, next_state in relation_group:
                    symbol = symbol.replace('||', '|').replace('&&', '&').replace('!', '~')
                    formula = to_dnf(symbol)
                    # @TODO prune
                    # update node, do not create edges for selfloop
                    if state == next_state:
                        buchi_graph.nodes[state]['label'] = formula
                    else:
                        buchi_graph.add_edge(state, next_state, label=formula)
                        # print(buchi_graph.edges[(state, next_state)])

            else:
                state_skip = re.findall(state + r':\n\tskip\n', output, re.DOTALL)
                if state_skip:
                    buchi_graph.nodes[state]['label'] = to_dnf('1')
                    
        # delete vertices without selfloop
        # self.delete_node_no_selfloop_except_init_accept(buchi_graph)
        # add sink state
        buchi_graph.add_node('sink', label=to_dnf('1'), name=state)
        for acpt_state in buchi_graph.graph['accept']:
            buchi_graph.nodes[acpt_state]['label'] = to_dnf('0')
            buchi_graph.add_edge(acpt_state, 'sink', label=to_dnf('1'))
            
        
        return buchi_graph                    