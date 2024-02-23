from __future__ import annotations
from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request, g
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, exc, ForeignKey
from functools import wraps
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from typing import List
import os

# Import your forms from the forms.py
from forms import CreatePostForm, RegisterFrom, LoginForm, CommentForm

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''
login_manager = LoginManager()
app = Flask(__name__)
# app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config["SECRET_KEY"] = os.environ.get("FLASK_KEY")
ckeditor = CKEditor(app)
Bootstrap5(app)

# TODO: Configure Flask-Login
# CREATE DATABASE
class Base(DeclarativeBase):
    pass
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)
login_manager.init_app(app)

class UserNotFoundError(Exception):
    pass

@login_manager.user_loader
def load_user(user_id):
    # return None
    return db.get_or_404(Db_users, user_id)
 
gravatar = Gravatar(
    app,
    size=100,
    rating='g',
    default='retro',
    force_default=False,
    force_lower=False,
    use_ssl=False,
    base_url=None
)

# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("Users.id"))
    author = relationship("Db_users", back_populates="posts")
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comment = relationship("Comment", back_populates="parent_post")
    


# TODO: Create a User table for all your registered users. 
class Db_users(db.Model, UserMixin):
    __tablename__ ="Users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=False, nullable=False)
    username: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), unique=False, nullable=False)
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="user")


class Comment(db.Model):
    __tablename__ = "Comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable= False)
    user_id : Mapped[int] = mapped_column(Integer, ForeignKey("Users.id"))
    user = relationship("Db_users", back_populates="comments")
    blog_id : Mapped[int] = mapped_column(Integer, ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comment")

with app.app_context():
    db.create_all()


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterFrom()
    if form.validate_on_submit():
        password = form.password.data
        hash = generate_password_hash(
            password=password,
            method="pbkdf2:sha256",
            salt_length=16
        )
        print(hash)
        try:
            new_user = Db_users(
                name = form.name.data,
                username = form.email.data,
                password = hash

            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("get_all_posts"))
        except exc.IntegrityError:
            flash("User already exist. Login instead")
            return redirect(url_for('login'))
    return render_template("register.html", form=form, current_user=current_user)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            username = form.username.data
            db_data = db.session.execute(
                db.select(Db_users).where(Db_users.username==username)
            ).scalar()
            can_proceed = check_password_hash(pwhash=db_data.password, password=form.password.data)
            if can_proceed:
                print(can_proceed)
                print(db_data.password)
                login_user(username, remember=False)
                return redirect(url_for("get_all_posts"))
            else:
                flash("The passwords does not match, please try again")
        except AttributeError:
            flash("The username does not exist")
            return redirect(url_for("register"))
    return render_template("login.html", form=form, current_user=current_user )


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/', methods=["GET", "POST"])
def get_all_posts():
    try:
        if current_user.is_authenticated:
            user_id = current_user.id
            result = db.session.execute(db.select(BlogPost))
            posts = result.scalars().all()
            return render_template("index.html", all_posts=posts, current_user=current_user, user_id=user_id)
        else:
            result = db.session.execute(db.select(BlogPost))
            posts = result.scalars().all()
            return render_template("index.html", all_posts=posts, current_user=current_user)
    except NotImplementedError or AttributeError:
        result = db.session.execute(db.select(BlogPost))
        posts = result.scalars().all()
        return render_template("index.html", all_posts=posts, current_user=current_user)
    else:
        result = db.session.execute(db.select(BlogPost))
        posts = result.scalars().all()
        return render_template("index.html", all_posts=posts, current_user=current_user, user_id=user_id)
# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>", methods=["POST", "GET"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm() 
    post_comments = db.session.execute(
                db.select(Comment).where(Comment.blog_id == post_id)
                ).scalars().all()
    if current_user.is_authenticated:
        if comment_form.validate_on_submit():
            comment = Comment(
                text = comment_form.comment.data,
                user_id = current_user.id,
                blog_id = post_id
            )
            db.session.add(comment)
            db.session.commit()
            
            return render_template("post.html", post=requested_post, form=comment_form, comments=post_comments, post_id=post_id, gravatar=gravatar)

    return render_template("post.html", post=requested_post, form=comment_form, current_user=current_user, comments=post_comments, gravatar=gravatar)


def admin_only(function):
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        user_id = current_user.id
        if user_id != 1:
            print(current_user.id)
            return abort(403)
        return function(*args, **kwargs)
    return wrapper_function

# TODO: Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm() 
    if form.validate_on_submit():
        user_id = db.session.execute(
            db.select(Db_users).where(Db_users.id == current_user.id)
        ).scalar().id
        print(current_user.is_authenticated)
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=date.today().strftime("%B %d, %Y"),
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user                                                             
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=False , port=5002)
