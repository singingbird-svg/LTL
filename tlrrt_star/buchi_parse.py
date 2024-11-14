# -*- coding: utf-8 -*-

import subprocess
import os.path
import re
import networkx as nx
import numpy as np
from networkx.classes.digraph import DiGraph
from sympy.logic.inference import satisfiable
from sympy.logic.boolalg import to_dnf
from itertools import combinations
import requests
from bs4 import BeautifulSoup


class Buchi(object):
    """
    construct buchi automaton graph
    """

    def __init__(self, task):
        """
        initialization
        :param task: task specified in LTL
        """
        # task specified in LTL
        self.formula = task.formula
        self.subformula = task.subformula
        self.number_of_robots = task.number_of_robots
        # graph of buchi automaton
        self.buchi_graph = DiGraph(type='buchi', init=[], accept=[])

        # minimal length (in terms of number of transitions) between a pair of nodes
        self.min_length = dict()
   
   #解析 ltl2ba 程序的输出并构建一个 Büchi 自动机  
   #过程：
   #选择 ltl2ba 的运行模式，生成公式对应的自动机输出。
   #解析输出找到所有的状态，并确定初始和接受状态。
   #遍历每个状态，解析并处理每个转移关系。
   #针对有效的转移条件，替换子公式、生成真值表，并添加边到 Büchi 自动机图。
   #为存在 skip 转移的状态添加自环边。           
    def construct_buchi_graph(self):
        """
        parse the output of the program ltl2ba and build the buchi automaton
        """
        #根据program参数决定使用离线或在线模式来生成自动机输出
        program = 'offline'
        if program == 'offline':
            # directory of the program ltl2ba
            dirname = os.path.dirname(__file__)
            # output of the program ltl2ba
            output = subprocess.check_output(dirname + "/.././ltl2ba -f \"" + self.formula + "\"", shell=True).decode(
                "utf-8")
            # find all states/nodes in the buchi automaton
            states = r'\n(\w+):'
            if_fi = r':\n\tif(.*?)fi'

        elif program == 'online':
            para = {
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                'formule': self.formula,
                'convert': 'Convert',
                'image': 'on',
                'descr': 'on',
                'flysimpl': 'on',
                'latsimpl': 'on',
                'sccsimpl': 'on',
                'fjtofj': 'on'
                }
            html_doc = requests.post('http://www.lsv.fr/~gastin/ltl2ba/index.php', data=para)
            # print(html_doc.text)
            output = BeautifulSoup(html_doc.text, 'html.parser').tt.string
            states = r'\n(\w+) :'
            if_fi = r' :(.*?)fi'

        # ---------------------------find all states/nodes in the buchi automaton--------------------

        #在 output 中查找与 states 模式匹配的所有子串，并将结果保存到 state_group 列表中
        state_re = re.compile(states) #re为正则表达式模块；将 states（它应该是一个包含正则表达式模式的字符串）编译成一个正则表达式对象 state_re。这样可以提高后续查找的效率
        state_group = re.findall(state_re, output) #使用 findall 函数在 output 字符串中查找所有与 state_re 模式匹配的子串
        # find initial and accepting states
        init = [s for s in state_group if 'init' in s]
        accept = [s for s in state_group if 'accept' in s]
        # finish the inilization of the graph of the buchi automaton
        #获得所有接受和初始状态
        self.buchi_graph.graph['init'] = init
        self.buchi_graph.graph['accept'] = accept
        
        #self.subformula = {1: '(l1_1)',}
        order_key = list(self.subformula.keys()) #从 self.subformula 字典中提取所有键，并将它们转换成一个列表 order_key
        order_key.sort(reverse=True)
        # for each state/node, find it transition relations
        for state in state_group:
            # add node
            # 将当前状态 state 添加到 Büchi 图 self.buchi_graph 中作为一个节点
            self.buchi_graph.add_node(state)
            # loop over all transitions starting from current state
            state_if_fi = re.findall(state + if_fi, output, re.DOTALL) #使用正则表达式查找从当前状态出发的所有可能的转移条件 if_fi；re.DOTALL 使得正则表达式可以跨多行匹配
            if state_if_fi: #如果找到了转移条件
                relation_group = re.findall(r':: (\(.*?\)) -> goto (\w+)\n\t', state_if_fi[0])  #使用正则表达式在转移条件中查找符号（symbol）和目标状态（next_state）。每一个符号-目标状态对被存储在 relation_group 中。
                for symbol, next_state in relation_group:
                    sym = symbol #保存当前符号 symbol 的初始值
                    # delete edges with multiple subformulas
                    num_pos = 0 #初始化一个计数器 num_pos 来统计符号中的正子公式数量
                    for sym in symbol.split(' && '): #按照&&分割并遍历每个子公式sym
                        if '!' not in sym:  #子公式不包含否定符号!，说明是正子公式
                            num_pos += 1 #统计正子公式的数量
                    if num_pos >= 2: continue
                    # whether the edge is feasible in terms of atomic propositions
                    for k in order_key: #将符号 symbol 中形如 e{k} 的子公式替换为实际的子公式内容 self.subformula[k]，eg.l1_1
                        symbol = symbol.replace('e{0}'.format(k), self.subformula[k])
                    # get the trurh assignment
                    truth_table = self.get_truth_assignment(symbol) #通过 get_truth_assignment 函数生成符号 symbol（命题） 的真值表
                    # infeasible transition
                    if not truth_table: continue   #如果是假命题，跳过
                    # add edge
                    self.buchi_graph.add_edge(state, next_state, truth=truth_table, symbol=sym) 
            else:
                #为 skip 转移添加自环（自我循环）边
                state_skip = re.findall(state + r'(.*?)skip\n', output, re.DOTALL)
                if state_skip:
                    self.buchi_graph.add_edge(state, state, truth='1')

