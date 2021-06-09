from urllib.parse import urlparse, urljoin
from flask import Flask, request, render_template, redirect, url_for, flash, abort
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user, UserMixin,
                         confirm_login, fresh_login_required)
from flask_wtf import FlaskForm as Form
from wtforms import BooleanField, StringField, validators
from passlib.apps import custom_app_context as pwd_context


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
    password = StringField('Password', [
        validators.Length(min=8, message=u"Password must be at least eight characters."),
        validators.InputRequired(u"Forget password?")])
    remember = BooleanField('Remember me')

class RegisterForm(Form):
    username = StringField('Username', [
        validators.Length(min=2, max=25, message=u"Huh, little too short for a username."),
        validators.InputRequired(u"Forget username?")])
    password = StringField('Password', [
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
    return USERS[int(user_id)]


@app.route('/')
@app.route('/index')
def home():
	return render_template('index.html')

@app.route('/listdata')
def listeverything():

	req = request.args

	returnType = req.get("returnType", type=str)
	dataType = req.get("dataType", type=str)
	topVals = req.get("quantity", default = -1, type=int)
	
	r = requests.get(f'http://restapi:5000/{returnType}/{dataType}?top={topVals}')

	return r.text

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit() and request.method == "POST" and "username" and "password" in request.form:
        username = request.form["username"]
        password = request.form["password"]
        hashedPass = pwd_context.encrypt(password)
        r = requests.get(f'http://restapi:5000/login/?user={username}&hashedPass={hashedPass}')
        
        if #r success:
            remember = request.form.get("remember", "false") == "true"
            if login_user(USER_NAMES[username], remember=remember):
                flash("Logged in!")
                flash("I'll remember you") if remember else None
                next = request.args.get("next")
                if not is_safe_url(next):
                    abort(400)
                return redirect(next or url_for('index'))
            else:
                flash("Sorry, but you could not log in.")
        else:
            flash(u"Invalid username.")
    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def login():
    form = RegisterForm()
    if form.validate_on_submit() and request.method == "POST" and "username" and "password" in request.form:
        username = request.form["username"]
        password = request.form["password"]
        hashedPass = pwd_context.encrypt(password)
        r = requests.get(f'http://restapi:5000/register/?user={username}&hashedPass={hashedPass}')

        if #r success:
            remember = request.form.get("remember", "false") == "true"
            if login_user(USER_NAMES[username], remember=remember):
                flash("Logged in!")
                flash("I'll remember you") if remember else None
                next = request.args.get("next")
                if not is_safe_url(next):
                    abort(400)
                return redirect(next or url_for('index'))
            else:
                flash("Sorry, but you could not log in.")
        else:
            flash(u"Invalid username.")
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("index"))


if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)
