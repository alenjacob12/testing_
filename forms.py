from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# TODO: Create a RegisterForm to register new users
class RegisterFrom(FlaskForm):
    name = StringField("Enter your name", validators=[DataRequired()])
    email = StringField("Enter your Email", validators=[DataRequired()])
    password = StringField("Enter your Password", validators=[DataRequired()])
    submit = SubmitField("Register")

# TODO: Create a LoginForm to login existing users
class LoginForm(FlaskForm):
    username = StringField("Enter your Username", validators=[DataRequired()])
    password = StringField("Enter your password", validators=[DataRequired()]) 
    submit = SubmitField("Log in")

# TODO: Create a CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    comment = CKEditorField("Comment ", validators=[DataRequired()])
    submit = SubmitField("Submit")
