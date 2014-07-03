Todo
======================

With Flask, SqlAlchemy, Semantic-UI
-----------------------------------

This is a demo site showing one way to use Flask to make a website.
I used a SqlAlchemy non-declarative model, and simple sqlite test db.
Semantic-UI for the front-end CSS
HTML rendered server-side with the Jinja2 template engine.
Vagrant upload, you can start the website starts with:

`> vagrant up
 ? (enter password at prompt)
 > vagrant ssh
 > cd projects/todoapp
 > python application.py
`
** Requires Virtualbox, Vagrant, & Git **


References at:
 
 * [Flask](http://flask.pocoo.org/docs/)
 * [Sqlalchemy in Flask](http://flask.pocoo.org/docs/patterns/sqlalchemy/#manual-object-relational-mapping)
 * [Jinja2](http://jinja.pocoo.org/docs/templates/)
 * [Semantic-ui](http://semantic-ui.com/element.html)
 * [Vagrant](https://docs.vagrantup.com/v2/)