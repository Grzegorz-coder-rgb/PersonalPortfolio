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

if __name__ == '__main__':
    app.run(debug=True)