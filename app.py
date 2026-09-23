```python
from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)

# Basic settings
app.config["SECRET_KEY"] = "mughaliyaa-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mughaliyaa.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


# =========================
# DATABASE TABLES
# =========================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100))
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(500))


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    phone = db.Column(db.String(30))
    address = db.Column(db.Text)
    total = db.Column(db.Float)
    status = db.Column(db.String(50), default="Pending")
    tracking_code = db.Column(db.String(50), unique=True)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# =========================
# SIMPLE WEBSITE DESIGN
# =========================

STYLE = """
<style>
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f7f3ed;
    color: #222;
}

nav {
    background: #111;
    color: white;
    padding: 18px 7%;
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
}

nav a {
    color: white;
    text-decoration: none;
    margin: 8px;
}

.brand {
    font-size: 23px;
    font-weight: bold;
}

.hero {
    background: #24170e;
    color: white;
    text-align: center;
    padding: 80px 20px;
}

.hero h1 {
    font-size: 42px;
}

.container {
    width: 88%;
    max-width: 1100px;
    margin: 35px auto;
}

.grid {
    display: grid;
    grid-template-columns:
    repeat(auto-fit, minmax(230px, 1fr));
    gap: 20px;
}

.card {
    background: white;
    padding: 18px;
    border-radius: 12px;
    box-shadow: 0 3px 15px #0001;
}

.card img {
    width: 100%;
    height: 250px;
    object-fit: cover;
    border-radius: 8px;
}

input, textarea {
    width: 100%;
    padding: 12px;
    margin: 7px 0 14px;
    border: 1px solid #ccc;
    border-radius: 7px;
}

button, .btn {
    background: #111;
    color: white;
    padding: 11px 18px;
    border: none;
    border-radius: 7px;
    text-decoration: none;
    cursor: pointer;
}

.price {
    font-size: 20px;
    font-weight: bold;
}

footer {
    background: #111;
    color: white;
    text-align: center;
    padding: 30px;
    margin-top: 50px;
}
</style>
"""


def page(content):
    return STYLE + """
    <nav>
        <div class="brand">Mughaliyaa Riyawaat</div>

        <div>
            <a href="/">Home</a>
            <a href="/products">Shop</a>
            <a href="/cart">Cart</a>
            <a href="/track">Track Order</a>

            {% if current_user.is_authenticated %}
                <a href="/logout">Logout</a>
            {% else %}
                <a href="/login">Login</a>
            {% endif %}
        </div>
    </nav>
    """ + content + """
    <footer>
        Mughaliyaa Riyawaat — Pakistani Luxury Fashion
    </footer>
    """


# =========================
# HOME
# =========================

@app.route("/")
def home():

    products = Product.query.filter(
        Product.stock > 0
    ).limit(6).all()

    content = """
    <section class="hero">
        <h1>Luxury Pakistani Fashion</h1>

        <p>
            Traditional style with a modern luxury look.
        </p>

        <a class="btn" href="/products">
            Explore Collection
        </a>
    </section>

    <div class="container">

        <h2>Featured Products</h2>

        <div class="grid">

        {% for p in products %}

            <div class="card">

                {% if p.image %}
                <img src="{{ p.image }}">
                {% endif %}

                <h3>{{ p.name }}</h3>

                <p>{{ p.category }}</p>

                <p class="price">
                    Rs. {{ "%.0f"|format(p.price) }}
                </p>

                <a class="btn"
                   href="/product/{{ p.id }}">
                    View Product
                </a>

            </div>

        {% endfor %}

        </div>

    </div>
    """

    return render_template_string(
        page(content),
        products=products
    )


# =========================
# PRODUCTS
# =========================

@app.route("/products")
def products():

    search = request.args.get("q", "")

    if search:
        products = Product.query.filter(
            Product.name.ilike("%" + search + "%")
        ).all()
    else:
        products = Product.query.all()

    content = """
    <div class="container">

        <h1>Shop</h1>

        <form>
            <input
                name="q"
                placeholder="Search products..."
                value="{{ search }}"
            >

            <button>Search</button>
        </form>

        <div class="grid">

        {% for p in products %}

            <div class="card">

                {% if p.image %}
                <img src="{{ p.image }}">
                {% endif %}

                <h3>{{ p.name }}</h3>

                <p>{{ p.description }}</p>

                <p class="price">
                    Rs. {{ "%.0f"|format(p.price) }}
                </p>

                <p>Stock: {{ p.stock }}</p>

                <a class="btn"
                   href="/product/{{ p.id }}">
                   Details
                </a>

            </div>

        {% endfor %}

        </div>

    </div>
    """

    return render_template_string(
        page(content),
        products=products,
        search=search
    )


# =========================
# PRODUCT DETAIL
# =========================

@app.route("/product/<int:product_id>")
def product_detail(product_id):

    product = db.get_or_404(Product, product_id)

    content = """
    <div class="container">

        <div class="card">

            {% if product.image %}
            <img src="{{ product.image }}"
                 style="max-width:500px">
            {% endif %}

            <h1>{{ product.name }}</h1>

            <p>{{ product.description }}</p>

            <p class="price">
                Rs. {{ "%.0f"|format(product.price) }}
            </p>

            <p>
                Available Stock: {{ product.stock }}
            </p>

            {% if product.stock > 0 %}

            <a class="btn"
               href="/cart/add/{{ product.id }}">
               Add to Cart
            </a>

            {% endif %}

        </div>

    </div>
    """

    return render_template_string(
        page(content),
        product=product
    )


# =========================
# LOGIN / REGISTER
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        name = request.form["name"]
        phone = request.form["phone"]
        password = request.form["password"]

        user = User.query.filter_by(phone=phone).first()

        if not user:

            user = User(
                name=name,
                phone=phone,
                password=generate_password_hash(password)
            )

            db.session.add(user)
            db.session.commit()

        else:

            if not check_password_hash(
                user.password,
                password
            ):
                return "Wrong password."

        login_user(user)

        return redirect("/")

    content = """
    <div class="container">

        <div class="card">

            <h1>Login / Register</h1>

            <form method="POST">

                <label>Name</label>
                <input name="name" required>

                <label>Phone</label>
                <input name="phone" required>

                <label>Password</label>
                <input
                    name="password"
                    type="password"
                    required
                >

                <button>
                    Continue
                </button>

            </form>

        </div>

    </div>
    """

    return render_template_string(page(content))


@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect("/")


# =========================
# CART
# =========================

@app.route("/cart")
def cart():

    cart = session.get("cart", [])

    products = Product.query.filter(
        Product.id.in_(cart)
    ).all() if cart else []

    total = sum(p.price for p in products)

    content = """
    <div class="container">

        <h1>Your Cart</h1>

        {% if products %}

            {% for p in products %}

            <div class="card">

                <h3>{{ p.name }}</h3>

                <p>
                    Rs. {{ "%.0f"|format(p.price) }}
                </p>

                <a class="btn"
                   href="/cart/remove/{{ p.id }}">
                   Remove
                </a>

            </div>

            {% endfor %}

            <h2>
                Total:
                Rs. {{ "%.0f"|format(total) }}
            </h2>

            <a class="btn" href="/checkout">
                Checkout
            </a>

        {% else %}

            <p>Your cart is empty.</p>

        {% endif %}

    </div>
    """

    return render_template_string(
        page(content),
        products=products,
        total=total
    )


@app.route("/cart/add/<int:product_id>")
def add_to_cart(product_id):

    product = db.get_or_404(Product, product_id)

    if product.stock > 0:

        cart = session.get("cart", [])

        cart.append(product.id)

        session["cart"] = cart

    return redirect("/cart")


@app.route("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):

    cart = session.get("cart", [])

    if product_id in cart:
        cart.remove(product_id)

    session["cart"] = cart

    return redirect("/cart")


# =========================
# CHECKOUT
# =========================

@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    cart = session.get("cart", [])

    products = Product.query.filter(
        Product.id.in_(cart)
    ).all() if cart else []

    if not products:
        return redirect("/cart")

    total = sum(p.price for p in products)

    if request.method == "POST":

        code = "MR-" + secrets.token_hex(4).upper()

        order = Order(
            customer_name=request.form["name"],
            phone=request.form["phone"],
            address=request.form["address"],
            total=total,
            status="Pending",
            tracking_code=code
        )

        for p in products:
            if p.stock > 0:
                p.stock -= 1

        db.session.add(order)
        db.session.commit()

        session["cart"] = []

        return f"""
        <div class="container">
            <div class="card">
                <h1>Order Placed!</h1>

                <p>
                    Your tracking code is:
                    <b>{code}</b>
                </p>

                <a class="btn" href="/track">
                    Track Order
                </a>
            </div>
        </div>
        """

    content = """
    <div class="container">

        <div class="card">

            <h1>Checkout</h1>

            <h3>
                Total:
                Rs. {{ "%.0f"|format(total) }}
            </h3>

            <form method="POST">

                <input
                    name="name"
                    placeholder="Full Name"
                    required
                >

                <input
                    name="phone"
                    placeholder="Phone"
                    required
                >

                <textarea
                    name="address"
                    placeholder="Delivery Address"
                    required
                ></textarea>

                <button>
                    Place Order
                </button>

            </form>

        </div>

    </div>
    """

    return render_template_string(
        page(content),
        total=total
    )


# =========================
# ORDER TRACKING
# =========================

@app.route("/track")
def track():

    code = request.args.get("code", "")

    order = None

    if code:
        order = Order.query.filter_by(
            tracking_code=code
        ).first()

    content = """
    <div class="container">

        <div class="card">

            <h1>Track Order</h1>

            <form>

                <input
                    name="code"
                    placeholder="MR-XXXXXXXX"
                    value="{{ code }}"
                >

                <button>
                    Track
                </button>

            </form>

            {% if order %}

                <hr>

                <h2>
                    Order #{{ order.id }}
                </h2>

                <p>
                    Status:
                    <b>{{ order.status }}</b>
                </p>

                <p>
                    Total:
                    Rs. {{ "%.0f"|format(order.total) }}
                </p>

            {% elif code %}

                <p>
                    Order not found.
                </p>

            {% endif %}

        </div>

    </div>
    """

    return render_template_string(
        page(content),
        order=order,
        code=code
    )


# =========================
# SAMPLE PRODUCTS
# =========================

def add_sample_products():

    if Product.query.count() == 0:

        db.session.add_all([

            Product(
                name="Royal Bridal Lehenga",
                category="Bridal",
                price=85000,
                description="Traditional luxury bridal lehenga.",
                stock=5
            ),

            Product(
                name="Classic Sharara",
                category="Sharara",
                price=45000,
                description="Elegant sharara for special occasions.",
                stock=8
            ),

            Product(
                name="Mughaliyaa Party Dress",
                category="Party Wear",
                price=32000,
                description="Luxury party wear.",
                stock=10
            )

        ])

        db.session.commit()


# Create database
with app.app_context():

    db.create_all()

    add_sample_products()


# Start website
if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
```

