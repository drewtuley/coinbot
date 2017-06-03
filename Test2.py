class Cl:
    def __init__(self):
        self.x = None

    def setx(self, xv):
        self.x = xv

    def __repr__(self):
        return str(self.x)

    def __eq__(self, other):
        return self.x == other.x

if __name__ == '__main__':
    c = Cl()
    c.setx(10)

    c1 = c

    c = Cl()
    c.setx(10)

    if c1 == c:
        print(c)
    else:
        print ('c={}, c1={}'.format(c, c1))
