from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    passwords = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Done")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    passwords = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class AddForm(FlaskForm):
    name = StringField("Name of the game", validators=[DataRequired()])
    img_url = StringField("URL of the image", validators=[DataRequired()])
    price = StringField("Price", validators=[DataRequired()])
    submit = SubmitField("Submit")
