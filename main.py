from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/hire.html")
def hire():
    return render_template("hire.html")

@app.route("/projects.html")
def projects():
    return render_template("projects.html")

@app.route("/plan.html")
def plan():
    return render_template("plan.html")

@app.route("/python.html")
def view():
    return render_template("python.html")

@app.route("/full.html")
def full():
    return render_template("full.html")

@app.route("/frontend.html")
def frontend():
    return render_template("frontend.html")

@app.route("/backend.html")
def backend():
    return render_template("backend.html")

@app.route("/AI.html")
def ai():
    return render_template("AI.html")


if __name__ == '__main__':
    app.run(debug=True)
