from .db_session import SqlAlchemyBase
import sqlalchemy
import datetime
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    uid = sqlalchemy.Column(sqlalchemy.Text, unique=True)
    nickname = sqlalchemy.Column(sqlalchemy.Text, unique=True)
    clicks = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    modificator = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('modificators.id'),default=0)

    modificators = orm.relation("Modificators")

