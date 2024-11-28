import numpy as np
import networkx as nx
import itertools
import copy
import json
import random
import subprocess

#定义工作空间
class Workspace(object):
    
    def __init__(self, domain_file = './src/default_domain.json', num_of_robots = 6):
        #工作空间大小
        self.length = 15 # 9   # length
        self.width = 40 # 9   # width
        #目标区域
        self.num_of_regions = 8
        self.n_shelf = 6
        self.regions = {'p(0)'.format(i): j for i, j in enumerate(self.allocate_region_dars)}
        self.height = max([cell[1]+1 for region in self.regions.values() for cell in region]) # 9   # 获得region最大x坐标，length
        self.width = max([cell[0]+1 for region in self.regions.values() for cell in region]) # 9   # width        
        #障碍物
        self.num_of_obstacles = 6
        self.occupied = []    
        self.obstacles = {'o{0}'.format(i+1): j for i, j in enumerate(self.allocate_obstacle_dars())}
        #机器人
        self.type_num = {1: num_of_robots} 
        self.type_robot_location = self.initialize()
        self.label_location = {'r{0}'.format(i + 1): j for i, j in enumerate(list(self.type_robot_location.values()))} #标记不同机器人的位置(位置编号，位置)
        self.type_robot_label = dict(zip(self.type_robot_location.keys(), self.label_location.keys()))#（(机器人类型，类型中编号)， 位置编号)

        #建立工作空间的图
        self.graph_workspace = nx.Graph() #建立空图
        self.build_graph() #建图
        self.domain = self.get_domain(domain_file)
        self.load_action_model()
        
#获得已经被离散化的目标区域
    def allocate_region_dars(self):
        regions = []
        #不同区域
        shelf_width_x = 2
        shelf_length_y = 5
        start_charging_station_x = 2
        charging_station_width_x = 4
        charging_station_length_y = 6
        first_shelf_to_charging_station_x = 2
        first_shelf_to_charging_station_y = 2
        inter_shelf_x = 3
        depot_to_last_shelf_x = 2
        depot_width_x = 4
        depot_length_y = 4
        
        #获得charging room的离散化坐标
        regions.append(list(itertools.product(range(start_charging_station_x, start_charging_station_x + charging_station_width_x), range(0, charging_station_length_y)))) 
        n_shelf = 6
        #离散化shelf区域
        for i in range(n_shelf):
            regions.append(list(itertools.product([charging_station_width_x + first_shelf_to_charging_station_x + 
                                                    i * (shelf_width_x + inter_shelf_x) - 1,
                                                    charging_station_width_x + first_shelf_to_charging_station_x + 
                                                    i * (shelf_width_x + inter_shelf_x) + shelf_width_x], 
                                                range(charging_station_length_y + first_shelf_to_charging_station_y,
                                                    charging_station_length_y + first_shelf_to_charging_station_y + shelf_length_y)))) 
 
        regions.append(list(itertools.product(range(charging_station_width_x + first_shelf_to_charging_station_x + 
                                                    (n_shelf - 1) * (shelf_width_x + inter_shelf_x) + shelf_width_x + depot_to_last_shelf_x,
                                                        charging_station_width_x + first_shelf_to_charging_station_x +
                                                    (n_shelf - 1) * (shelf_width_x + inter_shelf_x) + shelf_width_x + depot_to_last_shelf_x + depot_width_x),
                                            range(0, depot_length_y))))
        return regions

#返回障碍物区域  
    def allocate_obstacle_dars(self):
        obstacles = []
        shelf_width_x = 2
        shelf_length_y = 5
        charging_station_width_x = 4
        charging_station_length_y = 6
        first_shelf_to_charging_station_x = 2
        first_shelf_to_charging_station_y = 2
        inter_shelf_x = 3
        
        # p0 charging station
        # p1 grocery p2 health p3 outdors p4 pet p5 furniture p6 electronics
        n_shelf = 6
        for i in range(n_shelf):
            obstacles.append(list(itertools.product(range(charging_station_width_x + first_shelf_to_charging_station_x + 
                                                        i * (shelf_width_x + inter_shelf_x),
                                                        charging_station_width_x + first_shelf_to_charging_station_x + 
                                                        i * (shelf_width_x + inter_shelf_x) + shelf_width_x), 
                                                  range(charging_station_length_y + first_shelf_to_charging_station_y,
                                                        charging_station_length_y + first_shelf_to_charging_station_y + shelf_length_y))))
            

        return obstacles
    

#初始化机器人位置
    def initialize(self):
        type_robot_location = dict()
        x0 = copy.deepcopy(self.regions['p0'])
        #对每一个类型
        for robot_type in self.type_num.keys():
            #类型中的每一个机器人
            for num in range(self.type_num[robot_type]):
                #随机初始化于不同的位置
                while True:
                    candidate = random.sample(x0, 1)[0]
                    if candidate not in type_robot_location.values():
                        type_robot_location[(robot_type, num)] = candidate
                        x0.remove(candidate)
                        break
        return type_robot_location            

#找到下一步可以到达的位置   
    def reachable(self, location, obstacles):
        #将不在障碍物内，且没有超过边界，则将旁边的位置加入
        next_location = [location, location]  #初始化假设location不变
        #left
        if location[0] -1 > 0 and (location[0]-1, location[1]) not in obstacles:
            next_location.append((location, (location[0]-1, location[1])))
        # right
        if location[0]+1 < self.width and (location[0]+1, location[1]) not in obstacles:
            next_location.append((location, (location[0]+1, location[1])))
        # up
        if location[1]+1 < self.height and (location[0], location[1]+1) not in obstacles:
            next_location.append((location, (location[0], location[1]+1)))
        # down
        if location[1]-1 > 0 and (location[0], location[1]-1) not in obstacles:
            next_location.append((location, (location[0], location[1]-1)))      
        return next_location
 
#建图，将工作空间中的点和可行边    
    def build_graph(self):
        obstacles = list(itertools.chain(*self.obstacles.values()))    #将所有障碍物坐标合并成一个包含所有障碍物位置的列表
        for i in range(self.width):
            for j in range(self.height):
                #如果不在障碍物区域
                if (i, j) not in obstacles:
                    #返回可达的边
                    self.graph_workspace.add_edges_from(self.reachable((i,j), obstacles))
    
    def get_domain(self, domain_file):
        #是一个嵌套函数，它用于移除 JSON 字符串中的注释
        def remove_comments(json_str):
            return '\n'.join([line for line in json_str.split('\n') if not line.strip().startswith('//')])

        with open(domain_file, 'r') as f:
            data = f.read()

        cleaned_data = remove_comments(data)
        #json.loads() 将去除注释后的字符串解析成 JSON 对应的 Python 数据结构
        return json.loads(cleaned_data)        
    
    #建立动作的模型
    def load_action_model(self):
        self.action_model = nx.DiGraph()
        self.action_model.add_nodes_from(self.domain['action_model']['nodes']) #添加动作节点  
        
        for edge in self.domain['action_model']['edges']:
            from_node = edge['from']
            to_node = edge['to']
            label = edge['label']
            self.action_model.add_edge(from_node, to_node, label=label) #起点，终点，动作标签
        
        title = "./data/action_model"
        nx.nx_agraph.write_dot(self.action_model, title+'.dot') #将图导出为action_model.dot 文件
        command = "dot -Tpng {0}.dot >{0}.png".format(title) # 将 .dot 文件转换成 PNG 图像，存储在指定路径下。
        subprocess.run(command, shell=True, capture_output=True, text=True)     #自动生成图像文件           
    
    def name(self):
        return "supermarket"    