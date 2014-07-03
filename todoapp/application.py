# -*- coding: utf-8 -*-
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
	test = ["test", "finish"]
	return {"items": test}

@app.route('/todo')
def todo():
	return "details"

if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0')