# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from models import Todo
from database import db_session

app = Flask(__name__)

@app.route('/')
def index():
	todo_list = Todo.query.all()
	print todo_list
	return render_template("index.html", items=todo_list)


@app.route('/todo/', defaults={'todo_id': None}, methods=['GET', 'POST'])
@app.route('/todo/<todo_id>', methods=['GET', 'POST'])
def todo(todo_id):
	if request.method == "POST":
		title = request.form["todo"]
		notes = request.form["notes"]
		done = 0 if str(request.form["done"]) == 'false' else 1
		if todo_id is not None:
			todo = db_session.query(Todo).get(todo_id)
			todo.title = title
			todo.description = notes
			todo.done = done
		else:
			todo = Todo(title=title, description=notes, done=done)
		db_session.add(todo)
		db_session.commit()
		return "True"
	else:
		if todo_id is not None:
			todo = db_session.query(Todo).get(todo_id)
		else:
			todo = {"id": "", "title": "", "description": "", "done": 0}
		return render_template("todo.html", item=todo)

if __name__ == '__main__':
	from database import init_db
	init_db()

	app.debug = True
	app.run(host='0.0.0.0')