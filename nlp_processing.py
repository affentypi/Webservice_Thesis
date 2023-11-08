import difflib
import re
from pathlib import Path
import spacy
from spacy import displacy
from spacy.tokens import Span

import html_processing

def add_labels(param_doc: spacy.tokens.doc.Doc): # More Entities todo obsolete?
    """
    param:
    return:
    function:
    """
    spans = []
    count = 0
    for token in param_doc: # todo it does not work / implement in patterns
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
    param: a diff
    return: a better diff
    function: parts with prefix (" ", "+", "-") that follow each other are combined to one part. Meaning a list of [" ", "+", "+", " ", "-", "-", "-", "+"] is compacted to [" ", "+", " ", "-", "+"] while still containing all the data.
    """
    modifications = []
    indicator = 13  # 0: same, -1: "-", +1: "+"
    tmp = []
    for modification in diff:
        "To sort out the controller parts from difflib of the diff list."
        if modification != " " and modification != "+" and modification != "-" and not modification.startswith(
                "---") and not modification.startswith("+++") and not modification.startswith("@@"):
            if modification.startswith(" "):
                "If the previous part had the same indicator."
                if indicator == 0 and tmp:
                    tmp.append(modification[1:])
                else:
                    "If the previous part had a added or remove indicator, all previous entries are put together and appended, the indicator is set to same and the tmp-list is restarted."
                    modifications.append(" ".join(tmp))
                    indicator = 0
                    tmp = [modification] # Important to keep the first char as prefix!
            elif modification.startswith("+"):
                "Repeat for added!"
                if indicator == 1 and tmp:
                    tmp.append(modification[1:])
                else:
                    modifications.append(" ".join(tmp))
                    indicator = 1
                    tmp = [modification]
            elif modification.startswith("-"):
                "Repeat for remove!"
                if indicator == -1 and tmp:
                    tmp.append(modification[1:])
                else:
                    modifications.append(" ".join(tmp))
                    indicator = -1
                    tmp = [modification]
            else:
                #print("ERROR, diff has weird stuff in it") # todo fails at: 32019R2033, 32013R0883, 32013R1308, ...? -> still works
                pass
    return modifications

def process_nlp(file_name, html_processing_result: list[4], spacy_model: bool):
    """
    param: the file name for the HTML output, the html-processing-result with [changes_name, change_content, change_position, diffs] and a boolean indicating fast (True) or accurate (False).
    return: a list of change_names [M1, M3, ...] and a list aligning with these indicis containing all modifications to the change and their "data" = [name, operator, position, content, processed_content, word_diff].
    function: this "data" is collected and processed by iterating through the html-processing-result.
    """
    "Early Return for Repeals and Errors!"
    if type(html_processing_result[0]) != list and html_processing_result[0] == "REPEALED or no changes!":
        result = """
            {% extends "layout.html" %}
            {% block title %}
                Run
            {% endblock %}
            {% block content %}
            <p>Following modifications were found in <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{{ celex_new }}"> {{ celex_new }} </a> compared to old <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{{ celex_old }}"> {{ celex_old }} </a></p>
            <p> The legal act was repealed or there where no changes! </p>
            <p> Please check the files! </p>
            {% endblock %}
            """
        output_path = Path("templates/x_output_run" + file_name + ".html")
        output_path.open("w", encoding="utf-8").write(result)
        return None

    "Set Up for the NLP!"
    if spacy_model is False:
        nlp = spacy.load("en_core_web_trf") # accurate
    else: # https://spacy.io/usage/spacy-101
        nlp = spacy.load("en_core_web_sm")  # fast

    config = {
        "phrase_matcher_attr": None,
        "validate": True,
        "overwrite_ents": True, # overwrite_ents is very important!
        "ent_id_sep": "||",
    }
    "This contains the NLP Patterns which are used for the rule-based information extraction."
    ruler = nlp.add_pipe("entity_ruler", config=config)
    patterns = [{"label": "ORG", "pattern": {"TEXT": "EU"}},
                {"label": "ORG", "pattern": {"LOWER": "council"}},
                {"label": "ORG", "pattern": {"LOWER": "commission"}},
                {"label": "ORG", "pattern": [{"LOWER": "european"}, {"LOWER": "parliament"}]},
                {"label": "LAW", "pattern": [{"TEXT": {"REGEX": "\d{4}/\d{2,4}|\d{2,4}/\d{4}"}}]},
                {"label": "LAW", "pattern": [{"TEXT": {"REGEX": "Amendment|AMENDMENT|M\d+$|A\d+$"}}]}, #todo rename in change?
                {"label": "LAW", "pattern": [{"TEXT": {"REGEX": "Corrigendum|CORRIGENDUM|C\d+$"}}]},
                {"label": "LAW", "pattern": [{"ORTH": "OJ", "OP": "?"}, {"ORTH": "L"}, {"SHAPE": "ddd"}]},
                {"label": "LAW", "pattern": [{"LOWER": "paragraph"}, {"SHAPE": "d", "OP": "+"}]},
                {"label": "LAW", "pattern": [{"LOWER": "Article"}, {"SHAPE": "d", "OP": "+"}, {"ORTH": "(", "OP": "?"}, {}, {"ORTH": ")", "OP": "?"} ]},
                {"label": "LAW", "pattern": [{"LOWER": "point"}, {"SHAPE": "d", "OP": "+"}]},
                {"label": "LAW", "pattern": [{"LOWER": "point"}, {"ORTH": "("}, {}, {"ORTH": ")"} ]},
                {"label": "LAW", "pattern": [{"TEXT": {"REGEX": "\d{4}/\d{2,4}|\d{2,4}/\d{4}"}}]}
                ]
    ruler.add_patterns(patterns)
    # [org, law, date, gpe, norp, loc, language, money, quantity] (the only outputted ents)
    colors = {"ORG": "linear-gradient(90deg, #aa9cfc, #7aecec)", "LAW": "linear-gradient(90deg, #aa9cfc, #ff8197)", "DATE": "linear-gradient(90deg, #e49ce7, #bfe1d9)",
                "GPE": "linear-gradient(90deg, #aa5abe, #feca74)", "NORP": "linear-gradient(90deg, #aa77ff, #feca74)", "LOC": "linear-gradient(90deg, #aaa5eb, #feca74)",
              "QUANTITY": "linear-gradient(90deg, #e49ce7, #e4e7d2)", "MONEY": "linear-gradient(90deg, #e49ce7, #face69)", "LANGUAGE": "linear-gradient(90deg, #aa9cfc, #fc9ce7)"}
    options = {"ents": ["ORG", "LAW", "DATE", "GPE", "NORP", "LOC", "QUANTITY", "MONEY", "LANGUAGE"], "colors": colors}

    mods_name = html_processing_result[0]
    mods_content = html_processing_result[1]
    mods_position = html_processing_result[2]
    diffs = html_processing_result[3]
    count = 0
    "results" #todo fixate
    changes_names = []
    changes_tupels = []
    while count < len(mods_name) and count < len(mods_content) and count < len(mods_position): # General safety test
        "The change name for this modification is made!" #todo url appendix by the number of modifications in the change to give direct links to the documents (future work)
        name = mods_name[count]
        if "\xa0—————" in name: # to sill align the modification to the right change!
            name = name.replace("\xa0—————", "")
        if name in changes_names:
            "Modification is appended to the right change list."
            change_index = changes_names.index(name)
        else:
            "If the change list does not exist a new one is created."
            if not changes_names:
                changes_tupels.append([])
                changes_names.append(name)
                change_index = 0
            else:
                changes_tupels.append([])
                changes_names.append(name)
                change_index = changes_names.index(name)
        "Operator starts to include early recognition of deletion."
        operator = "DEFAULT"
        "The content is cut to the right content (if more follows) and deletion can already be detected. This content is (if not empty) processed by NLP."
        content = mods_content[count]
        inserted = False
        if "►" in content and "◄" in content: # the end of little insertions
            p = content.find("◄")
            content = content[:p + 1]
            inserted = True
        if "—————" in content:
            content = content[:content.find("—————") + 7]
            if inserted:
                operator = "Inserted Deletion"
            else:
                operator = "Deletion"
        "The content is processed by NLP which was set up earlier."
        processed_content = nlp(content)
        "The position of the modification (last pointer)"
        position = mods_position[count]
        "Further processing the diff by making a word level diff (instead of the line level from before)"
        diff = make_diff_great_again(diffs[count])
        word_diff = []
        if position == "": # table of content
            position = "the Start of the Document"
            operator = "Meta-Data"
        else:
            """The following part scans through the diff and if the right modification is found (with the arrow and the name) the parts until the last same-part are appended for context
             and starting with the end of the modification the rest until the last same-part is append, to limit the word-diff to the interesting part (plus context). If a modification of the
             same change is in there two times, both will be displayed.""" # todo both out by content (<- fails)
            start = False # modification started
            terminate = False # the modification is over
            last_same = 0 # the index of the last "same" part to include it in front of the start for context
            index = 0
            for mod in diff:
                if mod.startswith(" "):
                    last_same = index
                    if terminate:
                        word_diff.append(mod)
                        terminate = False
                        start = False
                    elif start:
                        word_diff.append(mod)
                elif mod.startswith("+"):
                    " End "
                    if "▼" in mod and start:
                        word_diff.append(mod)
                        terminate = True
                    elif "◄" in mod and start:
                        word_diff.append(mod)
                        terminate = True
                    elif start:
                        word_diff.append(mod)
                    " Start "
                    if "▼" + name in mod and not start:
                        if mod.count("▼") != 2: # ends in the same part
                            start = True
                        for part in diff[last_same:index]: # the context
                            word_diff.append(part)
                        word_diff.append(mod)
                    if "►" + name in mod and not start:
                        if "◄" not in mod: # ends in the same part
                            start = True
                        for part in diff[last_same:index]: # the context
                            word_diff.append(part)
                        word_diff.append(mod)
                elif start: # append everything inbetween start and terminate
                    word_diff.append(mod)
                index += 1
            if not word_diff: # some diffs are already small
                word_diff = diff

            finished_diff = []
            plus = []
            plus_count = 0
            minus = []
            minus_count = 0
            "Putting the diff parts together to get two list ready for a diff."
            for part in word_diff:
                if part.startswith("+"):
                    plus.append(part.replace("\xa0", " "))
                    plus_count += 1
                elif part.startswith("-"):
                    minus.append(part.replace("\xa0", " "))
                    minus_count += 1
                elif part.startswith(" "):
                    plus.append(part.replace("\xa0", " "))
                    minus.append(part.replace("\xa0", " "))

            "Removing the prefixes."
            for p in plus:
                p = p[1:]
            for m in minus:
                m = m[1:]
            "Making the diff! If only same-parts are in one of the lists, the other list is used as word diff."
            if plus_count > 0 and minus_count > 0:
                # tmp = make_diff_great_again(list(difflib.unified_diff(" ".join(minus).split(" "), " ".join(plus).split(" ")))) (unified is wrong!)
                tmp = list(difflib.Differ().compare(" ".join(minus).split(" "), " ".join(plus).split(" ")))
                finished_diff = make_diff_great_again(tmp)
            elif plus_count > 0:
                finished_diff = plus
            elif minus_count > 0:
                finished_diff = minus
            else:
                print("what?") # todo found: 32013R0345, 32013R0346, ...? -> still works
            word_diff = finished_diff

            "The operator is set by the count of added and removed. Some Additions (very exceptional) remove little parts (like a end signature) so is the pluses are far more, its still an addition."
            pluses = 0
            minuses = 0
            for mod in word_diff:
                if mod.startswith("+"):
                    pluses += 1
                elif mod.startswith("-"):
                    minuses += 1
            if operator == "Inserted Deletion" or operator == "Deletion":
                pass
            elif minuses == 0:
                if inserted:
                    operator = "Inserted Addition"
                else:
                    operator = "Addition"
            elif pluses == 0:
                if inserted:
                    operator = "Inserted Deletion"
                else:
                    operator = "Deletion"
            elif minuses * 13 < pluses: # for little deletion
                if inserted:
                    operator = "Inserted Addition"
                else:
                    operator = "Addition"
            else:
                if inserted:
                    operator = "Inserted Replacement"
                else:
                    operator = "Replacement"

        "Debugging Console Print Out"
        '''print("> NLP Processing -----------------------")
        print(f"Name: {name}")
        print(f"Position: {position}")
        print(f"Operator: {operator}")
        print(f"Content: {content}")
        print(f"Word-Diff: {word_diff}")
        print("nlp< -----------------------")'''
        changes_tupels[change_index].append([name, operator, position, content, processed_content, word_diff])

        count += 1

    "For testing to improve runtime and not create all the HTML files:"
    #return changes_names, changes_tupels

    " HTML output "
    amount_modifications = len(mods_content) - len(changes_names)
    "Making a result-string, which later can be written as HTML file."
    result = ["""
            {% extends "layout.html" %}
            {% block title %}
                Run
            {% endblock %}
            {% block content %}
            <p>Following modifications were found in <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{{ celex_new }}"> {{ celex_new }} </a> compared to old <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{{ celex_old }}"> {{ celex_old }} </a></p>
            <p> There are """ + amount_modifications.__str__() + """ modifications found!</p>
            <div class="accordion" id="changes">
            """]
    for cn in changes_names: # iterate through the changes, because the output is sorted by changes with all modification of each change put together
        tupels = changes_tupels[changes_names.index(cn)]
        amount_mods = len(tupels)
        for t in tupels:
            if "Meta-Data" in t:
                amount_mods -= 1
                break # because title and intro is also labeled as "Meta-Data"
        result.append('''
            <div class="accordion-item">
            <h2 class="accordion-header">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#''' + cn + '''" aria-expanded="false" aria-controls="''' + cn + '''">
            <strong> ''' + cn + " </strong> with <strong> " + amount_mods.__str__() + " </strong> Modifications"
            "</button>"
            "</h2>"
            '''<div id="''' + cn + '''" class="accordion-collapse collapse" data-bs-parent="#changes">
                <div class="accordion-body">''')
        for tuple in tupels:
            # [name (0), operator (1), position (2), content (3), processed_content (4), word_diff (5)]
            if tuple[0] != cn:
                print("ERROR: wrong tuple")
                break
            ents = displacy.render(tuple[4], style="ent", options=options)  # fails for some files
            result.append('''
                                    <div class="card">
                                    <div class="card-body">
                                    <strong>'''
                          + tuple[1] + "</strong> in <strong>" + tuple[2] + "</strong>" + ents
                          )
            old = ""
            for word in tuple[5]: # making the diff into colored HTML text
                if word.startswith(" "):
                    old = old + '''<div class="text-black-50">''' + word[1:] + '''</div>'''
                elif word.startswith("+"):
                    old = old + '''<p style="color:green;">''' + word[1:] + '''</p>'''
                elif word.startswith("-"):
                    old = old + '''<p style="color:red;">''' + word[1:] + '''</p>'''
            if tuple[1] != "Meta-Data": # todo title and intro would also need the diff ...
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

    "Writing the file (with the file name) so flask can render the right .html by using the file name it sets itself."
    output_path = Path("templates/x_output_run" + file_name + ".html")
    output_path.open("w", encoding="utf-8").write("".join(result))

    return changes_names, changes_tupels

### Debugging:
# URL to online html file (32019R0817)
url_first = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019R0817&from=DE"
url_middle = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02019R0817-20190522&from=DE" # C: 1 M: 0
url_latest = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A02019R0817-20210803&from=DE" # C: 1 M: 1
# Path to local html file (32019R0817)
file_first = "test_data/CELEX32019R0817_EN_TXT.html"
file_middle = "test_data/CELEX02019R0817-20190522_EN_TXT.html"  # C: 1 M: 0
file_latest = "test_data/CELEX02019R0817-20210803_EN_TXT.html"  # C: 1 M: 1

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------

'''stuff_old = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:31997S1401"
stuff_new = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:01997S1401-19981004"
result = "C: 2 ; M: 1 ;"

r = html_processing.find_changes_and_make_diff_of_surrounding_text(html_processing.pars_html(stuff_old)[1], html_processing.pars_html(stuff_new)[1])

#r = html_processing.find_changes_and_make_diff_of_surrounding_text(html_processing.pars_html(url_first)[1], html_processing.pars_html(url_latest)[1])
#r = html_processing.find_changes_and_make_diff_of_surrounding_text(html_processing.pars_html(test_one_link)[1], html_processing.find_newest(test_one_link)[1])
#r = html_processing.find_changes_and_make_diff_of_surrounding_text(html_processing.pars_html(t_old)[1], html_processing.pars_html(t_new)[1])
stuff = process_nlp("test", r, True)
#print(stuff[1][1][1][4])
#print(displacy.render(stuff[1][1][1][4], style="ent"))
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
#print(overall_changes)
overall_found_changes = 0
for rs in stuff[1]:
    overall_found_changes += len(rs)
overall_found_changes -= len(stuff[1])
#print(overall_found_changes)
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
print(overall_found_changes)
print(overall_changes)
print(overall_found_changes == overall_changes)'''
