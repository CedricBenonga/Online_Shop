from functools import wraps
import sqlalchemy
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5

''' if Bootstrap5 gives red, please run these two lines of code to the terminal:
    - pip uninstall flask-bootstrap bootstrap-flask
    - pip install bootstrap-flask
And, in the interpreter under settings, uninstall both then install bootstrap-flask '''

from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm
from flask_ckeditor import CKEditor

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)

# Connecting to DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Creating users Table
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    user_articles = relationship("UserArticle", back_populates="user_article")
    posts = relationship("ArticlePost", back_populates="user")


with app.app_context():
    db.create_all()


# Creating article Table
class ArticlePost(db.Model):
    __tablename__ = "articles"
    id = db.Column(db.Integer, unique=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text(250), nullable=False)
    img_url1 = db.Column(db.String(250), nullable=False)
    img_url2 = db.Column(db.String(250), nullable=False)
    img_url3 = db.Column(db.String(250), nullable=False)
    article_price = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(250), nullable=False)
    available = db.Column(db.String(250), nullable=False)
    # ***************Parent Relationship*************#
    user_articles = relationship("UserArticle", back_populates="parent_post")
    user = relationship("User", back_populates="posts")


with app.app_context():
    db.create_all()


# Creating user article Table
class UserArticle(db.Model):
    __tablename__ = "user_articles"
    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    img_url1 = db.Column(db.String(250), nullable=False)
    img_url2 = db.Column(db.String(250), nullable=False)
    img_url3 = db.Column(db.String(250), nullable=False)
    article_price = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(250), nullable=False)
    available = db.Column(db.String(250), nullable=False)
    # Creating a relational database
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # To get this line successfully, the User class must be
    # on top of the TaskPost class as the DB is created from the top lines going down. So if the TaskPost comes first,
    # it will crush as the ForeignKey("user.id") won't be found bcz it's not yet created.

    # ***************Child Relationship*************#
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id"))
    parent_post = relationship("ArticlePost", back_populates="user_articles")
    user_article = relationship("User", back_populates="user_articles")


with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)


# Creating "registered only" decorator, restriction for none-registered users.
def registered_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If user did not log in, forbid the access
        if not current_user.is_authenticated:
            return render_template("forbidden.html")
        # Else continue with the route function
        return f(*args, **kwargs)

    return decorated_function


# Creating "admin-only" decorator to make some routes or url(s) only accessible by the admin
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return render_template("forbidden.html")
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Formatting price to only up to the first two digits after coma without rounding the number
def format_to_2_decimal(num):
    return int(num*100)/100.00


# Home page
@app.route('/')
def get_all_posts():
    posts = ArticlePost.query.all()
    articles = UserArticle.query.all()
    art_nbr = 0
    if len(articles) > 0:
        for article in articles:
            if current_user.is_authenticated and article.user_id == current_user.id:
                art_nbr += int(article.quantity)

    return render_template("index.html", all_posts=posts, art_nbr=art_nbr)


# User registration
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit() and request.method == "POST":

        # Checking if the user already exists
        if User.query.filter_by(email=request.form.get('email')).first():
            flash("It looks like you're already one of us, please login instead!")  # to see this message,
            # you need to add some lines of code in the login.htl right on top of the form (in the same div).
            return redirect(url_for('login'))

        # Hashing and salting (encrypting) the password
        hashed_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )

        # Adding new user
        new_user = User(
            email=request.form.get('email'),
            name=request.form.get('name'),
            password=hashed_and_salted_password
        )

        # Saving the new user in the database
        db.session.add(new_user)
        db.session.commit()
        # Login and authenticate user after adding details to database.
        login_user(new_user)

        return redirect(url_for("get_all_posts", name=new_user.name))
    return render_template("register.html", form=form)


# User login
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit() and request.method == "POST":

        # Get data entered by the user
        email = request.form.get('email')  # or form.email.data
        password = request.form.get('password')  # or form.password.data

        # Find user in the DB by using the email entered.
        user = User.query.filter_by(email=email).first()

        # If email doesn't exist
        if not user:
            flash("This email does not exist, please try again.")
            return redirect(url_for('login'))

        # If password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))

        # If email exists in the DB and password correct, authorize access.
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))

    return render_template("login.html", form=form)


# User logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


# Article details
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = ArticlePost.query.get(post_id)
    return render_template("post.html", post=requested_post, current_user=current_user)


# Admin adding new article
@app.route("/new-post", methods=['GET', 'POST'])
@admin_only  # This decorator checks if the user is the admin or not
def add_new_post():
    try:  # this checks if the user is duplicating a post or nor
        form = CreatePostForm()
        if form.validate_on_submit():
            new_post = ArticlePost(
                name=form.name.data,
                description=form.description.data,
                img_url1=form.img_url1.data,
                img_url2=form.img_url2.data,
                img_url3=form.img_url3.data,
                article_price=form.article_price.data,
                type=form.type.data,
                available=form.available.data
            )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for("get_all_posts"))
    except sqlalchemy.exc.IntegrityError:
        db.session.rollback()
        return render_template("duplicate.html")
    return render_template("make-post.html", form=form)


