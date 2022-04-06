from .db_session import SqlAlchemyBase
import sqlalchemy
import datetime
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash


class User(SqlAlchemyBase):
    __tablename__ = 'modificators'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.Text, unique=True)
    multiplier = sqlalchemy.Column(sqlalchemy.Integer, default=1)
    duration = sqlalchemy.Column(sqlalchemy.Integer, default=1)

    #jobs = orm.relation("Jobs", back_populates="user")
