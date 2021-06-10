from urllib.parse import urlparse, urljoin
from flask import Flask, request, render_template, redirect, url_for, flash, abort, session
from flask_login import (LoginManager, current_user, login_required,
						 login_user, logout_user, UserMixin,
						 confirm_login, fresh_login_required)
from flask_wtf import FlaskForm as Form
from wtforms import BooleanField, StringField, validators, PasswordField
from passlib.hash import sha256_crypt as pwd_context

import requests
import json

app = Flask(__name__)
app.secret_key = "and the cats in the cradle and the silver spoon"

app.config.from_object(__name__)

login_manager = LoginManager()

login_manager.session_protection = "strong"
login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."
login_manager.refresh_view = "login"
login_manager.needs_refresh_message = (
	u"To protect your account, please reauthenticate to access this page."
)
login_manager.needs_refresh_message_category = "info"

login_manager.init_app(app)



class LoginForm(Form):
	username = StringField('Username', [
		validators.Length(min=2, max=25, message=u"Username must be at least two characters."),
		validators.InputRequired(u"Forget username?")])
	password = PasswordField('Password', [
		validators.Length(min=8, message=u"Password must be at least eight characters."),
		validators.InputRequired(u"Forget password?")])
	remember = BooleanField('Remember me')

class RegisterForm(Form):
	username = StringField('Username', [
		validators.Length(min=2, max=25, message=u"Huh, little too short for a username."),
		validators.InputRequired(u"Forget username?")])
	password = PasswordField('Password', [
		validators.Length(min=8, message=u"Password must be at least eight characters."),
		validators.InputRequired(u"Forget password?")])


def is_safe_url(target):
	"""
	:source: https://github.com/fengsp/flask-snippets/blob/master/security/redirect_back.py
	"""
	ref_url = urlparse(request.host_url)
	test_url = urlparse(urljoin(request.host_url, target))
	return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


class User(UserMixin):
	def __init__(self, id, name, token):
		self.id = id
		self.name = name
		self.token = token

@login_manager.user_loader
def load_user(user_id):
	return User(user_id, session.get("name"), session.get("token"))


@app.route('/')
@app.route('/index')
def index():
	return render_template('index.html')


@app.route('/calculator')
@login_required
def calculator():
	return render_template('calculator.html')


@app.route('/listdata')
@login_required
def listdata():

	req = request.args

	returnType = req.get("returnType", type=str)
	dataType = req.get("dataType", type=str)
	topVals = req.get("quantity", default = -1, type=int)
	
	r = requests.get(f'http://restapi:5000/{returnType}/{dataType}?top={topVals}&token={session["token"]}')
	data = r.json()

	if r.status_code == 401:
		logout_user()
		return render_template("index.html", message=data["message"])
	else:
		return r.text
	


@app.route("/login", methods=["GET", "POST"])
def login():
	form = LoginForm()
	if form.validate_on_submit() and request.method == "POST" and "username" and "password" in request.form:
		username = request.form["username"]
		password = request.form["password"]
		hashedPass = pwd_context.using(salt = "Thisisaverylong").hash(password)
		r = requests.get(f'http://restapi:5000/token/?user={username}&hashedPass={hashedPass}')
		data = r.json()

		if r.status_code == 201:
			curUser = User(data["id"], username, data["token"])
			remember = request.form.get("remember", "false") == "true"
			session["token"] = data["token"]
			session["id"] = data["id"]
			session["name"] = username
			if login_user(curUser, remember=remember):
				flash("Logged in!")
				flash("I'll remember you") if remember else None
				next = request.args.get("next")
				if not is_safe_url(next):
					abort(400)
				return redirect(next or url_for('index'))
			else:
				flash("Sorry, but you could not log in.")
		else:
			flash(u"Failed to log in")
	return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
	form = RegisterForm()
	if form.validate_on_submit() and request.method == "POST" and "username" and "password" in request.form:
		username = request.form["username"]
		password = request.form["password"]
		hashedPass = pwd_context.using(salt = "Thisisaverylong").hash(password)
		r = requests.post(f'http://restapi:5000/register/?user={username}&hashedPass={hashedPass}')

		if r.status_code == 201:
			flash("Successfully registered")
			redirect(url_for("login"))
		elif r.status_code == 400:
			flash("Failed to register, username already in use.")
	return render_template("register.html", form=form)


@app.route("/logout")
@login_required
def logout():
	logout_user()
	flash("Logged out.")
	return redirect(url_for("index"))


if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)
