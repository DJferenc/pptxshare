from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
import os, json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "topsecretadmin"

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"ppt", "pptx", "pdf", "docx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Felhasználók betöltése users.json-ból
try:
    with open("users.json", "r") as f:
        USERS = json.load(f)
except:
    USERS = {
        "kiispista": "titkos123",
        "nagylany": "almafa",
        "ferike99": "mateklecke"
    }
    with open("users.json", "w") as f:
        json.dump(USERS, f)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def user_folder(username):
    return os.path.join(app.config["UPLOAD_FOLDER"], username)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in USERS and USERS[username] == password:
            session["username"] = username
            os.makedirs(user_folder(username), exist_ok=True)
            return redirect(url_for("menu"))
        else:
            flash("Hibás felhasználónév vagy jelszó!")
    return render_template("login.html")

@app.route("/menu")
def menu():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("menu.html", username=session["username"])

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        if "file" not in request.files:
            flash("Nincs fájl!")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("Nincs kiválasztva fájl!")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = user_folder(session["username"])
            os.makedirs(path, exist_ok=True)
            file.save(os.path.join(path, filename))
            flash("Sikeres feltöltés!")
            return redirect(url_for("upload"))
    return render_template("upload.html")

# Letöltés + keresés
@app.route("/download", methods=["GET", "POST"])
def download():
    if "username" not in session:
        return redirect(url_for("login"))

    path = user_folder(session["username"])
    os.makedirs(path, exist_ok=True)
    files = os.listdir(path)

    # keresés
    query = request.args.get("search", "").lower()
    if query:
        files = [f for f in files if query in f.lower()]

    return render_template("download.html", files=files, username=session["username"], query=query)

# Fájl letöltés
@app.route("/files/<username>/<filename>")
def files(username, filename):
    if "username" not in session or session["username"] != username:
        return redirect(url_for("login"))
    return send_from_directory(user_folder(username), filename)

# Fájl törlés
@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    if "username" not in session:
        return redirect(url_for("login"))

    path = user_folder(session["username"])
    file_path = os.path.join(path, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"{filename} törölve lett!")
    else:
        flash("A fájl nem található!")

    return redirect(url_for("download"))

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)

