from datetime import datetime

import html_processing as html
import nlp_processing as run

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
        try:
            old_url = request.form['old']
            new_url = request.form['new']
            radio = request.form['btnradio']
            print(radio) #ToDo Just on? acc = false, fast is true
        except Exception as e:
            return render_template("error.html", exception= e)
        #run  todo
        celex_old, doc_old = html.pars_html(old_url)
        celex_new, doc_new = html.pars_html(new_url)

        run.process_changes(radio + celex_old + celex_new, html.find_changes_and_make_diff_of_surrounding_text(doc_old, doc_new), radio == "fast")
        return render_template("run"+ radio + celex_old + celex_new +".html", celex_new= celex_new, celex_old= celex_old)
    else:  # HTTP GET
        return render_template("twoLinks.html")


@app.route("/oneLink/", methods=['POST', 'GET'])
def oneLink():
    if request.method == 'POST':
        try:
            url = request.form['doc']
            radio = request.form['btnradio']
        except Exception as e:
            return render_template("error.html", exception=e)

        celex_old, doc_old = html.pars_html(url)
        celex_new, doc_new = html.find_newest(url)
        run.process_changes(radio + celex_old + celex_new, html.find_changes_and_make_diff_of_surrounding_text(doc_old, doc_new), radio == "fast")
        return render_template("run"+ radio + celex_old + celex_new +".html", celex_new=celex_new, celex_old=celex_old)
    else:  # HTTP GET
        return render_template("oneLink.html")


@app.route("/celex/", methods=['POST', 'GET'])
def celex():
    if request.method == 'POST':
        try:
            celex_input = request.form['celex']
            radio = request.form['btnradio']
        except Exception as e:
            return render_template("error.html", exception=e)

        print("it works")
        url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:" + celex_input
        celex_old, doc_old = html.pars_html(url)
        if celex_input != celex_old:
            print("ERROR")
        celex_new, doc_new = html.find_newest(url)
        run.process_changes(radio + celex_old + celex_new,
                            html.find_changes_and_make_diff_of_surrounding_text(doc_old, doc_new), radio == "fast")
        return render_template("run" + radio + celex_old + celex_new + ".html", celex_new=celex_new,
                               celex_old=celex_old)
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
