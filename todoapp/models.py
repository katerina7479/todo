from sqlalchemy import Table, Column, Integer, String, Date
from sqlalchemy.orm import mapper
from sqlalchemy.dialects.sqlite.base import BOOLEAN
from database import metadata, db_session

class Todo(object):
    query = db_session.query_property()

    def __init__(self, title, description=None, done=False, due_date=None):
        self.title = title
        self.description = description
        self.done = done
        self.due_date = due_date

    def __repr__(self):
        return '<Todo %r>' % (self.title)

todo_table = Table('todo', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('title', String(50), unique=True),
                   Column('description', String(120)),
                   Column('done', BOOLEAN),
                   Column('due_date', Date, nullable=True)
                   )

mapper(Todo, todo_table)
