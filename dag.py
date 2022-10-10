import copy
import csv
import sys

sys.setrecursionlimit(1000000)


class DAG:
    def __init__(self, v_num):
        self.V = v_num  # 节点数
        self.E = 0  # 边数
        self.adj = [[] for _ in range(self.V)]  # 邻接表（保留三个位置给start，end，entry）
        self.in_degree = [0] * self.V  # 入度（保留三个位置给start，end，entry）
        # start, exit, entry默认值
        self.start = v_num
        self.exit = v_num + 1
        self.entry = v_num + 2

    def add_edge(self, v, w):
        self.E += 1
        self.in_degree[w] += 1
        self.adj[v].append(w)

    def remove_edge(self, v, w):
        self.E -= 1
        self.in_degree[w] -= 1
        self.adj[v].remove(w)

    # 获得和v相邻且有从v指向它的边的节点
    def get_adj(self, v):
        return self.adj[v]

    # 获得一个dict：键为节点，值为包含该节点所有子树中节点的set
    def get_children_dict(self):
        children = {}
        for v in range(self.V):
            dfs = DFS(self)
            dfs.dfs(v)
            v_children = set()
            for w in range(self.V):
                if dfs.is_marked(w) == True and w != v:
                    v_children.add(w)
            children[v] = v_children

        return children

    def get_in_degree(self, v):
        return self.in_degree[v]

    def get_V(self):
        return self.V

    def get_E(self):
        return self.E

    def reverse_dag(self):
        reverse = DAG(self.V)
        for v in range(self.V):
            for w in self.get_adj(v):
                reverse.add_edge(w, v)
        return reverse

    def add_start(self):
        # 找出所有入度为0的节点
        start_nodes = set()
        for v in range(self.V):
            if self.in_degree[v] == 0:
                start_nodes.add(v)

        self.V += 1
        self.start = self.V - 1
        self.adj.append([])
        self.in_degree.append(0)
        # 添加entry到start的边
        for start_node in start_nodes:
            self.add_edge(self.start, start_node)

    def set_natural_start(self):
        count = 0
        for v in range(self.V):
            if self.in_degree[v] == 0:
                count += 1
                s = v
        if count == 1:
            self.start = s

    def set_start(self, v):
        self.start = v

    def get_natural_start(self):
        count = 0
        for v in range(self.V):
            if self.in_degree[v] == 0:
                count += 1
                s = v
        if count == 1:
            return s
        else:
            return -1

    def add_exit(self):

        # 找出所有出度为0的节点
        end_nodes = set()
        for v in range(self.V):
            v_adj = self.get_adj(v)
            if len(v_adj) == 0:
                end_nodes.add(v)

        self.V += 1
        self.exit = self.V - 1
        self.adj.append([])
        self.in_degree.append(0)

        # 添加end到exit的边
        for end_node in end_nodes:
            self.add_edge(end_node, self.exit)

    def set_exit(self, v):
        self.exit = v

    def add_entry(self):
        self.V += 1
        self.entry = self.V - 1
        self.adj.append([])
        self.in_degree.append(0)
        self.add_edge(self.entry, self.start)
        self.add_edge(self.entry, self.exit)

    # 构建支配字典 （节点：被这个节点支配的节点set）
    def get_dominator_dict(self):
        # 以dict形式维护每个节点支配的节点
        dominator_dict = {}
        # 先从start进行一次dfs
        dfs = DFS(self)
        dfs.dfs(self.start)
        # 保存所有能访问到的节点
        visited_before_removal = set()
        for v in range(self.V):
            if dfs.is_marked(v) == True:
                visited_before_removal.add(v)
        # print("visited_before_removal:", visited_before_removal)

        # 每次去掉一个点v（不包括start，end和entry）进行dfs
        for v in range(self.V):
            temp_dag = copy.deepcopy(self)

            # 在当前dag的复制中去掉点v: 如果点w后继中有v则删掉
            for w in range(self.V):
                if v in temp_dag.get_adj(w):
                    temp_dag.remove_edge(w, v)

            # 再对删除v后的dag进行一次dfs
            dfs = DFS(temp_dag)
            if v != temp_dag.start:
                dfs.dfs(temp_dag.start)
            # 保存此时能访问到的节点
            visited_after_removal = set()
            for w in range(temp_dag.V):
                if dfs.is_marked(w) == True:
                    visited_after_removal.add(w)

            # print("visited_after_removal", v, visited_after_removal)

            # 如果有节点之前能访问到但现在访问不到，则点v支配它
            dominated_by_v = set()
            for w in range(temp_dag.V):
                if w in visited_before_removal and w not in visited_after_removal:
                    dominated_by_v.add(w)

            # 保存v和被v支配的节点
            dominator_dict[v] = dominated_by_v

        return dominator_dict

    # 构建支配树
    def get_dominator_tree(self):
        dominator_dict = self.get_dominator_dict()
        # for k, v in dominator_dict.items():
        #     print("dominator_dict:", k, ": ", v)

        dominator_tree = DAG(self.V)
        for v in range(dominator_tree.V):
            dominated_by_v = dominator_dict[v]
            for w in dominated_by_v:
                if w == v:
                    continue

                if len(dominator_tree.get_adj(w)) == 0:
                    dominator_tree.add_edge(w, v)
                else:
                    ptr = w
                    # 向上找直到找到不被v支配或到根节点
                    while ptr in dominated_by_v and len(dominator_tree.get_adj(ptr)) != 0 and ptr != v:
                        pre = ptr
                        ptr = dominator_tree.get_adj(ptr)[0]

                    if ptr != v:
                        if ptr not in dominated_by_v:
                            if len(dominator_tree.get_adj(pre)) != 0:
                                dominator_tree.remove_edge(pre, dominator_tree.get_adj(pre)[0])
                            dominator_tree.add_edge(pre, v)
                        else:
                            if len(dominator_tree.get_adj(ptr)) != 0:
                                dominator_tree.remove_edge(ptr, dominator_tree.get_adj(ptr)[0])
                            dominator_tree.add_edge(ptr, v)

        # for v in range(dominator_tree.V):
        #     print("dominator tree", v, "adj:", dominator_tree.get_adj(v))
        return dominator_tree

    # 获得dict形式的的支配边界（节点：节点的支配边界set）
    def get_dominance_frontier(self):
        dominator_tree = self.get_dominator_tree()
        # 根据支配树构建直接支配者dict（节点：节点的直接支配者）
        idom_dict = {}
        for v in range(dominator_tree.V):
            for w in dominator_tree.get_adj(v):
                idom_dict[v] = w

        # for k, v in idom_dict.items():
        #     print("idom_dict:", k, ": ", v)

        # 根据CFG（当前DAG）构建predecessor dict（节点：节点CFG中的直接前序节点）
        pred_dict = {}
        for v in range(self.V):
            pred_dict[v] = set()
        for v in range(self.V):
            for w in self.get_adj(v):
                pred_dict[w].add(v)

        # for k, v in pred_dict.items():
        #     print("pred_dict:", k, ": ", v)

        # 支配边界dict
        df_dict = {}
        for v in range(self.V):
            df_dict[v] = set()
        for v in range(self.V):
            for predecessor in pred_dict[v]:
                runner = predecessor
                while runner != idom_dict[v]:
                    df_dict[runner].add(v)
                    runner = idom_dict[runner]

        return df_dict

    # 直接返回控制依赖树（无需手动反转，但需要手动添加伪节点）
    def get_cdg(self):
        re_dag = self.reverse_dag()
        re_dag.set_natural_start()
        df_dict = re_dag.get_dominance_frontier()
        cdg = DAG(self.V)
        for v, v_df_list in df_dict.items():
            for df in v_df_list:
                cdg.add_edge(df, v)
        return cdg


