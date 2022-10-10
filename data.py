import numpy as np
from block import Block
from dag import DAG
from dag import DFS
import csv


class Data:
    def __init__(self):
        self.block_dict = self.read_data('data/attachment1.csv')
        self.read_read_and_write('data/attachment2.csv')
        self.read_successor('data/attachment3.csv')
        # print(self.block_dict)
        self.process_hash = {}
        self.process_alu = {}
        self.construct_control_dependency()
        self.construct_data_dependency()
        self.construct_process_dict('data/process_hash.csv', self.process_hash)
        self.construct_process_dict('data/process_alu.csv', self.process_alu)

    def read_data(self, file_path):
        # return {id:model}
        re = {}
        with open(file_path) as infile:
            infile.readline()
            for line in infile:
                info = line.split(',')
                re[int(info[0])] = Block(int(info[0]), int(info[1]), int(info[2]), int(info[3]), int(info[4]))
        return re

    def read_read_and_write(self, file_path):
        with open(file_path) as infile:
            for line in infile:
                info = line.split(',')
                id = int(info[0])
                mode = info[1]
                if len(info) > 2:
                    items = info[2:]
                    data = set()
                    for item in items:
                        data.add(int(item[1:]))
                    if mode == 'W':
                        self.block_dict[id].set_write(data)
                    elif mode == 'R':
                        self.block_dict[id].set_read(data)

    def read_successor(self, file_path):
        with open(file_path) as infile:
            for line in infile:
                info = line.split(',')
                id = int(info[0])
                if len(info) > 1:
                    items = info[1:]
                    data = set()
                    for item in items:
                        data.add(int(item))
                    self.block_dict[id].set_successor(data)

    def update_with_dag(self, dag: DAG):
        for v in range(607):
            v_adj = dag.adj(v)
            new_successor = set()
            for w in v_adj:
                new_successor.add(w)
            self.block_dict[v].set_successor(new_successor)

    def construct_dag(self):
        dag = DAG(607)
        for v in range(607):
            for w in self.block_dict[v].successor:
                dag.add_edge(v, w)
        dag.set_natural_start()
        return dag

    def construct_control_dependency(self):
        dag = self.construct_dag()
        dag.add_exit()
        dag.add_entry()
        cdg = dag.get_cdg()
        for v in range(607):
            v_cdg_children = set()
            dfs = DFS(cdg)
            dfs.dfs(v)
            for w in range(607):
                if dfs.is_marked(w) and w != v and w <= 606:
                    v_cdg_children.add(w)
            self.block_dict[v].control = v_cdg_children

    def construct_data_dependency(self):
        dag = self.construct_dag()
        for v in range(607):
            v_read_vars = self.block_dict[v].read
            v_write_vars = self.block_dict[v].write
            v_RAW_children = set()
            v_WAR_children = set()
            v_WAW_children = set()
            dfs = DFS(dag)
            dfs.dfs(v)
            for w in range(607):
                if w != v and dfs.is_marked(w) == True:
                    w_read_vars = self.block_dict[w].read
                    w_write_vars = self.block_dict[w].write
                    for w_read_var in w_read_vars:
                        # v写w读
                        if w_read_var in v_write_vars:
                            v_RAW_children.add(w)
                    for w_write_var in w_write_vars:
                        # v读w写
                        if w_write_var in v_read_vars:
                            v_WAR_children.add(w)
                        # v写w写
                        if w_write_var in v_write_vars:
                            v_WAW_children.add(w)
            self.block_dict[v].read_after_write = v_RAW_children
            self.block_dict[v].write_after_read = v_WAR_children
            self.block_dict[v].write_after_write = v_WAW_children

    def construct_process_dict(self, file_path, process):
        with open(file_path) as infile:
            for line in infile:
                info = line.split(',')
                id = int(info[0])
                process[id] = []
                for i in info[1:]:
                    process[id].append(int(i))


