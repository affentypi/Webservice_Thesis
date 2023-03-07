import re
from datetime import datetime

from flask import *

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/explanation/")
def explanation():
    return render_template("explanation.html")


@app.route("/twoLinks/", methods=['POST', 'GET'])
def twoLinks():
    if request.method == 'POST':
        oldDoc = request.form['old']
        newDoc = request.form['new']
        ok = request.form['checkbox']
        failure = "none"

        if oldDoc == "" or newDoc == "":
            failure = "one or both of the links were empty" #TODO oneLink?
            return render_template("error.html", failure)
        if ok:
            "success"
            return render_template("twoLinks.html")
        else:
            failure = "checkbox for Standard-search was not ticked"
            return render_template("error.html", failure)
    else:  # HTTP GET
        return render_template("twoLinks.html")


@app.route("/oneLink/", methods=['POST', 'GET'])
def oneLink():
    if request.method == 'POST':
        doc = request.form['doc']
        ok = request.form['checkbox']
        failure = "none"

        if doc == "":
            failure = "no link entered"
            return render_template("error.html", failure)
        if ok:
            "success"
            return render_template("oneLink.html")
        else:
            failure = "checkbox for OneLink-search was not ticked"
            return render_template("error.html", failure)
    else:  # HTTP GET
        return render_template("oneLink.html")


@app.route("/CELEX/", methods=['POST', 'GET'])
def celex():
    if request.method == 'POST':
        doc = request.form['celex']
        ok = request.form['checkbox']
        failure = "none"

        if doc == "":
            failure = "no CELEX Number was entered"
            return render_template("error.html", failure)
        if ok:
            "success"
            return render_template("celex.html")
        else:
            failure = "checkbox for CELEX-search was not ticked"
            return render_template("error.html", failure)
    else:  # HTTP GET
        return render_template("celex.html")


@app.route("/about/")
def about():
    return render_template("about.html")


@app.route("/hello/")
@app.route("/hello/<name>")
def hello_there(name=None):
    return render_template(
        "hello_there.html",
        name=name,
        date=datetime.now()
    )
    # Filter the name argument to letters only using regular expressions. URL arguments
    # can contain arbitrary text, so we restrict to safe characters only.
    # match_object = re.match("[a-zA-Z]+", name) TODO


@app.route("/api/data")
def get_data():
    return app.send_static_file("data.json")
