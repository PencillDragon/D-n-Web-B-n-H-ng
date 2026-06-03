from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "my_secret_key_123"


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

if __name__ == "__main__":
    app.run(debug=True)