from __init__ import bcrypt, db
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from models import User

from routes.main.forms import (LoginForm, RegistrationForm, RequestResetForm,
                               ResetPasswordForm, UpdateAccountInfoForm)
from routes.main.utils import save_picture, send_reset_email

main = Blueprint("main", __name__)


@main.route("/", methods=["GET", "POST"])
def homepage():
    return render_template("homepage.html")


@main.route("/your_tasks", methods=["GET", "POST"])
def homepage():
    return render_template("your_tasks.html")


@main.route("/task_stats", methods=["GET", "POST"])
def homepage():
    return render_template("task_stats.html")


@main.route("/leaderboards", methods=["GET", "POST"])
def homepage():
    return render_template("leaderboards.html")


@main.route("/search/@/<username>", methods=["GET", "POST"])
def homepage(username: str = ""):
    return render_template("search.html")


@main.route("/account/@/<username>", methods=["GET", "POST"])
def homepage(username: str = ""):
    return render_template("user_account.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.homepage"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            db.session.remove()
            return (
                redirect(next_page) if next_page else redirect(
                    url_for("main.homepage"))
            )
        elif not user:
            flash("There is no account with that name", "warning")
        else:
            flash("Username and Password do not match", "warning")
    return render_template("login.html", title="Login", form=form)


@main.route("/logout", methods=["GET", "POST"])
def logout():
    if not current_user.is_authenticated:
        flash("You need to be logged in to view this page", "warning")
        return redirect(url_for("main.login"))
    logout_user()
    return redirect(url_for("main.homepage"))


@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.homepage"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data, email=form.email.data, password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        db.session.remove()
        user = User.query.filter_by(username=form.username.data).first()
        login_user(user)
        return redirect(url_for("main.login"))
    return render_template("register.html", title="Register", form=form)


@main.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@main.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        db.session.remove()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@main.route("/account", methods=["GET", "POST"])
def account():
    if not current_user.is_authenticated:
        flash("You need to be logged in to view this page", "warning")
        return redirect(url_for("main.login"))
    form = UpdateAccountInfoForm()
    refresh_flag = False
    if form.validate_on_submit():
        user = User.query.get(int(current_user.id))
        if form.picture.data:
            picture_file = save_picture(form.picture.data, locator=0)
            user.image_file = picture_file
            refresh_flag = True
        if (form.old_password.data or form.new_password.data or form.confirm_password.data):
            if form.new_password.data == form.confirm_password.data:
                hashed_password = bcrypt.generate_password_hash(
                    form.new_password.data).decode('utf-8')
                user.password = hashed_password
                refresh_flag = True
        if form.username.data != user.username:
            user.username = form.username.data
            refresh_flag = True
        if form.email.data != user.email:
            user.email = form.email.data
            refresh_flag = True
        if form.motto.data != user.motto:
            user.motto = form.motto.data
            refresh_flag = True
        if form.bio.data != user.bio:
            user.bio = form.bio.data
            refresh_flag = True
        if form.birthday.data != user.birthday:
            user.birthday = form.birthday.data
            refresh_flag = True
        if refresh_flag:
            db.session.commit()
            db.session.remove()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('main.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.motto.data = current_user.motto
        form.bio.data = current_user.bio
        form.birthday.data = current_user.birthday

    return render_template('account.html', title='Account Info', form=form)
