import difflib
import re
from pathlib import Path
import spacy
from spacy import displacy
from spacy.tokens import Span

import html_processing

def text_strip(text: str):
    """
    param:
    return:
    function:
    """
    # TODO how to replace more/all
    result = (text.replace("\xa0", " ").replace('‘', "'").replace('’', "'")
              .replace(' ̃', "''").replace('▼', " ").replace('►', " ")
              .replace('◄', " ").replace("Corrected by:", " ")
              .replace("Amended by:", " ").strip())
    return result

def add_labels(param_doc: spacy.tokens.doc.Doc): # More Entities todo obsolete?
    """
    param:
    return:
    function:
    """
    spans = []
    count = 0
    for token in param_doc: # todo it does not work
        if re.match('\d{4}/\d{2,4}|\d{2,4}/\d{4}', token.text):
            spans.append(Span(param_doc, count, count + 1, label="LAW"))
        if re.match("Corrigendum|CORRIGENDUM|C\d+$", token.text):
            spans.append(Span(param_doc, count, count + 1, label="CORRIGENDUM"))
        if re.match("Amendment|AMENDMENT|M\d+$|A\d+$", token.text):
            spans.append(Span(param_doc, count, count + 1, label="AMENDMENT"))
        count += 1
    for span in spans:
        param_doc.set_ents([span], default="unmodified")
    return param_doc

def make_diff_great_again(diff):
    """
    param:
    return:
    function:
    """
    modifications = []
    indicator = 13  # 0: same, -1: "-", +1: "+"
    tmp = []
    for modification in diff:
        if modification != " " and modification != "+" and modification != "-" and not modification.startswith(
                "---") and not modification.startswith("+++") and not modification.startswith("@@"):
            if modification.startswith(" "):
                if indicator == 0:
                    if 0 < len(tmp):
                        tmp.append(modification[1:])
                else:
                    modifications.append(" ".join(tmp))
                    indicator = 0
                    tmp = [modification]
            elif modification.startswith("+"):
                if indicator == 1:
                    if 0 < len(tmp):
                        tmp.append(modification[1:])
                else:
                    modifications.append(" ".join(tmp))
                    indicator = 1
                    tmp = [modification]
            elif modification.startswith("-"):
                if indicator == -1:
                    if 0 < len(tmp):
                        tmp.append(modification[1:])
                else:
                    modifications.append(" ".join(tmp))
                    indicator = -1
                    tmp = [modification]
            else:
                print("ERROR, diff has weird stuff in it")
    # todo error with +1. and -1.
    return modifications


