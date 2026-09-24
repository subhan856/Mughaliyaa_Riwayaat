import os, secrets, re
from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import quote

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///mughaliyaa.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

limiter = Limiter(key_func=get_remote_address, app=app, default_limits=[])

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(120), default="")
    email = db.Column(db.String(160), default="")
    password_hash = db.Column(db.String(255), default="")
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    addresses = db.relationship("Address", backref="user", lazy=True)
    orders = db.relationship("Order", backref="user", lazy=True)

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    label = db.Column(db.String(80), default="Home")
    address = db.Column(db.Text, nullable=False)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, default="")
    price = db.Column(db.Numeric(12,2), nullable=False)
    sale_price = db.Column(db.Numeric(12,2))
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(500), default="")
    gallery = db.Column(db.Text, default="")
    sizes = db.Column(db.String(300), default="S,M,L,XL")
    colors = db.Column(db.String(300), default="")
    featured = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    order_no = db.Column(db.String(40), unique=True, nullable=False)
    status = db.Column(db.String(40), default="Pending")
    payment_method = db.Column(db.String(40), default="COD")
    payment_status = db.Column(db.String(40), default="Pending")
    total = db.Column(db.Numeric(12,2), default=0)
    address = db.Column(db.Text, default="")
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    tracking_code = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    product_name = db.Column(db.String(180), nullable=False)
    qty = db.Column(db.Integer, default=1)
    price = db.Column(db.Numeric(12,2), default=0)
    size = db.Column(db.String(40), default="")
    color = db.Column(db.String(60), default="")

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    percent = db.Column(db.Float, default=0)
    active = db.Column(db.Boolean, default=True)

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

@login_manager.user_loader
def load_user(uid):
    return db.session.get(User, int(uid))

def price_for(p):
    return float(p.sale_price if p.sale_price is not None else p.price)

def cart_items():
    raw = session.get("cart", {})
    out=[]
    total=0
    for pid, data in raw.items():
        p=db.session.get(Product, int(pid))
        if not p or not p.active: continue
        qty=max(1, int(data.get("qty",1)))
        qty=min(qty, p.stock if p.stock > 0 else 1)
        line=price_for(p)*qty
        out.append({"product":p,"qty":qty,"size":data.get("size",""),"color":data.get("color",""),"line":line})
        total+=line
    return out,total

@app.context_processor
def inject_globals():
    items,total=cart_items()
    return {
        "cart_count": sum(x["qty"] for x in items),
        "cart_total": total,
        "store_name": os.getenv("STORE_NAME","Mughaliyaa Riyawaat"),
        "store_phone": os.getenv("STORE_PHONE","+92XXXXXXXXXX"),
        "store_whatsapp": os.getenv("STORE_WHATSAPP","+92XXXXXXXXXX"),
        "store_email": os.getenv("STORE_EMAIL","your@email.com"),
        "store_address": os.getenv("STORE_ADDRESS","Rawalpindi, Pakistan"),
        "store_lat": os.getenv("STORE_LAT","33.6844"),
        "store_lng": os.getenv("STORE_LNG","73.0479")
    }

@app.route("/")
def home():
    products=Product.query.filter_by(active=True).order_by(Product.created_at.desc()).limit(8).all()
    return render_template("home.html", products=products)

@app.route("/shop")
def shop():
    q=request.args.get("q","").strip()
    category=request.args.get("category","").strip()
    query=Product.query.filter_by(active=True)
    if q: query=query.filter(Product.name.ilike(f"%{q}%"))
    if category: query=query.filter_by(category=category)
    products=query.order_by(Product.created_at.desc()).all()
    categories=[x[0] for x in db.session.query(Product.category).filter_by(active=True).distinct().all()]
    return render_template("shop.html", products=products, categories=categories, q=q, category=category)

@app.route("/product/<slug>")
def product(slug):
    p=Product.query.filter_by(slug=slug,active=True).first_or_404()
    gallery=[x.strip() for x in p.gallery.split(",") if x.strip()]
    return render_template("product.html", product=p, gallery=gallery)

@app.post("/cart/add")
def cart_add():
    pid=int(request.form["product_id"])
    p=db.session.get(Product,pid) or abort(404)
    qty=max(1,int(request.form.get("qty",1)))
    if p.stock < qty: flash("Stock available nahi hai.","error"); return redirect(request.referrer or url_for("shop"))
    cart=session.get("cart",{})
    cart[str(pid)]={"qty":qty,"size":request.form.get("size",""),"color":request.form.get("color","")}
    session["cart"]=cart
    flash("Product cart mein add ho gaya.","success")
    return redirect(url_for("cart"))

