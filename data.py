import numpy as np
from block import Block


class Data:
    def __init__(self):
        self.block_dict = self.read_data('data/attachment1.csv')
        self.read_read_and_write('data/attachment2.csv')
        self.read_successor('data/attachment3.csv')
        # print(self.block_dict)

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
