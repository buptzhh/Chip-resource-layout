
class Block:
    def __init__(self, id, tcam, hash, alu, qualfy):
        self.tcam = tcam
        self.hash = hash
        self.alu = alu
        self.qualfy = qualfy
        self.id = id
        self.read_after_write = set()   # 写后读
        self.write_after_read = set()   # 读后写
        self.write_after_write = set()  # 写后写
        self.control = set()            # 控制依赖
        self.read = set()
        self.write = set()
        self.successor = set()

    def set_read(self, read):
        self.read = read

    def set_write(self, write):
        self.write = write

    def set_successor(self, successor):
        self.successor = successor