@app.route("/cart")
def cart():
    items,total=cart_items()
    return render_template("cart.html",items=items,total=total)

@app.post("/cart/remove/<int:pid>")
def cart_remove(pid):
    cart=session.get("cart",{})
    cart.pop(str(pid),None); session["cart"]=cart
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET","POST"])
@login_required
def checkout():
    items,total=cart_items()
    if not items: return redirect(url_for("shop"))
    if request.method=="POST":
        address=request.form.get("address","").strip()
        if not address: flash("Delivery address zaroori hai.","error"); return redirect(url_for("checkout"))
        discount=0
        code=request.form.get("coupon","").strip().upper()
        if code:
            c=Coupon.query.filter_by(code=code,active=True).first()
            if c: discount=total*c.percent/100
        final=round(total-discount,2)
        order=Order(user_id=current_user.id, order_no="MR-"+secrets.token_hex(5).upper(),
                    payment_method=request.form.get("payment_method","COD"),
                    total=final,address=address,
                    lat=float(request.form["lat"]) if request.form.get("lat") else None,
                    lng=float(request.form["lng"]) if request.form.get("lng") else None)
        db.session.add(order); db.session.flush()
        for x in items:
            db.session.add(OrderItem(order_id=order.id,product_id=x["product"].id,
                product_name=x["product"].name,qty=x["qty"],price=x["product"].sale_price or x["product"].price,
                size=x["size"],color=x["color"]))
            x["product"].stock=max(0,x["product"].stock-x["qty"])
        db.session.commit()
        session["cart"]={}
        return redirect(url_for("order_detail",order_no=order.order_no))
    return render_template("checkout.html",items=items,total=total)

@app.route("/order/<order_no>")
@login_required
def order_detail(order_no):
    o=Order.query.filter_by(order_no=order_no,user_id=current_user.id).first_or_404()
    return render_template("order.html",order=o)

@app.route("/account")
@login_required
def account():
    return render_template("account.html",orders=Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all())

@app.route("/login", methods=["GET","POST"])
@limiter.limit("10/minute")
def login():
    if request.method=="POST":
        phone=re.sub(r"\s+","",request.form.get("phone",""))
        if not phone: flash("Phone number enter karo.","error")
        else:
            session["otp_phone"]=phone
            session["otp_sent_at"]=datetime.utcnow().isoformat()
            # Production: call Twilio Verify here.
            try:
                from twilio.rest import Client
                sid=os.getenv("TWILIO_ACCOUNT_SID"); token=os.getenv("TWILIO_AUTH_TOKEN"); service=os.getenv("TWILIO_VERIFY_SERVICE_SID")
                if sid and token and service:
                    Client(sid,token).verify.v2.services(service).verifications.create(to=phone,channel="sms")
                    session["otp_mode"]="twilio"
                else:
                    session["otp_mode"]="not_configured"
                    flash("OTP provider configure nahi hua. .env mein Twilio Verify credentials add karo.","error")
                    return redirect(url_for("login"))
                return redirect(url_for("verify_otp"))
            except Exception:
                flash("OTP service se connection nahi hua. Credentials/API check karo.","error")
    return render_template("login.html")

@app.route("/verify-otp", methods=["GET","POST"])
@limiter.limit("10/minute")
def verify_otp():
    phone=session.get("otp_phone")
    if not phone: return redirect(url_for("login"))
    if request.method=="POST":
        code=request.form.get("code","").strip()
        try:
            from twilio.rest import Client
            Client(os.getenv("TWILIO_ACCOUNT_SID"),os.getenv("TWILIO_AUTH_TOKEN")).verify.v2.services(os.getenv("TWILIO_VERIFY_SERVICE_SID")).verification_checks.create(to=phone,code=code)
            u=User.query.filter_by(phone=phone).first()
            if not u:
                u=User(phone=phone); db.session.add(u); db.session.commit()
            login_user(u,remember=True)
            return redirect(url_for("account"))
        except Exception:
            flash("OTP verify nahi hua.","error")
    return render_template("verify_otp.html",phone=phone)

@app.route("/logout")
def logout():
    logout_user(); return redirect(url_for("home"))

