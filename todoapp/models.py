from sqlalchemy import Table, Column, Integer, String, Boolean
from sqlalchemy.orm import mapper
from database import metadata, db_session

class Todo(object):
    query = db_session.query_property()

    def __init__(self, title, description=None, done=False):
        self.title = title
        self.description = description
        self.done = done

    def __repr__(self):
        return '<Todo %r>' % (self.title)

todo_table = Table('todo', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('title', String(50), unique=True),
                   Column('description', String(120)),
                   Column('done', Boolean)
                   )

mapper(Todo, todo_table)