# 获得 [命题 真]这种类型的字母表
    def get_truth_assignment(self, symbol):
        """
        get one set of truth assignment that makes the symbol true
        :param symbol: logical expression which controls the transition
        :return: a set of truth assignment enables the symbol
        """
        # empty symbol
        if symbol == '(1)':
            return '1'
        # non-empty symbol
        else:
            #获得表达式的析取范式
            exp = symbol.replace('||', '|').replace('&&', '&').replace('!', '~') #将||替换成|（表示逻辑“或”）;将&&替换成&（表示逻辑“与”）;将!替换成~（表示逻辑“非”）。
            exp_dnf = to_dnf(exp).__str__() #使用to_dnf()函数将表达式转化为析取范式（DNF）
            # loop over each clause
            # 转换后的表达式会被拆分为若干个子句（使用' | '分隔），每个子句是一种可能的真值分配组合
            # 遍历析取范式的从句
            for clause in exp_dnf.split(' | '):
                truth_table = dict() #创建一个空字典truth_table来存储每个变量的布尔值
                clause = clause.strip('(').strip(')') # 子句会被去掉外层括号
                literals = clause.split(' & ') #按照 & 分割句子
                # loop over each literal
                for literal in literals:
                    if '~' not in literal: #如果不是非，则这个literal是真的
                        truth_table[literal] = True
                    else:
                        truth_table[literal[1:]] = False
                # whether exist a literal with positive and negative version
                # 检查子句中的文字，判断是否存在自相矛盾的情况（即包含正反两种形式的文字）。如果矛盾，则跳过该子句
                '''
                literals 的定义：
                literals 是当前子句中的所有文字(literal)的列表, 包含子句中所有的正负文字。例如，若子句是 (A & ~A & B)，则 literals 为 ['A', '~A', 'B']，包含了两个同样的变量 A，但一个为正文字，另一个为负文字。

                truth_table 的生成：
                对每个文字 literal, 代码将它的变量名（去掉 ~）作为键，取值为 True 或 False, 并存入 truth_table。例如, 若 literals 为 ['A', '~A', 'B']，则 truth_table 生成过程如下：

                处理 A 时, truth_table['A'] = True
                处理 ~A 时, truth_table['A'] = False(会覆盖前面的 True)
                最终, truth_table 变为 {'A': False, 'B': True}
                因此, 当子句中存在矛盾(即同一变量既有正文字又有负文字)时, truth_table 的键数目（即唯一变量数）会比 literals 中的文字数目少
                '''
                if len(literals) != len(truth_table):
                    continue
                else:
                    # exist a robot with two positive literals
                    # 检查是否存在重复的正文字（以字母“_”分割的真值分配），若存在则跳过该子句
                    true_key = [truth.split('_')[1] for truth in truth_table.keys() if truth_table[truth]] #获取命题
                    if len(true_key) != len(set(true_key)): #set(true_key) 将 true_key 列表转换为集合，集合会去除重复的元素
                        continue
                    else:
                        # print(clause, truth_table)
                        return truth_table
            return dict()

