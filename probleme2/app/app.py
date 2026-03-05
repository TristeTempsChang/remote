from flask import Flask, request, session, redirect, url_for, render_template_string, abort

app = Flask(__name__)

USERS = {
    "tristan": "password123",
}

LOGIN_FORM = """
<!doctype html>
<title>TeamBulbizarre</title>
<h1>Login</h1>
<form method="post">
  <input name="username" placeholder="username" required>
  <input name="password" placeholder="password" type="password" required>
  <button type="submit">Sign in</button>
</form>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
"""

@app.get("/login")
def login_get():
    return render_template_string(LOGIN_FORM, error=None)

@app.post("/login")
def login_post():
    u = request.form.get("username", "")
    p = request.form.get("password", "")
    if USERS.get(u) == p:
        session["user"] = u
        return redirect(url_for("private"))
    return render_template_string(LOGIN_FORM, error="Invalid credentials"), 401

@app.get("/private")
def private():
    if "user" not in session:
        return redirect(url_for("login_get"))
    return "Accès au contenu privé autorisé", 200