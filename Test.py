class Test1:
    def __init__(self):
        self.a = None
        print('init1')

    def parse(self, xx):
        self.a = xx['a']


class Test2(Test1):
    def __init__(self):
        Test1.__init__(self)
        self.b = None

    def parse(self, yy):
        Test1.parse(self, yy)
        self.b = yy['b']


if __name__ == "__main__":
    t1 = Test1()
    t1.parse({'a': 12})
    print('a={}'.format(t1.a))

    t2 = Test2()
    t2.parse({'a': 13, 'b': 23})
    print('a={}'.format(t2.a))
    print('b={}'.format(t2.b))
