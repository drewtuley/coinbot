from sqlalchemy import Column, Integer, String
from sqlalchemy import Sequence
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(10))
    fullname = Column(String)
    password = Column(String)

    def parse(self, injson):
        self.name = injson['name']
        self.fullname = injson['fullname']
        self.password = injson['password']

    def __repr__(self):
        return "<User(name='%s', fullname='%s', password='%s')>" % (
            self.name, self.fullname, self.password)


print(User.__table__)
engine = create_engine('sqlite:///alchemy.db', echo=True)
print(engine)


Base.metadata.create_all(engine)

ed_user = User(name='ed', fullname='Ed Jones', password='edspassword')

print(ed_user)

Session = sessionmaker(bind=engine)
session = Session()
session.add(ed_user)

our_user = session.query(User).filter_by(name='ed').first()  # doctest:+NORMALIZE_WHITESPACE
print(our_user)

session.add_all([
    User(name='wendy', fullname='Wendy Williams', password='foobar'),
    User(name='mary', fullname='Mary Contrary', password='xxg527'),
    User(name='fred', fullname='Fred Flinstone', password='blah')]
)

ed_user.password = 'f8s7ccs'

print(session.dirty)
print(session.new)

session.commit()

print(ed_user.id)

for instance in session.query(User).order_by(User.id):
    print(instance.name, instance.fullname)

for name, fullname, id in session.query(User.name, User.fullname, User.id):
    print(name, fullname)

for row in session.query(User, User.name).all():
    print(row.User, row.name)

nm = {'name': 'drew', 'fullname': 'Andrew', 'password': 'wibble'}
drew = User()
drew.parse(nm)
print(drew)
session.add(drew)
session.commit()

for row in session.query(User, User.name).all():
    print(row.User, row.name)