def process_changes(file_name, html_processing_result: list[4], spacy_model: bool): #
    """
    param:
    return:
    function:
    """
    if type(html_processing_result[0]) != list and html_processing_result[0] == "REPEALED or no changes!":
        result = """
            {% extends "layout.html" %}
            {% block title %}
                Run
            {% endblock %}
            {% block content %}
            <p>Following modifications were found in <strong> {{ celex_new }} </strong>compared to old <strong> {{ celex_old }} </strong></p>
            <p> The legal act was repealed or there where no changes! </p>
            <p> Please check the files! </p>
            {% endblock %}
            """
        #output_path = Path("templates/x_output_run" + file_name + ".html")
        #output_path.open("w", encoding="utf-8").write(result)
        return None

    # todo elif with if something is empty!

    if spacy_model is False:
        nlp = spacy.load("en_core_web_trf")
    else:
        nlp = spacy.load("en_core_web_sm")  # https://spacy.io/usage/spacy-101

    config = {
        "phrase_matcher_attr": None,
        "validate": True,
        "overwrite_ents": True,
        "ent_id_sep": "||",
    }
    ruler = nlp.add_pipe("entity_ruler", config=config)
    patterns = [{"label": "ORG", "pattern": {"TEXT": "EU"}},
                {"label": "LAW", "pattern": [{"TEXT": {"REGEX": "\d{4}/\d{2,4}|\d{2,4}/\d{4}"}}]},
                {"label": "LAW", "pattern": [{"ORTH": "OJ", "OP": "?"}, {"ORTH": "L"}, {"SHAPE": "ddd"}]},
                {"label": "LAW", "pattern": [{"LOWER": "paragraph"}, {"SHAPE": "d", "OP": "+"}]},
                {"label": "LAW", "pattern": [{"LOWER": "Article"}, {"SHAPE": "d", "OP": "+"}, {"ORTH": "(", "OP": "?"}, {}, {"ORTH": ")", "OP": "?"} ]},
                {"label": "LAW", "pattern": [{"LOWER": "point"}, {"SHAPE": "d", "OP": "+"}]},
                {"label": "LAW", "pattern": [{"LOWER": "point"}, {"ORTH": "("}, {}, {"ORTH": ")"} ]},
                ]
    ruler.add_patterns(patterns)

    mods_name = html_processing_result[0]
    mods_content = html_processing_result[1]
    mods_position = html_processing_result[2]
    diffs = html_processing_result[3]
    count = 0
    changes_names = [] # [change_name, meta, mod[operator, content, position, comparison]]
    changes_tupels = []
    while count < len(mods_name) and count < len(mods_content) and count < len(mods_position): # General safety test
        "change name"
        name = mods_name[count]
        if "\xa0—————" in name: # Deletion
            name = name.replace("\xa0—————", "")
        change_index = -1 #todo remove?
        if name in changes_names:
            change_index = changes_names.index(name)
        else:
            if not changes_names:
                changes_tupels.append([])
                changes_names.append(name)
                change_index = 0
            else:
                changes_tupels.append([])
                changes_names.append(name)
                change_index = changes_names.index(name)
        "modification operator"
        operator = "DEFAULT"
        "modification content"
        content = mods_content[count]
        if "◄" in content: # the end of little addings
            p = content.find("◄")
            content = content[:p + 1]
            operator = "Insertion"
        elif "\xa0—————" in content:
            content = content[:content.find("\xa0—————") + 7]
            operator = "Deletion"
        content = text_strip(content.replace(name, ""))
        c_len = len(content) #todo remove?
        "modification position"
        position = mods_position[count]
        "modification old vs. new"
        modifications = []
        word_diff = []
        if position == "":
            position = "Meta-Data"
            operator = position
        else:
            "modification old vs. new"
            possible_diffs = []
            print(f">>> Name: {name}, Position: {position}, Content: {content}")
            for diff in diffs[1:]:
                if "+▼" + name in diff or "+►" + name in diff:
                    if make_diff_great_again(diff) not in possible_diffs:
                        possible_diffs.append(make_diff_great_again(diff))
                elif "+▼" + name + "\xa0—————" in diff or "+►" + name + "\xa0—————" in diff:
                    operator = "Deletion"
                    if make_diff_great_again(diff) not in possible_diffs:
                        possible_diffs.append(make_diff_great_again(diff))
            for diff in possible_diffs:
                for part in diff:
                    part = text_strip(part)
                    if content in part or part in content and operator != "Deletion":
                        modifications = diff
                        break
                    elif position in part and operator == "Deletion":
                        modifications = diff
                        break
            arrow_index = []
            same_indicis = []
            index = 0
            for mod in modifications:
                if "▼" in mod or "►" in mod or "◄" in mod: # ▼ ► ◄
                    arrow_index.append(index)
                if mod.startswith(" "):
                    same_indicis.append(index)
                index += 1
            frame = [0, len(modifications)]
            indexed = True
            if len(arrow_index) == 1:
                for i in same_indicis:
                    if arrow_index[0] > i > frame[0]:
                        frame[0] = i
                    elif arrow_index[0] < i < frame[1]:
                        frame[1] = i
            elif len(arrow_index) == 2:
                for i in same_indicis:
                    if arrow_index[0] > i > frame[0]:
                        frame[0] = i
                    elif arrow_index[1] < i < frame[1]:
                        frame[1] = i
            elif len(arrow_index) > 2:
                for i in same_indicis:
                    if arrow_index[0] > i > frame[0]:
                        frame[0] = i
                    elif arrow_index[-1] < i < frame[1]:
                        frame[1] = i
            else:
                print("no indicis")
                indexed = False
            if operator == "Deletion":
                word_diff = modifications[frame[0]:frame[1]]
            elif indexed:
                plus = []
                minus = []
                for mod in modifications[frame[0]:frame[1]]:
                    if mod.startswith("+"):
                        plus.append(mod[1:])
                    elif mod.startswith("-"):
                        minus.append(mod[1:])
                    else: #todo help?
                        word_diff.append(mod)
                tmp = make_diff_great_again(list(difflib.unified_diff(text_strip(" ".join(minus)).split(" "), text_strip(" ".join(plus)).split(" "))))
                for t in tmp:
                    if t not in word_diff:
                        word_diff.append(t)
            else:
                word_diff = modifications
        print(f">>> diff: {word_diff}")
        '''print("> NLP Processing -----------------------")
        print(f"Name: {name}")
        print(f"Position: {position}")
        print(f"Operator: {operator}")
        print(f"Content: {content}")
        print(f"Word-Diff: {word_diff}")
        print("nlp< -----------------------")'''
        changes_tupels[change_index].append([name, operator, content, position, word_diff])

        count += 1
    amount_modifications = len(mods_content) - len(changes_names)
    result = ["""
            {% extends "layout.html" %}
            {% block title %}
                Run
            {% endblock %}
            {% block content %}
            <p>Following modifications were found in <strong> {{ celex_new }} </strong>compared to old <strong> {{ celex_old }} </strong></p>
            <p> There are """ + amount_modifications.__str__() + """ modifications found!</p>
            <div class="accordion" id="changes">
            """]
    for cn in changes_names:
        tupels = changes_tupels[changes_names.index(cn)]
        amount_mods = len(tupels)
        for t in tupels:
            if "Meta-Data" in t:
                amount_mods -= 1
        result.append('''
            <div class="accordion-item">
            <h2 class="accordion-header">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#''' + cn + '''" aria-expanded="false" aria-controls="''' + cn + '''">
            <strong> ''' + cn + " </strong> with <strong> " + amount_mods.__str__() + " </strong> Modifications"
            "</button>"
            "</h2>"
            '''<div id="''' + cn + '''" class="accordion-collapse collapse" data-bs-parent="#changes">
                <div class="accordion-body">''')
        for tuple in tupels: # [name(0), operator(1), content(2), position(3), word_diff(4)]
            if tuple[0] != cn:
                print("ERROR: wrong tuple")
                break
            if "—————" in tuple[2]:
                ents = tuple[2]
            else:
                doc = nlp(tuple[2])
                ents = displacy.render(doc, style="ent")
            result.append('''
                                    <div class="card">
                                    <div class="card-body">
                                    <strong>'''
                          + tuple[1] + "</strong> in <strong>" + tuple[3] + "</strong>" + ents
                          )
            old = ""
            for word in tuple[4]:
                if word.startswith(" "):
                    old = old + '''<div class="text-black-50">''' + word[1:] + '''</div>'''
                elif word.startswith("+"):
                    old = old + '''<p style="color:green;">''' + word[1:] + '''</p>'''
                elif word.startswith("-"):
                    old = old + '''<p style="color:red;">''' + word[1:] + '''</p>'''
            if tuple[3] != "Meta-Data":
                result.append('''
                        <p> <strong> the corresponding passage: </strong></p> 
                        <br>
                        ''' + old)
            result.append('''</div>
                          </div>
                              ''')

        result.append('''
              </div>
            </div>
          </div>''')

    result.append("""
    </div>
    {% endblock %}
        """)

    #output_path = Path("templates/x_output_run" + file_name + ".html")
    #output_path.open("w", encoding="utf-8").write("".join(result))

    return changes_names, changes_tupels

