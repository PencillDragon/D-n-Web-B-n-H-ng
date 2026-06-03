from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "my_secret_key_123"

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    address = db.Column(db.String(200))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    image = db.Column(db.String(300))

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)
    user = db.relationship('User', backref='carts')
    product = db.relationship('Product', backref='carts')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total = db.Column(db.Float)
    address = db.Column(db.String(200))
    status = db.Column(db.String(50), default='Chờ xử lý')
    created_at = db.Column(db.String(50))
    user = db.relationship('User', backref='orders')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    order = db.relationship('Order', backref='items')
    product = db.relationship('Product', backref='order_items')

with app.app_context():
    db.create_all()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.template_filter('vnd')
def vnd(value):
    return "{:,.0f}".format(value).replace(",", ".")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        existing = User.query.filter_by(username=request.form['username']).first()
        if existing: return render_template("register.html", error="Username đã tồn tại")
        user = User(username=request.form['username'], password=request.form['password'], address=request.form['address'])
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'],
        password=request.form['password']).first()
        if user:
            session.clear()
            session["role"] = "user"
            session["user"] = user.username
            session["user_id"] = user.id
            return redirect("/")
        return render_template("login.html", error="Sai tên đăng nhập hoặc mật khẩu")
    return render_template("login.html")

ADMIN_USER, ADMIN_PASS = "admin", "123456"
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session.clear()
            session["role"] = "admin"
            return redirect("/")
        return render_template("admin.html", error="Sai thông tin admin")
    return render_template("admin.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/login")

@app.route('/')
def home():
    if "role" not in session: return redirect(url_for("login"))
    
    keyword = request.args.get("q", "")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    query = Product.query
    if keyword: query = query.filter(Product.name.ilike(f"%{keyword}%"))
    if min_price: query = query.filter(Product.price >= float(min_price))
    if max_price: query = query.filter(Product.price <= float(max_price))
    products = query.all()

    cart_count = 0
    if session.get("role") == "user":
        cart_count = Cart.query.filter_by(user_id=session["user_id"]).count()

    return render_template("index.html", products=products, keyword=keyword, cart_count=cart_count)

@app.route('/cart')
def cart():
    if session.get("role") != "user": return redirect("/login")
    user_id = session["user_id"]
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    user_address = ""
    user = User.query.get(user_id)
    if user: user_address = user.address
        
    return render_template("cart.html", cart_items=cart_items, total=total, user_address=user_address)

@app.route('/cart/add/<int:product_id>')
def cart_add(product_id):
    if session.get("role") != "user": return redirect("/login")
    user_id = session["user_id"]
    item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    if item:
        item.quantity += 1
    else:
        item = Cart(user_id=user_id, product_id=product_id, quantity=1)
        db.session.add(item)
    db.session.commit()
    return redirect("/")

@app.route('/cart/delete/<int:id>')
def cart_delete(id):
    if session.get("role") != "user": return redirect("/login")
    item = Cart.query.get_or_404(id)
    if item.user_id == session["user_id"]:
        db.session.delete(item)
        db.session.commit()
    return redirect("/cart")

@app.route('/order/place', methods=['POST'])
def order_place():
    if session.get("role") != "user": return redirect("/login")
    user_id = session["user_id"]
    items = Cart.query.filter_by(user_id=user_id).all()
    if not items: return redirect("/cart")

    address = request.form['address']
    total = sum(i.product.price * i.quantity for i in items)

    order = Order(user_id=user_id, total=total, address=address, status="Chờ xử lý", created_at=datetime.now().strftime("%d/%m/%Y %H:%M"))
    db.session.add(order)
    db.session.flush()

    for i in items:
        order_item = OrderItem(order_id=order.id, product_id=i.product_id, quantity=i.quantity, price=i.product.price)
        db.session.add(order_item)
        db.session.delete(i)

    db.session.commit()
    return redirect("/orders")

@app.route('/orders')
def orders():
    if session.get("role") != "user": return redirect("/login")
    my_orders = Order.query.filter_by(user_id=session["user_id"]).order_by(Order.id.desc()).all()
    return render_template("orders.html", orders=my_orders)

@app.route('/orders/<int:order_id>')
def order_detail(order_id):
    if session.get("role") != "user": return redirect("/login")
    order = Order.query.get_or_404(order_id)
    if order.user_id != session["user_id"]: return "Bạn không có quyền xem đơn hàng này"
    return render_template("order_detail.html", order=order)

@app.route('/orders/cancel/<int:order_id>')
def order_cancel(order_id):
    if session.get("role") != "user": return redirect("/login")
    order = Order.query.get_or_404(order_id)
    if order.user_id != session["user_id"]: return "Bạn không có quyền"
    if order.status != "Chờ xử lý": return redirect("/orders")
    order.status = "Đã hủy"
    db.session.commit()
    return redirect("/orders")

@app.route("/add", methods=["POST"])
def add():
    if session.get("role") != "admin": return "Bạn không có quyền"
    name, price, file = request.form["name"], request.form["price"], request.files["image"]
    if file.filename == "" or not allowed_file(file.filename): return "Lỗi file ảnh"
    filename = str(uuid.uuid4()) + "." + file.filename.rsplit(".", 1)[1].lower()
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    db.session.add(Product(name=name, price=float(price), image="uploads/" + filename))
    db.session.commit()
    return redirect("/")

@app.route('/delete/<int:id>')
def delete(id):
    if session.get("role") != "admin": return "Bạn không có quyền"
    p = Product.query.get_or_404(id)
    if p:
        if os.path.exists(os.path.join("static", p.image)): os.remove(os.path.join("static", p.image))
        db.session.delete(p)
        db.session.commit()
    return redirect("/")

@app.route('/update/<int:id>', methods=['POST'])
def update(id):

    if session.get("role") != "admin":
        return "Bạn không có quyền"

    p = Product.query.get_or_404(id)

    name = request.form.get('name')
    price = request.form.get('price')

    if name:
        p.name = name

    if price:
        try:
            p.price = float(price)
        except:
            return "Giá không hợp lệ"

    file = request.files.get("new_image")

    if file and file.filename != "" and allowed_file(file.filename):

        if os.path.exists(os.path.join("static", p.image)):
            os.remove(os.path.join("static", p.image))

        filename = str(uuid.uuid4()) + "." + file.filename.rsplit(".", 1)[1].lower()
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        p.image = "uploads/" + filename

    db.session.commit()
    return redirect("/")

@app.route('/admin/orders')
def admin_orders():
    if session.get("role") != "admin": return "Bạn không có quyền"
    orders = Order.query.order_by(Order.id.desc()).all()
    return render_template("admin_orders.html", orders=orders)

@app.route('/admin/order/status/<int:id>', methods=['POST'])
def update_order_status(id):
    if session.get("role") != "admin": return "Bạn không có quyền"
    Order.query.get_or_404(id).status = request.form['status']
    db.session.commit()
    return redirect('/admin/orders')

if __name__ == "__main__":
    app.run(debug=True)