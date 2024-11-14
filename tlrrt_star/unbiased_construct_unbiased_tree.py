# -*- coding: utf-8 -*-

import numpy as np
import pyvisgraph as vg
import sys
import datetime

# 一个基于无偏采样和布尔接收条件的路径规划算法。
# 它在一个状态空间中通过迭代构建树结构，不断扩展节点，并确保路径无碰撞、满足接收条件（Büchi）。
# 通过检测是否遇到目标状态，最终返回一条可行的路径
def construction_unbiased_tree(tree, n_max):
    """
    construction of the unbiased tree
    :param tree: unbiased tree
    :param n_max: maximum number of iterations
    :return: found path
    """
    # trivial suffix path, the initial state can transition to itself
    #如果是后缀且tree.init[1]能够根据label转移回到init
    #tree.init[1]有自环
    if tree.segment == 'suffix' and tree.check_transition_b(tree.init[1], tree.unbiased_tree.nodes[tree.init]['label'],
                                                            tree.init[1]):
        #将初始状态添加到目标集合tree.goals中
        tree.goals.add(tree.init)
        #如果在布尔图（Büchi graph）中，初始状态的转移条件满足接受条件，则返回一个初始状态的路径。
        if tree.buchi.buchi_graph.edges[(tree.init[1], tree.init[1])]['truth'] == '1':
            return {0: [0, []]}
        else: #返回一个包含初始状态的路径
            return {0: [0, [tree.init]]}
    s = datetime.datetime.now()
    #构建前缀的树或者后缀（但不自环？）
    for n in range(n_max): 
        #不能超时
        if (datetime.datetime.now() - s).total_seconds() > 2000: #  or n > 2000:
            print('overtime')
            exit()
        # unbiased sample
        x_rand = list()
        x_rand.append(tree.sample())  #采样工作空间内的一个点
        #为每一个机器人找到一个有效采样点
        for i in range(1, tree.robot):
           # 这是一个无限循环，直到找到一个有效的，无碰撞的采样点。
            while 1:
                point = tree.sample()
                if tree.collision_avoidance(point, x_rand):
                    x_rand.append(tree.sample())#多个x_rand
                    break

        x_rand = tuple(x_rand)

        q_nearest = tree.nearest(x_rand) #找到距离x_rand位置距离最近的q_nearest
        x_new = tree.steer(x_rand, q_nearest[0][0]) #x_rand向q_nearest方向移动一步

        # label of x_new
        label = []
        # 为每个机器人计算其在状态x_new下的标签（get_label）。如果标签存在，则添加编号
        for i in range(tree.robot):
            ap = tree.get_label(x_new[i])
            ap = ap + '_' + str(i + 1) if ap != '' else ap
            label.append(ap)
        # near state
        # 检查x_new到达目标是否有障碍物。如果是轻量模式（lite），并且发现障碍物，则跳过此节点。
        if tree.lite:
            # avoid near
            near_nodes = [q_nearest]
        else:
            near_nodes = tree.near(tree.mulp2single(x_new))
            near_nodes = near_nodes + q_nearest if q_nearest[0] not in near_nodes else near_nodes
        # check the line is obstacle-free
        obs_check = tree.obstacle_check(near_nodes, x_new, label)
        # not obstacle-free
        if tree.lite and not list(obs_check.items())[0][1]: continue

        # iterate over each buchi state
        for b_state in tree.buchi.buchi_graph.nodes:
            # new product state
            q_new = (x_new, b_state)
            # extend
            added = tree.extend(q_new, near_nodes, label, obs_check)
            # rewire
            if not tree.lite and added:
            #     print(len(near_nodes))
                tree.rewire(q_new, near_nodes, obs_check)

        # detect the first accepting state
        # if len(tree.goals): break
        # 找到goals就break
        if len(tree.goals) > 0 and tree.segment == 'prefix':
            # print(n, end=' ')
            break
        if len(tree.goals) > 0 and tree.segment == 'suffix':
            # print(n, end=' ')
            break
    return tree.find_path(tree.goals)


def path_via_visibility(tree, path):
    """
    using the visibility graph to find the shortest path
    :param tree: unbiased tree
    :param path: path found by the first step of the suffix part
    :return: a path in the free workspace (after treating all regions as obstacles) and its distance cost
    """
    paths = []
    max_len = 0
    # find a path for each robot using visibility graph method
    for i in range(tree.robot):
        init = path[-1][0][i]
        goal = path[0][0][i]
        shortest = tree.g.shortest_path(vg.Point(init[0], init[1]), vg.Point(goal[0], goal[1]))
        max_len = len(shortest) if len(shortest) > max_len else max_len
        paths.append([(point.x, point.y) for point in shortest])
    # append to the same length
    for i in range(tree.robot):
        paths[i] = paths[i] + [paths[i][-1]]*(max_len-len(paths[i]))
    # combine to one path of product state
    path_free = [(tuple([p[i] for p in paths]), '') for i in range(max_len)]  # second component serves as buchi state
    # calculate cost
    cost = 0
    for i in range(1, max_len):
        cost = cost + np.linalg.norm(np.subtract(tree.mulp2single(path_free[i][0]), tree.mulp2single(path_free[i-1][0])))

    return cost, path_free