### Debugging:
# Big file:
# URL to the html file (REACH 17.12.2022)
reach_url_new = 'https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02006R1907-20221217&from=EN'
# URL to the old html file (REACH 06.03.2013)
reach_url_old = 'https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02006R1907-20130306&from=EN'
# Small file:
# URL to online html file (32019R0817)
url_first = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019R0817&from=DE"
url_middle = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02019R0817-20190522&from=DE" # C: 1 M: 0
url_latest = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A02019R0817-20210803&from=DE" # C: 1 M: 1
# Path to local html file (32019R0817)
file_first = "test_data/CELEX32019R0817_EN_TXT.html"
file_middle = "test_data/CELEX02019R0817-20190522_EN_TXT.html"  # C: 1 M: 0
file_latest = "test_data/CELEX02019R0817-20210803_EN_TXT.html"  # C: 1 M: 1
# Some Test File
t_old = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32003D0076"
t_middle = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02003D0076-20180510" # M: 2
t_new = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02003D0076-20210811" # M: 2 + 6
# One Link Text File (and Deleted TEST)
test_one_link = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32013R0347"
#test_one_link = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02013R0347-20220428" # M: 0 + 0 + 0 + 1 + 1 + 0 + 1

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------

""" Nested Modifications and Weird Arrows are found! Not fixable?
stuff_old = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:31997S2136"
stuff_new = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:01997S2136-20011215"
result = "C: 0 ; M: 1 ;"
"""