class DFS:
    def __init__(self, dag: DAG):
        self.marked = [False for _ in range(610)]
        self.count = 0
        self.dag = dag
        self.keys = set()
        self.stack = []
        self.process_dict = {}
        self.process_count = 0

        self.i = 0
        for v in range(self.dag.V):
            self.marked[v] = False

    def dfs(self, v):
        self.marked[v] = True
        self.count += 1
        for w in self.dag.get_adj(v):
            if self.marked[w] != True:
                self.dfs(w)

    def is_marked(self, v):
        return self.marked[v]

    def get_count(self):
        return self.count

    def dfs_process(self, v, block_dict):
        self.stack.append(v)

        if len(self.dag.get_adj(v)) == 0:
            add_list = []
            key = ""
            sum_val = 0
            for i in self.stack:
                if block_dict[i].alu > 0:
                    add_list.append(i)
                    key += str(i)
                    sum_val += block_dict[i].alu
            if key not in self.keys and key != "" and sum_val > 56:
                outfile = open("process_alu.csv", 'a+', newline="")
                csvWriter = csv.writer(outfile, delimiter=',')
                output = []
                output.append(self.i)
                self.i += 1
                for v in add_list:
                    output.append(v)
                csvWriter.writerow(output)
                outfile.close()
                print(output)
                self.keys.add(key)
            # for i in self.stack:
            #     if block_dict[i].hash > 0:
            #         add_list.append(i)
            #         key += str(i)
            #         sum_val += block_dict[i].hash
            # if key not in self.keys and key!="" and sum_val > 2:
            #     outfile = open("process_hash.csv", 'a+', newline="")
            #     csvWriter = csv.writer(outfile, delimiter=',')
            #     output = []
            #     output.append(self.i)
            #     self.i+=1
            #     for v in add_list:
            #         output.append(v)
            #     csvWriter.writerow(output)
            #     outfile.close()
            #     print(output)
            #     self.keys.add(key)
            self.process_count += 1

        for w in self.dag.get_adj(v):
            self.dfs_process(w, block_dict)

        self.stack.pop()

    def get_process_dict(self):
        return self.process_dict

# if __name__ == "__main__":
#     dag = DAG(8)
#     dag.add_edge(0, 1)
#     dag.add_edge(1, 2)
#     dag.add_edge(2, 3)
#     dag.add_edge(2, 4)
#     dag.add_edge(3, 5)
#     dag.add_edge(3, 6)
#     dag.add_edge(5, 7)
#     dag.add_edge(6, 7)
#     dag.add_edge(7, 2)
#     dag.set_start(0)
#     # print("raw dag V:", dag.get_V())
#     # print("raw dag E:", dag.get_E())
#
#     dag.add_exit()
#     dag.add_edge(0, dag.exit)
#     # print("add exit:", dag.exit)
#     # print("add exit dag start:", dag.start)
#     # print("add exit dag V:", dag.get_V())
#     # print("add exit dag E:", dag.get_E())
#
#     # re_dag = dag.reverse_dag()
#     # re_dag.set_natural_start()
#
#     # print("reverse dag start:", re_dag.start)
#     # print("reverse dag V:", re_dag.get_V())
#     # print("reverse dag E:", re_dag.get_E())
#
#     cdg = dag.get_cdg()
#     # for v in range(cdg.V):
#     #     print(v, "adj:", cdg.get_adj(v))
#     for k, v in cdg.get_children_dict().items():
#         print("children dict:", k, "children: ", v)










