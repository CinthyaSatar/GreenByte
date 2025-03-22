from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from greenbyte.models import User
from flask_login import current_user

class RegistrationForm(FlaskForm):
    firstName = StringField('First Name', validators=[DataRequired(), Length(min=1,max=25)])
    lastName = StringField('Last Name', validators=[DataRequired(), Length(min=1,max=25)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirmPassword = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField('Register Account')

    def validateField(self,email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("This email is taken! Please try with another")
    
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    firstName = StringField('First Name', validators=[DataRequired(), Length(min=1,max=25)])
    lastName = StringField('Last Name', validators=[DataRequired(), Length(min=1,max=25)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    picture = FileField("Update account picture", validators=[FileAllowed(['jpg','png'])])
    submit = SubmitField('Update  Account')

    def validate_email(self,email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("This email is taken! Please try with another")
  
class requestResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validateField(self,email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("There is no account with that email! Please try with another")

class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    confirmPassword = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField('Rest Password')

