
from flask import Flask, render_template, request, redirect, session, jsonify, Response
import os, sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")

DATABASE = 'database.db'

def get_db():
    return sqlite3.connect(DATABASE)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image TEXT,
        user TEXT,
        rating INTEGER
    )''')
    conn.commit()
    conn.close()

init_db()

# ================= AUTH =================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"]=u
            return redirect("/rate")
        return render_template("login.html", error="Invalid login")

    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        u = request.form["username"]
        p = request.form["password"]
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username,password) VALUES (?,?)",(u,p))
            conn.commit()
        except:
            return render_template("register.html", error="User exists")
        conn.close()
        return redirect("/")
    return render_template("register.html")

# ================= RATE =================
@app.route("/rate")
def rate():
    if "user" not in session:
        return redirect("/")
    images = os.listdir("static/images")
    return render_template("rate.html", images=images)

@app.route("/submit", methods=["POST"])
def submit():
    if "user" not in session:
        return jsonify({"error":"unauthorized"}),401
    data = request.json
    img = data["image"]
    rating = int(data["rating"])
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO ratings (image,user,rating) VALUES (?,?,?)",
              (img, session["user"], rating))
    conn.commit()
    conn.close()
    return jsonify({"msg":"ok"})

# ================= ADMIN =================
@app.route("/admin")
def admin():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT image, AVG(rating) FROM ratings GROUP BY image")
    data = c.fetchall()
    conn.close()
    return render_template("admin.html", data=data)

# ================= CSV =================
@app.route("/download")
def download():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT image,user,rating FROM ratings")
    rows = c.fetchall()
    conn.close()

    def gen():
        yield "image,user,rating\n"
        for r in rows:
            yield f"{r[0]},{r[1]},{r[2]}\n"

    return Response(gen(), mimetype="text/csv",
                    headers={"Content-Disposition":"attachment;filename=data.csv"})

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT image, AVG(rating) FROM ratings GROUP BY image")
    data = c.fetchall()
    conn.close()
    return render_template("dashboard.html", data=data)

if __name__ == "__main__":
    app.run()