# Admin editing article
@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
@admin_only  # This decorator checks if the user is the admin or not
def edit_post(post_id):
    post = ArticlePost.query.get(post_id)
    edit_form = CreatePostForm(
        name=post.name,
        description=post.description,
        img_url1=post.img_url1,
        img_url2=post.img_url2,
        img_url3=post.img_url3,
        article_price=post.article_price,
        type=post.type,
        available=post.available
    )
    if edit_form.validate_on_submit():
        post.name = edit_form.name.data
        post.description = edit_form.description.data
        post.img_url1 = edit_form.img_url1.data
        post.img_url2 = edit_form.img_url2.data
        post.img_url3 = edit_form.img_url3.data
        post.article_price = edit_form.article_price.data
        post.type = edit_form.type.data
        post.available = edit_form.available.data

        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form)


# Admin deleting article
@app.route("/delete/<int:post_id>")
@admin_only  # This decorator checks if the user is the admin or not
def delete_post(post_id):
    post_to_delete = ArticlePost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return render_template("success.html", post=post_to_delete)


# Delete confirmation
@app.route("/confirmation/<int:post_id>")
def confirm_delete(post_id):
    post_to_delete = ArticlePost.query.get(post_id)
    return render_template("confirm_delete.html", post=post_to_delete)


# Search for an article
@app.route("/search", methods=["POST", "GET"])
def search():
    if request.method == 'POST':
        searched_article = request.form["search"]  # Or searched_article = request.args.get('search')
        all_articles = ArticlePost.query.all()
        list_searched_article = []
        for article in all_articles:
            if searched_article.lower() in article.name.lower() or searched_article.lower() in article.type.lower():
                list_searched_article.append(article)
        return render_template("index.html", all_posts=list_searched_article)


# Adding to cart or increase article quantity in the cart
@app.route("/add_to_cart/<int:post_id>")
def add_to_cart(post_id):
    articles = UserArticle.query.all()
    selected_article = ArticlePost.query.get(post_id)

    if not current_user.is_authenticated:
        flash('Please login first.')
        return redirect(url_for('login'))

    try:
        if selected_article not in articles:
            new_post = UserArticle(
                name=selected_article.name,
                quantity=1,
                img_url1=selected_article.img_url1,
                img_url2=selected_article.img_url2,
                img_url3=selected_article.img_url3,
                article_price=selected_article.article_price,
                type=selected_article.type,
                available=selected_article.available,
                user_id=current_user.id
            )

            db.session.add(new_post)
            db.session.commit()

    except AttributeError:

        for article in articles:
            if article.user_id == current_user.id:
                article.article_price += article.article_price / article.quantity
                article.article_price = float(format_to_2_decimal(article.article_price))
                article.quantity += 1
                db.session.commit()

    return redirect(url_for('get_all_posts'))


# Reduce article quantity in the cart
@app.route("/reduce/<int:post_id>")
def reduce(post_id):
    selected_article = UserArticle.query.get(post_id)

    if selected_article.user_id == current_user.id:
        selected_article.quantity = int(selected_article.quantity)
        if selected_article.quantity > 1:
            selected_article.article_price -= int(selected_article.article_price) / int(selected_article.quantity)
            selected_article.article_price = (format_to_2_decimal(selected_article.article_price))
            selected_article.quantity -= 1
            db.session.commit()
        if int(selected_article.quantity) <= 1:
            selected_article.quantity = 1
            selected_article.article_price = selected_article.article_price
            db.session.commit()

    return redirect(url_for('cart'))


# Display articles and total price in the cart
@app.route("/cart")
def cart():
    articles = UserArticle.query.all()
    total_due = 0
    art_nbr = 0
    for article in articles:

        if not current_user.is_authenticated:
            flash('Please login first.')
            return redirect(url_for('login'))
        if article.user_id == current_user.id:
            art_nbr += int(article.quantity)
            total_due += article.article_price
            total_due = format_to_2_decimal(total_due)
    return render_template("cart.html", all_posts=articles, total_due=total_due, art_nbr=art_nbr)


# Remove article from the cart
@app.route("/remove/<int:post_id>")
def remove(post_id):
    article_to_remove = UserArticle.query.get(post_id)
    db.session.delete(article_to_remove)
    db.session.commit()

    posts = UserArticle.query.all()
    user_posts = []

    try:
        for post in posts:
            if post.user_id == current_user.id:
                user_posts.append(post)
    except AttributeError:
        pass

    return render_template("cart.html", all_posts=user_posts)


# Checkout section
# https://developers.payfast.co.za/docs#step_1_form_fields  # Link for PayFast
@app.route("/checkout")
def checkout():
    # Telling the user that this item is no longer available => to be added.
    articles = UserArticle.query.all()
    total_due = 0
    for article in articles:
        if article.user_id == current_user.id:
            total_due += article.article_price
            total_due = format_to_2_decimal(total_due)
    return render_template("payment.html", total_due=total_due - 0.01)
# https://developers.payfast.co.za/docs#step_1_form_fields  # Link for PayFast


if __name__ == "__main__":
    app.run(debug=True)
