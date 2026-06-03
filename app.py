from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import uuid


app = Flask(__name__)
app.secret_key = "my_secret_key_123"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# mặt hàng
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    image = db.Column(db.String(300))

with app.app_context():
    db.create_all()

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

if __name__ == "__main__":
    app.run(debug=True)