@app.post("/wishlist/<int:pid>")
@login_required
def wishlist(pid):
    if Product.query.get_or_404(pid):
        exists=Wishlist.query.filter_by(user_id=current_user.id,product_id=pid).first()
        if exists: db.session.delete(exists)
        else: db.session.add(Wishlist(user_id=current_user.id,product_id=pid))
        db.session.commit()
    return redirect(request.referrer or url_for("shop"))

@app.route("/admin")
@login_required
def admin():
    if not current_user.is_admin: abort(403)
    return render_template("admin.html",products=Product.query.order_by(Product.id.desc()).all(),
        orders=Order.query.order_by(Order.created_at.desc()).all(),users=User.query.order_by(User.id.desc()).all())

@app.post("/admin/product")
@login_required
def admin_product():
    if not current_user.is_admin: abort(403)
    name=request.form["name"].strip()
    slug=re.sub(r"[^a-z0-9]+","-",name.lower()).strip("-")+"-"+secrets.token_hex(2)
    p=Product(name=name,slug=slug,category=request.form["category"],description=request.form.get("description",""),
              price=Decimal(request.form["price"]),sale_price=Decimal(request.form["sale_price"]) if request.form.get("sale_price") else None,
              stock=int(request.form.get("stock",0)),image=request.form.get("image",""),
              gallery=request.form.get("gallery",""),sizes=request.form.get("sizes","S,M,L,XL"),
              colors=request.form.get("colors",""),featured=bool(request.form.get("featured")))
    db.session.add(p); db.session.commit()
    return redirect(url_for("admin"))

@app.post("/admin/order/<int:oid>")
@login_required
def admin_order(oid):
    if not current_user.is_admin: abort(403)
    o=Order.query.get_or_404(oid)
    o.status=request.form.get("status",o.status)
    o.tracking_code=request.form.get("tracking_code",o.tracking_code)
    o.payment_status=request.form.get("payment_status",o.payment_status)
    db.session.commit()
    return redirect(url_for("admin"))

@app.route("/api/map")
def map_api():
    orders=Order.query.filter(Order.lat.isnot(None),Order.lng.isnot(None)).all()
    return jsonify([{"order":o.order_no,"lat":o.lat,"lng":o.lng,"status":o.status} for o in orders])

@app.route("/track")
def track():
    return render_template("track.html")

@app.post("/api/track")
def api_track():
    code=request.form.get("code","").strip()
    o=Order.query.filter_by(tracking_code=code).first()
    if not o: return jsonify({"ok":False,"message":"Tracking code nahi mila."}),404
    return jsonify({"ok":True,"order":o.order_no,"status":o.status,"created":o.created_at.strftime("%d %b %Y"),"tracking":o.tracking_code})

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/health")
def health(): return {"ok":True,"service":"Mughaliyaa Riyawaat"}

def seed():
    db.create_all()
    if not User.query.filter_by(phone=os.getenv("ADMIN_PHONE","+920000000000")).first():
        admin=User(phone=os.getenv("ADMIN_PHONE","+920000000000"),name="Store Admin",
                   email=os.getenv("ADMIN_EMAIL","admin@mughaliyaa.com"),
                   password_hash=generate_password_hash(os.getenv("ADMIN_PASSWORD","ChangeThisNow!")),
                   is_admin=True)
        db.session.add(admin)
    if not Coupon.query.filter_by(code="ROYAL10").first():
        db.session.add(Coupon(code="ROYAL10",percent=10))
    if Product.query.count()==0:
        demo=[
            ("Royal Bridal Lehenga","Bridal","85000","75000",6,"https://images.unsplash.com/photo-1594633312681-425c7b97ccd1"),
            ("Mughal Sharara","Sharara","48500","",8,"https://images.unsplash.com/photo-1610030469983-98e550d080f1"),
            ("Emerald Formal","Formal","32000","",10,"https://images.unsplash.com/photo-1595777457583-95e059d581b8"),
            ("Velvet Evening Dress","Party Wear","27500","24500",12,"https://images.unsplash.com/photo-1566479179817-c0e1f2c7f6f3")
        ]
        for n,c,p,s,st,img in demo:
            slug=re.sub(r"[^a-z0-9]+","-",n.lower()).strip("-")+"-"+secrets.token_hex(2)
            db.session.add(Product(name=n,slug=slug,category=c,price=Decimal(p),sale_price=Decimal(s) if s else None,stock=st,image=img,featured=True))
    db.session.commit()

with app.app_context(): seed()

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")),debug=True)