# fails

stuff_old = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:31997S2136"
stuff_new = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:01997S2136-20011215"
result = "C: 0 ; M: 1 ;"

r = html_processing.find_changes_and_make_diff_of_surrounding_text(html_processing.pars_html(stuff_old)[1], html_processing.pars_html(stuff_new)[1])

#r = html_processing.find_changes_and_make_diff_of_surrounding_text(html_processing.pars_html(url_first)[1], html_processing.pars_html(url_latest)[1])
#r = html_processing.find_changes_and_make_diff_of_surrounding_text(html_processing.pars_html(test_one_link)[1], html_processing.find_newest(test_one_link)[1])
#r = html_processing.find_changes_and_make_diff_of_surrounding_text(html_processing.pars_html(t_old)[1], html_processing.pars_html(t_new)[1])
stuff = process_changes("test", r, True)

expected_cs = result.split(";")[0].replace("C: ", "").split("+")
expected_cs_changes = len(expected_cs)
expected_cs_mods_per_changes = []
for ecs in expected_cs:
    expected_cs_mods_per_changes.append(int(ecs))
    if int(ecs) == 0:
        expected_cs_changes -= 1

expected_ms = result.split(";")[1].replace("M: ", "").split("+")
expected_ms_changes = len(expected_ms)
expected_ms_mods_per_changes = []
for ems in expected_ms:
    expected_ms_mods_per_changes.append(int(ems))
    if int(ems) == 0:
        expected_ms_changes -= 1

overall_changes = 0
for modcs in expected_cs_mods_per_changes:
    overall_changes += modcs
for modms in expected_ms_mods_per_changes:
    overall_changes += modms

print(f"C: {expected_cs_changes} and Modifications per Changes = {expected_cs_mods_per_changes}")
print(f"M: {expected_ms_changes} and Modifications per Changes = {expected_ms_mods_per_changes}")
print(f"Overall there are {overall_changes} expected!")
print(stuff[0])
print(overall_changes)
overall_found_changes = 0
for rs in stuff[1]:
    overall_found_changes += len(rs)
overall_found_changes -= len(stuff[1])
print(overall_found_changes)
found_ms_changes = 0
found_cs_changes = 0
for sname in stuff[0]:
    if sname.startswith("A") or sname.startswith("M"):
        found_ms_changes += 1
    if sname.startswith("C"):
        found_cs_changes += 1
print(found_ms_changes == expected_ms_changes)
print(found_cs_changes == expected_cs_changes)
print(len(stuff[0]) == expected_ms_changes + expected_cs_changes)
print(len(stuff[1]) == expected_ms_changes + expected_cs_changes)
print(overall_found_changes == overall_changes)
