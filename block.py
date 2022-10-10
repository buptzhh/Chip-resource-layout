
class Block:
    def __init__(self, id, tcam, hash, alu, qualfy):
        self.tcam = tcam
        self.hash = hash
        self.alu = alu
        self.qualfy = qualfy
        self.id = id
        self.read_after_write = set()   # 写后读,小于
        self.write_after_write = set()  # 写后写，小于
        self.write_after_read = set()   # 读后写，小于等于
        self.control = set()            # 控制依赖,小于等于

        self.less = set()
        self.less_equal = set()

        self.read = set()
        self.write = set()
        self.successor = set()

    def set_read(self, read):
        self.read = read

    def set_write(self, write):
        self.write = write

    def set_successor(self, successor):
        self.successor = successor

    def gen_less(self):
        for i in self.read_after_write:
            self.less.add(i)
        for i in self.write_after_write:
            self.less.add(i)
        for i in self.write_after_read:
            if i not in self.less:
                self.less_equal.add(i)
        for i in self.control:
            if i not in self.less:
                self.less_equal.add(i)