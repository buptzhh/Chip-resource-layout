from data import Data
from gurobipy import *
import numpy as np
import csv

# 设置初始最大级数
max_length = 64


class simulator:
    def __init__(self):
        # 获取输入参数
        self.data = Data()

    def static_algorithm_for_problem1(self):
        # 模型建立
        model = Model()

        # 每级是否使用变量：0-1
        y = {}
        for j in range(max_length):
            y[j] = model.addVar(lb=0, ub=1, vtype=GRB.BINARY, name="package_" + str(j), obj=0, column=None)
        # 被占用的每级的前一级也需要被占用，防止空级
        for j in range(1, max_length):
            model.addConstr(y[j - 1] >= y[j], name='c_pre_' + str(j))
        # 基本块i是否放在j级：0-1
        x = {}
        for i in range(len(self.data.block_dict)):
            for j in range(max_length):
                x[str(i) + "_" + str(j)] = model.addVar(lb=0, ub=1, vtype=GRB.BINARY, name="x_" + str(i) + "_" + str(j),
                                                        obj=0, column=None)

        # 块每一级如果被占用，则至少有一个基本块被排布到该级；基本块被排布到某一级时，该级则被占用。
        for j in range(max_length):
            model.addConstr(
                y[j] * GRB.MAXINT >= quicksum(x[str(i) + "_" + str(j)] for i in range(len(self.data.block_dict))),
                name="y_01_" + str(j))
            model.addConstr(
                quicksum(x[str(i) + "_" + str(j)] for i in range(len(self.data.block_dict))) * GRB.MAXINT >= y[j],
                name="y_10_" + str(j))
        # 基本块必须被放置
        for i in range(len(self.data.block_dict)):
            model.addConstr(quicksum(x[str(i) + "_" + str(j)] for j in range(max_length)) == 1, name="x_sum_" + str(i))
        # resource constraint
        for j in range(max_length):
            model.addConstr(quicksum(
                (self.data.block_dict[i].tcam * x[str(i) + "_" + str(j)]) for i in
                range(len(self.data.block_dict))) <= 1,
                            name="tcam_of_" + str(j))
            model.addConstr(quicksum(
                (self.data.block_dict[i].hash * x[str(i) + "_" + str(j)]) for i in
                range(len(self.data.block_dict))) <= 2,
                            name="hash_of_" + str(j))
            model.addConstr(quicksum(
                (self.data.block_dict[i].alu * x[str(i) + "_" + str(j)]) for i in
                range(len(self.data.block_dict))) <= 56,
                            name="alu_of_" + str(j))
            model.addConstr(quicksum(
                (self.data.block_dict[i].qualfy * x[str(i) + "_" + str(j)]) for i in
                range(len(self.data.block_dict))) <= 64,
                            name="qualfy_of_" + str(j))
        # 折叠层资源限制
        for j in range(16):
            model.addConstr(quicksum(
                (self.data.block_dict[i].tcam * (x[str(i) + "_" + str(j)] + x[str(i) + "_" + str(j + 16)])) for i in
                range(len(self.data.block_dict))) <= 1,
                            name="tcam_of_fold_" + str(j))
            model.addConstr(quicksum(
                (self.data.block_dict[i].hash * (x[str(i) + "_" + str(j)] + x[str(i) + "_" + str(j + 16)])) for i in
                range(len(self.data.block_dict))) <= 3,
                            name="hash_of_fold_" + str(j))
        # TCAM资源偶数级数限制
        model.addConstr(quicksum(
            (self.data.block_dict[i].tcam * x[str(i) + "_" + str(j)]) for i in range(len(self.data.block_dict)) for j in
            range(max_length) if j % 2 == 0) <= 5,
                        name="tcam_on_even")
        # 控制依赖和数据依赖
        for i in range(len(self.data.block_dict)):
            for k in self.data.block_dict[i].control:
                model.addConstr(quicksum((j * x[str(i) + "_" + str(j)]) for j in range(max_length)) <=
                                quicksum((j * x[str(k) + "_" + str(j)]) for j in range(max_length)),
                                name="control_" + str(i) + "_" + str(k))
            for k in self.data.block_dict[i].write_after_read:
                if k not in self.data.block_dict[i].control:
                    model.addConstr(quicksum((j * x[str(i) + "_" + str(j)]) for j in range(max_length)) <=
                                    quicksum((j * x[str(k) + "_" + str(j)]) for j in range(max_length)),
                                    name="write_after_read_" + str(i) + "_" + str(k))
            for k in self.data.block_dict[i].write_after_write:
                model.addConstr(quicksum((j * x[str(i) + "_" + str(j)]) for j in range(max_length)) + 1 <=
                                quicksum((j * x[str(k) + "_" + str(j)]) for j in range(max_length)),
                                name="write_after_write_" + str(i) + "_" + str(k))
            for k in self.data.block_dict[i].read_after_write:
                if k not in self.data.block_dict[i].write_after_write:
                    model.addConstr(quicksum((j * x[str(i) + "_" + str(j)]) for j in range(max_length)) + 1 <=
                                    quicksum((j * x[str(k) + "_" + str(j)]) for j in range(max_length)),
                                    name="read_after_write_" + str(i) + "_" + str(k))
        # objective
        f = quicksum(value for key, value in y.items())
        model.setObjective(f, GRB.MINIMIZE)

        # setParam
        model.setParam(GRB.Param.Threads, 4)

        model.Params.timelimit = 3600 * 6
        model.Params.LogToConsole = True
        model.optimize()
        model.write('model_1.lp')
        if model.status == GRB.Status.OPTIMAL:
            print("optimal")
            print("Optimal Objective Value", model.objVal)
            pass
        elif model.status == GRB.Status.INFEASIBLE:
            print("infeasible")
        self.output('output_problem_1.csv', x, y)
        pass

    def static_algorithm_for_problem2(self):
        # 模型建立
        model = Model()

        # 每级是否使用变量：0-1
        y = {}
        for j in range(max_length):
            y[j] = model.addVar(lb=0, ub=1, vtype=GRB.BINARY, name="package_" + str(j), obj=0, column=None)
        # 被占用的每级的前一级也需要被占用，防止空级
        for j in range(1, max_length):
            model.addConstr(y[j - 1] >= y[j], name='c_pre_' + str(j))
        # 基本块i是否放在j级：0-1
        x = {}
        for i in range(len(self.data.block_dict)):
            for j in range(max_length):
                x[str(i) + "_" + str(j)] = model.addVar(lb=0, ub=1, vtype=GRB.BINARY, name="x_" + str(i) + "_" + str(j),
                                                        obj=0, column=None)

        # 每一级如果被占用，则至少有一个基本块被排布到该级；基本块被排布到某一级时，该级则被占用。
        for j in range(max_length):
            model.addConstr(
                y[j] * GRB.MAXINT >= quicksum(x[str(i) + "_" + str(j)] for i in range(len(self.data.block_dict))),
                name="y_01_" + str(j))
            model.addConstr(
                quicksum(x[str(i) + "_" + str(j)] for i in range(len(self.data.block_dict))) * GRB.MAXINT >= y[j],
                name="y_10_" + str(j))
        # 基本块必须被放置
        for i in range(len(self.data.block_dict)):
            model.addConstr(quicksum(x[str(i) + "_" + str(j)] for j in range(max_length)) == 1, name="x_sum_" + str(i))
        # resource constraint
        for j in range(max_length):
            model.addConstr(quicksum(
                (self.data.block_dict[i].tcam * x[str(i) + "_" + str(j)]) for i in
                range(len(self.data.block_dict))) <= 1,
                            name="tcam_of_" + str(j))
            model.addConstr(quicksum(
                (self.data.block_dict[i].qualfy * x[str(i) + "_" + str(j)]) for i in
                range(len(self.data.block_dict))) <= 64,
                            name="qualfy_of_" + str(j))
        # 折叠层资源限制
        for j in range(16):
            model.addConstr(quicksum(
                (self.data.block_dict[i].tcam * (x[str(i) + "_" + str(j)] + x[str(i) + "_" + str(j + 16)])) for i in
                range(len(self.data.block_dict))) <= 1,
                            name="tcam_of_fold_" + str(j))
        # TCAM资源偶数级数限制
        model.addConstr(quicksum(
            (self.data.block_dict[i].tcam * x[str(i) + "_" + str(j)]) for i in range(len(self.data.block_dict)) for j in
            range(max_length) if j % 2 == 0) <= 5,
                        name="tcam_on_even")
        # 控制依赖和数据依赖
        for i in range(len(self.data.block_dict)):
            for k in self.data.block_dict[i].control:
                model.addConstr(quicksum((j * x[str(i) + "_" + str(j)]) for j in range(max_length)) <=
                                quicksum((j * x[str(k) + "_" + str(j)]) for j in range(max_length)),
                                name="control_" + str(i) + "_" + str(k))
            for k in self.data.block_dict[i].write_after_read:
                if k not in self.data.block_dict[i].control:
                    model.addConstr(quicksum((j * x[str(i) + "_" + str(j)]) for j in range(max_length)) <=
                                    quicksum((j * x[str(k) + "_" + str(j)]) for j in range(max_length)),
                                    name="write_after_read_" + str(i) + "_" + str(k))
            for k in self.data.block_dict[i].write_after_write:
                model.addConstr(quicksum((j * x[str(i) + "_" + str(j)]) for j in range(max_length)) + 1 <=
                                quicksum((j * x[str(k) + "_" + str(j)]) for j in range(max_length)),
                                name="write_after_write_" + str(i) + "_" + str(k))
            for k in self.data.block_dict[i].read_after_write:
                if k not in self.data.block_dict[i].write_after_write:
                    model.addConstr(quicksum((j * x[str(i) + "_" + str(j)]) for j in range(max_length)) + 1 <=
                                    quicksum((j * x[str(k) + "_" + str(j)]) for j in range(max_length)),
                                    name="read_after_write_" + str(i) + "_" + str(k))
        
        sum_of_each_process_hash_in_each_level = {}
        for j in range(max_length):
            sum_of_each_process_hash_in_each_level[j] = {}
            for key, value in self.data.process_hash.items():
                # 每一级中，每一执行流程的HASH资源使用之和：Int
                sum_of_each_process_hash_in_each_level[j][key] = model.addVar(lb=0, ub=2, vtype=GRB.INTEGER, name="sum_of_process_"+str(key)+"_hash_in_each_level" + str(j),
                                                     obj=0, column=None)
                # 令变量等于每一级中，每一执行流程的HASH资源使用之和
                model.addConstr(sum_of_each_process_hash_in_each_level[j][key] ==
                                quicksum((self.data.block_dict[i].hash * x[str(i) + "_" + str(j)]) for i in value),
                                name="sum_of_process_"+str(key)+"_hash_in_each_level" + str(j)+"_equal_to_val")
                # 每一级中，每一执行流程的HASH资源使用之和小于等于2
                model.addConstr(sum_of_each_process_hash_in_each_level[j][key] <= 2,
                                name="hash_of_process_" + str(key) + "_in_" + str(j))
            # 每一级中，每一执行流程的ALU资源使用之和小于等于56
            for key, value in self.data.process_alu.items():
                model.addConstr(quicksum((self.data.block_dict[i].alu * x[str(i) + "_" + str(j)]) for i in
                                         value) <= 56,
                                name="alu_of_process_" + str(key) + "_in_" + str(j))
        # 各级中执行流程HASH资源使用最大值
        max_hash_in_each_level = {}
        for j in range(16):
            # 添加变量，利用GenConstrMax约束取行流程HASH资源使用最大值
            max_hash_in_each_level[j] = model.addVar(lb=0, ub=2, vtype=GRB.INTEGER, name="max_hash_in_level_" + str(j),
                                                     obj=0, column=None)
            max_hash_in_each_level[j + 16] = model.addVar(lb=0, ub=2, vtype=GRB.INTEGER,
                                                          name="max_hash_in_level_" + str(j + 16),
                                                          obj=0, column=None)
            # 令max_hash_in_each_level[j] 为j级中执行流程HASH资源使用最大值
            model.addGenConstrMax(max_hash_in_each_level[j],
                                  [sum_of_each_process_hash_in_each_level[j][key]
                                   for key in sum_of_each_process_hash_in_each_level[j]],
                                  0,
                                  name='max_hash_in_level_' + str(j))
            model.addGenConstrMax(max_hash_in_each_level[j + 16],
                                  [sum_of_each_process_hash_in_each_level[j + 16][key]
                                   for key in sum_of_each_process_hash_in_each_level[j + 16]],
                                  0,
                                  name='max_hash_in_level_' + str(j + 16))
            # 折叠级两级各自执行流程HASH资源使用最大值之和小于3
            model.addConstr(max_hash_in_each_level[j] + max_hash_in_each_level[j + 16] <= 3,
                            name="max_hash_in_fold_level_" + str(j))
        # objective
        f = quicksum(value for key, value in y.items())
        model.setObjective(f, GRB.MINIMIZE)
        model.update()
        # setParam
        model.setParam(GRB.Param.Threads, 32)

        # 设置时间限制-1h
        model.Params.timelimit = 3600
        model.Params.LogToConsole = True
        model.optimize()
        model.write('model_2.lp')
        if model.status == GRB.Status.OPTIMAL:
            print("optimal")
            print("Optimal Objective Value", model.objVal)
            pass
        elif model.status == GRB.Status.INFEASIBLE:
            print("infeasible")
        self.output('output_problem_2.csv', x, y)
        pass

    def output(self, filepath, x, y):
        # 结果输出到csv
        with open(filepath, 'w', newline="") as outfile:
            csvWriter = csv.writer(outfile, delimiter=',')
            for j in range(max_length):
                output = []
                if y[j].x == 1:
                    output.append(j)

                    tcam = sum(self.data.block_dict[i].tcam * x[str(i) + "_" + str(j)].x for i in
                               range(len(self.data.block_dict)))
                    hash = sum(self.data.block_dict[i].hash * x[str(i) + "_" + str(j)].x for i in
                               range(len(self.data.block_dict)))
                    alu = sum(self.data.block_dict[i].alu * x[str(i) + "_" + str(j)].x for i in
                              range(len(self.data.block_dict)))
                    qualfy = sum(self.data.block_dict[i].qualfy * x[str(i) + "_" + str(j)].x for i in
                                 range(len(self.data.block_dict)))
                    output.append(tcam)
                    output.append(hash)
                    output.append(alu)
                    output.append(qualfy)
                    for i in range(len(self.data.block_dict)):
                        if x[str(i) + "_" + str(j)].x == 1:
                            output.append(i)

                    csvWriter.writerow(output)


if __name__ == "__main__":
    # 问题一
    s = simulator()
    s.static_algorithm_for_problem1()
    # 问题二
    s = simulator()
    s.static_algorithm_for_problem2()
