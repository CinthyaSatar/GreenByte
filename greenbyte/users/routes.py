from flask import Blueprint
from flask import  render_template, flash, redirect, url_for, request
from greenbyte.models import User, Post
from greenbyte.users.forms import (
    RegistrationForm,
    LoginForm,
    UpdateAccountForm,
    RequestResetForm,  # Changed from requestResetForm
    ResetPasswordForm
)
from greenbyte import bcrypt, db
from flask_login import login_user, current_user, logout_user, login_required
from greenbyte.users.utils import savePicture, sendResetEmail



users = Blueprint('users', __name__)

@users.route("/register", methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashedPassword = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username = form.username.data,
            firstName = form.firstName.data,
            lastName = form.lastName.data,
            email = form.email.data,
            password = hashedPassword
        )
        db.session.add(user)
        db.session.commit()

        flash(f'Account created for {form.firstName.data}! You can now login', 'success')
        return redirect(url_for('users.login'))
    return render_template("register.html", form=form)

@users.route("/login", methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            nextPage = request.args.get('next')
            flash("You have been logged in", "success")
            return redirect(nextPage) if nextPage else redirect(url_for('main.index'))
        else:
            flash("Login Failed. Please check email and password", "danger")
    return render_template("login.html", form=form)

@users.route("/logout ", methods=['GET','POST'])
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@users.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            pictureFile = savePicture(form.picture.data)
            current_user.image_file = pictureFile

        current_user.username = form.username.data
        current_user.firstName = form.firstName.data
        current_user.lastName = form.lastName.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Account has been updated!", "success")
        return redirect(url_for("users.account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.firstName.data = current_user.firstName
        form.lastName.data = current_user.lastName
        form.email.data = current_user.email

    imageFile = url_for('static', filename='profilePics/'+current_user.image_file)
    return render_template("account.html", imageFile=imageFile, form=form)

@users.route("/user/<string:username>")
def page_user(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template("page_user.html", posts=posts, user=user)

@users.route("/resetPassword", methods=['GET', 'POST'])
def resetRequest():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RequestResetForm()  # Changed from requestResetForm
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        sendResetEmail(user)
        flash("Email has been sent with instruction to reset your password", "info")
        return redirect(url_for('main.index'))

    return render_template("resetRequest.html", form=form)

@users.route("/resetPassword/<token>", methods=['GET', 'POST'])
def resetToken(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    user = User.verify_reset_token(token)
    if user is None:
        flash("That is an invalid or expired token", "warning")
        return redirect(url_for("resetRequest"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashedPassword = bcrypt. generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashedPassword
        db.session.commit()

        flash(f'Your password has been updated {user.firstName}! You can now login', 'success')
        return redirect(url_for('main.login'))
    return render_template("resetToken.html", form=form)
