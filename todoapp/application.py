# -*- coding: utf-8 -*-
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
	test = ["test", "finish"]
	return render_template("index.html", items=test)


@app.route('/todo/', methods=['GET', 'POST'])
def todo():
	if request.method == "POST":
		Todo(title=request.form["todo"], notes=request.form["notes"], done=request.form["done"])

		return "True"
	else:
		return render_template("todo.html")

if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0')