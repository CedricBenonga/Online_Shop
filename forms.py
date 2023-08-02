from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm
class CreatePostForm(FlaskForm):
    name = StringField("Article name", validators=[DataRequired()])
    description = CKEditorField("Article Description", validators=[DataRequired()])
    img_url1 = StringField("Article Image URL1", validators=[DataRequired(), URL()])
    img_url2 = StringField("Article Image URL2", validators=[DataRequired(), URL()])
    img_url3 = StringField("Article Image URL3", validators=[DataRequired(), URL()])
    article_price = IntegerField("Article Price", validators=[DataRequired()])
    type = StringField("Article Type", validators=[DataRequired()])
    available = StringField("Available", validators=[DataRequired()])
    submit = SubmitField("Submit")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Up")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")
