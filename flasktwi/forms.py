from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flasktwi.models import User
from flask_login import current_user
from flask_wtf.file import FileField, FileAllowed

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min = 3, max = 20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('password')])
    confirm_password = PasswordField('Confirm password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is allready taken')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is allready exist')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Confirm password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min = 3, max = 20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    about = StringField('About me')
    avatar = FileField('Update profile picture', validators=[FileAllowed(['jpg', 'png', 'gif'])])
    profile_background = FileField('Update profile background', validators=[FileAllowed(['jpg', 'png', 'gif'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is allready taken')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('This email is allready exist')

class PostForm(FlaskForm):
    post_image = FileField('Upload image (jpg, png, gif)', validators=[FileAllowed(['jpg', 'png', 'gif'])])
    title = StringField('Title', validators=[DataRequired(), Length(min = 1, max = 50)])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min = 1, max = 500)])
    submit = SubmitField('Post')

class ReplyForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired(), Length(min = 1, max = 500)])
    submit = SubmitField('Post')