#寻找最短路径
    def get_minimal_length(self):
        """
        search the shortest path from a node to another, i.e., # of transitions in the path
        :return: 
        """
        # loop over pairs of buchi states
        #遍历图中的节点
        for head_node in self.buchi_graph.nodes():  #头节点
            for tail_node in self.buchi_graph.nodes(): #尾节点
                # head_node = tail_node, and tail_node is an accepting state
                if head_node != tail_node and 'accept' in tail_node: #如果不是自环且尾节点是accept节点
                    try:
                        length, _ = nx.algorithms.single_source_dijkstra(self.buchi_graph,
                                                                         source=head_node, target=tail_node)  #迪杰斯特拉找最短路径
                    # couldn't find a path from head_node to tail_node
                    #是一段用于捕获异常的代码，旨在处理一种特定情况，即：在尝试寻找图中两个节点之间的最短路径时，如果这两个节点之间没有路径相连，那么将会引发 NetworkXNoPath 异常
                    except nx.exception.NetworkXNoPath:  
                        length = np.inf
                    self.min_length[(head_node, tail_node)] = length
                # head_node != tail_node and tail_node is an accepting state
                # move 1 step forward to all reachable states of head_node then calculate the minimal length
                # 寻找从一个节点到自身的最短路径
                elif head_node == tail_node and 'accept' in tail_node:  #如果头节点和尾节点相等且都为接受状态
                    length = np.inf #将length初始化为正无穷大。这个变量用来存储从 head_node 到 tail_node 的最短路径长度
                    for suc in self.buchi_graph.succ[head_node]: #遍历 head_node 的所有后继节点 suc
                        try:
                            len1, _ = nx.algorithms.single_source_dijkstra(self.buchi_graph,
                                                                           source=suc, target=tail_node)  #计算从后继节点 suc 到 tail_node 的最短路径长度
                        except nx.exception.NetworkXNoPath: #如果没有找到路径（即 NetworkXNoPath 异常），则将 len1 设置为无穷大，表示没有有效路径
                            len1 = np.inf
                        if len1 < length: #如果len1比当前的length小，则更新length。len1+1是因为从head_node到suc的距离需要加上1，表示整个循环路径的长度。
                            length = len1 + 1
                    self.min_length[(head_node, tail_node)] = length

#获得可以从init到达的accept以及可行的后缀
    def get_feasible_accepting_state(self):
        """
        get feasbile accepting/final state, or check whether an accepting state is feaasible
        :return:
        """
        accept = self.buchi_graph.graph['accept']  #保存accept状态
        self.buchi_graph.graph['accept'] = [] 
        for ac in accept: #遍历accept状态
            for init in self.buchi_graph.graph['init']: #遍历init状态
                if self.min_length[(init, ac)] < np.inf and self.min_length[(ac, ac)] < np.inf: #判断前缀和后缀路径是否存在
                    self.buchi_graph.graph['accept'].append(ac)
                    break
        if not self.buchi_graph.graph['accept']:
            print('No feasible accepting states!!!!!!!!! ')
            exit()

#用于解析给定的逻辑表达式symbol，并将其中的区域与机器人编号进行关联
#返回一个字典，其中键是机器人编号，值是与该机器人相关的区域列表
#输入 symbol = 'l1_1 & l3_1 & l4_1 & l4_6 | l3_4 & l5_6'
#输出 {1: ['l1_1', 'l3_1', 'l4_1'], 4: ['l3_4'], 6: ['l4_6', 'l5_6']}
    def robot2region(self, symbol):
        """
        pair of robot and corresponding regions in the expression
        :param symbol: logical expression
        :return: robot index : regions
        eg: input:  exp = 'l1_1 & l3_1 & l4_1 & l4_6 | l3_4 & l5_6'
            output: {1: ['l1_1', 'l3_1', 'l4_1'], 4: ['l3_4'], 6: ['l4_6', 'l5_6']}
        """

        robot_region = dict()
        for r in range(self.number_of_robots):
            findall = re.findall(r'(l\d+?_{0})[^0-9]'.format(r + 1), symbol)
            if findall:
                robot_region[str(r + 1)] = findall

        return robot_region
