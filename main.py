from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, logout_user, login_required, current_user, LoginManager
from sqlalchemy.orm import relationship
from forms import RegisterForm, LoginForm, AddForm
import stripe
import os
from functools import wraps
from flask import abort


app = Flask(__name__)

bootstrap = Bootstrap5(app)
stripe.api_key = os.environ.get("API_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///commerce.db"
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(150), nullable=False)


class Games(db.Model):
    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(100), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    cart = relationship("Cart", back_populates="games")


class Cart(db.Model):
    __tablename__ = "cart"
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"))
    games = relationship("Games", back_populates="cart")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(100), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def home():
    all_games = Games.query.all()
    return render_template("index.html", games=all_games)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        user = User()
        user.name = form.name.data
        user.email = form.email.data
        password = form.passwords.data
        user.password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.passwords.data
        user = User.query.filter_by(email=email).first()
        if not user:
            error = "This email doesnt exist. Please try again."
            return render_template("login.html", error=error, form=form)
        elif not check_password_hash(user.password, password):
            error = "Password incorrect. Please try again."
            return render_template("login.html", error=error, form=form)
        else:
            login_user(user)
            return redirect("/")
    return render_template("login.html", form=form)


@app.route('/cart')
def cart():
    games = Cart.query.all()
    return render_template("cart.html", games=games)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/add', methods=["GET", "POST"])
@admin_only
def add():
    form = AddForm()
    if form.validate_on_submit():
        game = Games()
        game.name = form.name.data
        game.img_url = form.img_url.data
        game.price = form.price.data
        db.session.add(game)
        db.session.commit()
        return redirect("/")
    return render_template("add.html", form=form)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/cart-add/<int:g_id>', methods=["GET", "POST"])
def add_cart(g_id):
    game = Games.query.get(g_id)
    if not current_user.is_authenticated:
        flash("You need to login or register to add games to the cart.")
        return redirect(url_for("login"))
    c = Cart()
    c.game_id = g_id
    c.user_id = current_user.id
    c.name = game.name
    c.price = game.price
    c.img_url = game.img_url
    db.session.add(c)
    db.session.commit()
    return redirect(url_for("home"))


@app.route('/delete/<int:game_id>')
@login_required
def delete(game_id):
    game_delete = Cart.query.get(game_id)
    db.session.delete(game_delete)
    db.session.commit()
    return redirect(url_for('cart'))


@app.route('/create-checkout-session/<int:game_id>', methods=['POST', 'GET'])
def create_checkout_session(game_id):
    game_buy = Cart.query.get(game_id)
    checkout_session = stripe.checkout.Session.create(
        line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": game_buy.name,
                                     "images": [game_buy.img_url]},
                    "unit_amount": int(f"{game_buy.price.strip('$')}00"),
                },
                'quantity': 1,
            }],
        mode='payment',
        success_url=f"http://127.0.0.1:5000/success/{game_id}",
        cancel_url="http://127.0.0.1:5000/cancel",
    )
    return redirect(checkout_session.url, code=303)


@app.route("/success/<int:game_id>")
@login_required
def success(game_id):
    game_bought = Cart.query.get(game_id)
    db.session.delete(game_bought)
    db.session.commit()
    return render_template("success.html", game=game_bought)


@app.route("/cancel")
@login_required
def cancel():
    return render_template("cancel.html")


if __name__ == '__main__':
    app.run(debug=True)
