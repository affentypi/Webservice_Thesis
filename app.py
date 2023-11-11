import html_processing as html
import nlp_processing as run

from flask import *

app = Flask(__name__)


@app.route("/")
@app.route("/home/")
def home():
    return render_template("home.html")

@app.route("/explanation/")
def explanation():
    return render_template("explanation.html")

@app.route("/twoLinks/", methods=['POST', 'GET'])
def twoLinks():
    "Enter old and new document."
    if request.method == 'POST':
        try: # fetch input
            old_url = request.form['old']
            new_url = request.form['new']
            radio = request.form['btnradio']
            print(radio)
        except Exception as e:
            return render_template("error.html", exception= e)
        try: # run the algorithm
            celex_old, doc_old = html.pars_html(old_url)
            celex_new, doc_new = html.pars_html(new_url)
            run.process_nlp(radio + celex_old + celex_new, html.find_changes_and_make_diff_of_surrounding_text(doc_old, doc_new), radio == "fast")
            return render_template("x_output_run"+ radio + celex_old + celex_new +".html", celex_new= celex_new, celex_old= celex_old)
        except Exception as e:
            return render_template("error.html", exception=e)
    else:  # HTTP GET
        return render_template("twoLinks.html")

@app.route("/oneLink/", methods=['POST', 'GET'])
def oneLink():
    "Only enter the link to the old document."
    if request.method == 'POST':
        try: # fetch input
            url = request.form['doc']
            radio = request.form['btnradio']
            print(radio)
        except Exception as e:
            return render_template("error.html", exception=e)
        try: # run the algorithm
            celex_old, doc_old = html.pars_html(url)
            celex_new, doc_new = html.find_newest(url)
            run.process_nlp(radio + celex_old + celex_new, html.find_changes_and_make_diff_of_surrounding_text(doc_old, doc_new), radio == "fast")
            return render_template("x_output_run"+ radio + celex_old + celex_new +".html", celex_new=celex_new, celex_old=celex_old)
        except Exception as e:
            return render_template("error.html", exception= e)
    else:  # HTTP GET
        return render_template("oneLink.html")

@app.route("/celex/", methods=['POST', 'GET'])
def celex():
    "Only enter the CELEX number of the old document."
    if request.method == 'POST':
        try: # fetch input
            celex_input = request.form['celex']
            radio = request.form['btnradio']
            print(radio)
        except Exception as e:
            return render_template("error.html", exception=e)
        try: # run the algorithm
            url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:" + celex_input
            celex_old, doc_old = html.pars_html(url)
            if celex_input != celex_old:
                return render_template("error.html", exception="Error in finding the old and new document! I am sorry!")
            celex_new, doc_new = html.find_newest(url)
            run.process_nlp(radio + celex_old + celex_new, html.find_changes_and_make_diff_of_surrounding_text(doc_old, doc_new), radio == "fast")
            return render_template("x_output_run" + radio + celex_old + celex_new + ".html", celex_new=celex_new, celex_old=celex_old)
        except Exception as e:
            return render_template("error.html", exception=e)
    else:  # HTTP GET
        return render_template("celex.html")

@app.route("/about/")
def about():
    return render_template("about.html")

# match_object = re.match("[a-zA-Z]+", name) TODO safety and securtiy

'''@app.route("/api/data")
def get_data():
    return app.send_static_file("data.json")'''
