from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import uuid


app = Flask(__name__)
app.secret_key = "my_secret_key_123"

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# người dùng
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    address = db.Column(db.String(200))


with app.app_context():
    db.create_all()

# đăng ký tài khoản
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        user = User(
            username=request.form['username'],
            password=request.form['password'],
            address=request.form['address']
        )

        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template("register.html")

# đăng nhập người dùng
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        user = User.query.filter_by(
            username=request.form['username'],
            password=request.form['password']
        ).first()

        if user:
            session.clear()

            session["role"] = "user"
            session["user"] = user.username
            return redirect("/")

        return "Sai login"

    return render_template("login.html")

# đăng nhập admin
ADMIN_USER = "admin"
ADMIN_PASS = "123456"

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session.clear()
            session["role"] = "admin"
            return redirect("/")

        return "Sai admin"

    return render_template("admin.html")

# đăng xuất
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/login")

>>>>>>> Stashed changes
# giỏ hàng
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)

    user = db.relationship('User', backref='carts')
    product = db.relationship('Product', backref='carts')

# đặt hàng
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total = db.Column(db.Float)
    address = db.Column(db.String(200))
    status = db.Column(db.String(50), default='Chờ xử lý')
    created_at = db.Column(db.String(50))

    user = db.relationship('User', backref='orders')

# hàng được đặt
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)

    order = db.relationship('Order', backref='items')
    product = db.relationship('Product', backref='order_items')


db = SQLAlchemy(app)

# mặt hàng
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    image = db.Column(db.String(300))

with app.app_context():
    db.create_all()

# thêm vào giỏ hàng
@app.route('/cart/add/<int:product_id>')
def cart_add(product_id):
    if session.get("role") != "user":
        return redirect("/login")

    user_id = session["user_id"]

    # kiểm tra đã có trong giỏ chưa
    item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if item:
        item.quantity += 1
    else:
        item = Cart(user_id=user_id, product_id=product_id, quantity=1)
        db.session.add(item)

    db.session.commit()
    return redirect("/cart")

# xem giỏ hàng
@app.route('/cart')
def cart():
    if session.get("role") != "user":
        return redirect("/login")

    user_id = session["user_id"]
    items = Cart.query.filter_by(user_id=user_id).all()

    total = sum(i.product.price * i.quantity for i in items)
    return render_template("cart.html", items=items, total=total)

# cập nhật số lượng trong giỏ
@app.route('/cart/update/<int:cart_id>', methods=['POST'])
def cart_update(cart_id):
    if session.get("role") != "user":
        return redirect("/login")

    item = Cart.query.get_or_404(cart_id)
    qty = int(request.form['quantity'])

    if qty <= 0:
        db.session.delete(item)
    else:
        item.quantity = qty

    db.session.commit()
    return redirect("/cart")

# xóa khỏi giỏ hàng
@app.route('/cart/delete/<int:cart_id>')
def cart_delete(cart_id):
    if session.get("role") != "user":
        return redirect("/login")

    item = Cart.query.get_or_404(cart_id)
    db.session.delete(item)
    db.session.commit()
    return redirect("/cart")

# đặt hàng (từ giỏ hàng)
@app.route('/order/place', methods=['POST'])
def order_place():
    if session.get("role") != "user":
        return redirect("/login")

    user_id = session["user_id"]
    items = Cart.query.filter_by(user_id=user_id).all()

    if not items:
        return redirect("/cart")

    address = request.form['address']
    total = sum(i.product.price * i.quantity for i in items)

    order = Order(
        user_id=user_id,
        total=total,
        address=address,
        status="Chờ xử lý",
        created_at=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    db.session.add(order)
    db.session.flush()  # lấy order.id trước khi commit

    for i in items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=i.product_id,
            quantity=i.quantity,
            price=i.product.price
        )
        db.session.add(order_item)
        db.session.delete(i)  # xóa khỏi giỏ

    db.session.commit()
    return redirect("/orders")

# xem đơn hàng của user
@app.route('/orders')
def orders():
    if session.get("role") != "user":
        return redirect("/login")

    user_id = session["user_id"]
    my_orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()

    return render_template("orders.html", orders=my_orders)

