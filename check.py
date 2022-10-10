from data import Data
from gurobipy import *
import numpy as np
import csv
from dag import DAG
import copy
from dag import DFS


def dfs_process(v, cfg, stack, process):
    stack.append(v)

    if len(cfg.get_adj(v)) == 0:
        process.append(copy.deepcopy(stack))

    for w in cfg.get_adj(v):
        dfs_process(w, cfg, stack, process)

    stack.pop()


data = Data()
level = {}
file_path = 'output_problem_2.csv'
with open(file_path) as infile:
    for line in infile:
        info = line.split(',')
        id = int(info[0])
        if float(info[3]) > 56:
            level[id] = []
            for i in info[5:]:
                level[id].append(int(i))
raw_cfg = data.construct_dag()
children_dict = raw_cfg.get_children_dict()

alu_cfg = DAG(607)
for v, v_children in children_dict.items():
    if data.block_dict[v].alu > 0:
        for v_child in v_children:
            if data.block_dict[v_child].alu > 0:
                alu_cfg.add_edge(v, v_child)
children_dict = alu_cfg.get_children_dict()
flag = True
while flag:
    flag = False
    for v in range(607):
        print("2:", v)
        for w in alu_cfg.get_adj(v):
            w_children = children_dict[w]
            for x in alu_cfg.get_adj(v):
                if x in w_children:
                    alu_cfg.remove_edge(v, x)
                    flag = True
children_dict = alu_cfg.get_children_dict()

for id, value in level.items():
    cfg = DAG(607)
    for block in value:
        for block2 in value:
            if block2 in children_dict[block]:
                cfg.add_edge(block, block2)

    root = set()
    for v in value:
        if cfg.get_in_degree(v) == 0:
            root.add(v)

    processes = []
    stack = []
    for r in root:
        dfs_process(r, cfg, stack, processes)
    print(root)
    print(value)
    print(processes)
    for process in processes:
        sum_val = 0
        for i in process:
            sum_val += data.block_dict[i].alu
        if sum_val > 56:
            print(process)

    pass
