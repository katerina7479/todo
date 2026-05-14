# -*- coding: utf-8 -*-
from datetime import date, datetime
from flask import Flask, render_template, request
from models import Todo
from database import db_session


app = Flask(__name__)


def _sort_key(item):
    today = date.today()
    if item.due_date is not None and item.due_date < today:
        return (0, item.due_date)
    return (1, item.due_date or date.max)


@app.route('/')
def index():
    # List Page — overdue items sorted to top
    todo_list = sorted(Todo.query.all(), key=_sort_key)
    return render_template("index.html", items=todo_list, today=date.today())


@app.route('/todo/', defaults={'todo_id': None}, methods=['GET', 'POST'])
@app.route('/todo/<todo_id>', methods=['GET', 'POST'])
def todo(todo_id):
    # Detail Page
    if request.method == "POST":
        title = request.form["todo"]
        notes = request.form["notes"]
        done = False if str(request.form["done"]) == 'false' else True  # JS to python false
        due_date_str = request.form.get("due_date", "").strip()
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None
        if todo_id is not None: # Existing, get it
            todo = db_session.query(Todo).get(todo_id)
            todo.title = title
            todo.description = notes
            todo.done = done
            todo.due_date = due_date
        else: # It's new
            todo = Todo(title=title, description=notes, done=done, due_date=due_date)
            db_session.add(todo)
        db_session.commit()
        return "OK"
    else: # GET
        if todo_id is not None:
            todo = db_session.query(Todo).get(todo_id)
        else:
            todo = {"id": "", "title": "", "description": "", "done": 0, "due_date": None}
        return render_template("todo.html", item=todo)


if __name__ == '__main__':
    # Initialize Database
    from database import init_db
    init_db()

    # Start App
    app.debug = True
    app.run(host='0.0.0.0')