# xem chi tiết đơn hàng
@app.route('/orders/<int:order_id>')
def order_detail(order_id):
    if session.get("role") != "user":
        return redirect("/login")

    order = Order.query.get_or_404(order_id)

    if order.user_id != session["user_id"]:
        return "Bạn không có quyền xem đơn hàng này"

    return render_template("order_detail.html", order=order)

# hủy đơn hàng
@app.route('/orders/cancel/<int:order_id>')
def order_cancel(order_id):
    if session.get("role") != "user":
        return redirect("/login")

    order = Order.query.get_or_404(order_id)

    if order.user_id != session["user_id"]:
        return "Bạn không có quyền hủy đơn hàng này"

    if order.status != "Chờ xử lý":
        return redirect("/orders")

    order.status = "Đã hủy"
    db.session.commit()
    return redirect("/orders")

if __name__ == "__main__":
    app.run(debug=True)

# trang chủ
@app.route('/')
def home():
    
    if "role" not in session:
        return redirect(url_for("login"))
    keyword = request.args.get("q", "")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")

    query = Product.query

    if keyword:
        query = query.filter(Product.name.ilike(f"%{keyword}%"))

    if min_price:
        query = query.filter(Product.price >= float(min_price))

    if max_price:
        query = query.filter(Product.price <= float(max_price))

    products = query.all()

    return render_template(
        "index.html",
        products=products,
        keyword=keyword
    )

# hàm check file ảnh
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.template_filter('vnd')
def vnd(value):
    return "{:,.0f}".format(value).replace(",", ".")

# thêm
@app.route("/add", methods=["POST"])
def add():

    if session.get("role") != "admin":
        return "Bạn không có quyền để làm điều này"

    name = request.form["name"]
    price = request.form["price"]

    file = request.files["image"]

    if file.filename == "":
        return "Vui lòng chọn ảnh"

    if not allowed_file(file.filename):
        return "Định dạng ảnh không đúng"

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = str(uuid.uuid4()) + "." + ext

    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    
    p = Product(
        name=name,
        price=price,
        image="uploads/" + filename
    )

    db.session.add(p)
    db.session.commit()

    return redirect("/")
# xóa
@app.route('/delete/<int:id>')
def delete(id):

    if session.get("role") != "admin":
        return "Bạn không có quyền để làm điều này"

    p = Product.query.get_or_404(id)

    if p:
        image_path = os.path.join("static", p.image)

        if os.path.exists(image_path):
            os.remove(image_path)

        db.session.delete(p)
        db.session.commit()

    return redirect("/")

# cập nhật
@app.route('/update/<int:id>', methods=['POST'])
def update(id):

    if session.get("role") != "admin":
        return "Bạn không có quyền để làm điều này"

    p = Product.query.get_or_404(id)

    name = request.form['name']
    price = request.form['price']
    
    p.name=name
    p.price=price

    file = request.files["new image"]
    if file.filename == "":
        return "Vui lòng chọn ảnh"

    if not allowed_file(file.filename):
        return "Định dạng ảnh không đúng"

    old_image = os.path.join("static", p.image)
    if os.path.exists(old_image):
        os.remove(old_image)
        
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = str(uuid.uuid4()) + "." + ext

    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    p.image = "uploads/" + filename

    db.session.commit()

    return redirect("/")

# xem tất cả đơn hàng (admin)
@app.route('/admin/orders')
def admin_orders():

    if session.get("role") != "admin":
        return "Bạn không có quyền để làm điều này"

    orders = Order.query.order_by(Order.id.desc()).all()
    return render_template("admin_orders.html", orders=orders)

# cập nhật trạng thái đơn hàng
@app.route('/admin/order/status/<int:id>', methods=['POST'])
def update_order_status(id):

    if session.get("role") != "admin":
        return "Bạn không có quyền để làm điều này"

    order = Order.query.get_or_404(id)
    order.status = request.form['status']
    db.session.commit()

    return redirect('/admin/orders')

if __name__ == "__main__":
    app.run(debug=True)
