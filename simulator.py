from data import Data
from gurobipy import *
import numpy as np
import csv

max_length = 100


class simulator:
    def __init__(self):
        self.data = Data()
        # print(self.data.block_dict)


    def static_algorithm_for_problem1(self):
        model = Model()
        y = {}
        for j in range(max_length):
            y[j] = model.addVar(lb=0, ub=1, vtype=GRB.BINARY, name="package_" + str(j), obj=0, column=None)
        for j in range(1, max_length):
            model.addConstr(y[j-1] >= y[j], name='c_pre_'+str(j))
        x = {}
        for i in range(len(self.data.block_dict)):
            for j in range(max_length):
                x[str(i) + "_" + str(j)] = model.addVar(lb=0, ub=1, vtype=GRB.BINARY, name="x_" + str(i) + "_" + str(j),
                                                        obj=0, column=None)

        # 块被使用了
        for j in range(max_length):
            model.addConstr(
                y[j] * GRB.MAXINT >= quicksum(x[str(i) + "_" + str(j)] for i in range(len(self.data.block_dict))),
                name="y_01_" + str(j))
            model.addConstr(quicksum(x[str(i) + "_" + str(j)] for i in range(len(self.data.block_dict))) * GRB.MAXINT>= y[j],
                name="y_10_" + str(j))
        # 基本块必须被放置
        for i in range(len(self.data.block_dict)):
            model.addConstr(quicksum(x[str(i) + "_" + str(j)] for j in range(max_length)) == 1, name="x_sum_" + str(i))
        # resource constraint
        for j in range(max_length):
            model.addConstr(quicksum(
                (self.data.block_dict[i].tcam * x[str(i) + "_" + str(j)]) for i in range(len(self.data.block_dict))) <= 1,
                            name="tcam_of_" + str(j))
            model.addConstr(quicksum(
                (self.data.block_dict[i].hash * x[str(i) + "_" + str(j)]) for i in range(len(self.data.block_dict))) <= 2,
                            name="hash_of_" + str(j))
            model.addConstr(quicksum(
                (self.data.block_dict[i].alu * x[str(i) + "_" + str(j)]) for i in range(len(self.data.block_dict))) <= 56,
                            name="alu_of_" + str(j))
            model.addConstr(quicksum(
                (self.data.block_dict[i].qualfy * x[str(i) + "_" + str(j)]) for i in range(len(self.data.block_dict))) <= 64,
                            name="qualfy_of_" + str(j))

        for j in range(16):
            model.addConstr(quicksum(
                (self.data.block_dict[i].tcam * (x[str(i) + "_" + str(j)] + x[str(i) + "_" + str(j + 16)])) for i in
                range(len(self.data.block_dict))) <= 1,
                            name="tcam_of_fold_" + str(j))
            model.addConstr(quicksum(
                (self.data.block_dict[i].hash * (x[str(i) + "_" + str(j)] + x[str(i) + "_" + str(j + 16)])) for i in
                range(len(self.data.block_dict))) <= 3,
                            name="hash_of_fold_" + str(j))

        model.addConstr(quicksum(
            (self.data.block_dict[i].tcam * x[str(i) + "_" + str(j)]) for i in range(len(self.data.block_dict)) for j in
            range(max_length) if j % 2 == 0) <= 5,
                        name="tcam_on_even")

        # objective
        f = quicksum(value for key, value in y.items())
        model.setObjective(f, GRB.MINIMIZE)


        # setParam
        model.setParam(GRB.Param.Threads, 4)

        # model.Params.Method = 5
        model.Params.timelimit = 3600
        model.Params.LogToConsole = True
        model.optimize()
        model.write('model.lp')
        if model.status == GRB.Status.OPTIMAL:
            print("optimal")
            print("Optimal Objective Value", model.objVal)
            pass
        elif model.status == GRB.Status.INFEASIBLE:
            print("infeasible")
        self.output('output.csv', x, y)
        pass

    def output(self, filepath, x, y):
        with open(filepath,'w', newline="") as outfile:
            csvWriter = csv.writer(outfile, delimiter=',')
            for j in range(max_length):
                output = []
                if y[j].x == 1:
                    output.append(j)

                    tcam = sum(self.data.block_dict[i].tcam * x[str(i) + "_" + str(j)].x for i in range(len(self.data.block_dict)))
                    hash = sum(self.data.block_dict[i].hash * x[str(i) + "_" + str(j)].x for i in range(len(self.data.block_dict)))
                    alu = sum(self.data.block_dict[i].alu * x[str(i) + "_" + str(j)].x for i in range(len(self.data.block_dict)))
                    qualfy = sum(self.data.block_dict[i].qualfy * x[str(i) + "_" + str(j)].x for i in range(len(self.data.block_dict)))
                    output.append(tcam)
                    output.append(hash)
                    output.append(alu)
                    output.append(qualfy)
                    for i in range(len(self.data.block_dict)):
                        if x[str(i) + "_" + str(j)].x == 1:
                            output.append(i)

                    csvWriter.writerow(output)


if __name__ == "__main__":
    s = simulator()
    s.static_algorithm_for_problem1()
