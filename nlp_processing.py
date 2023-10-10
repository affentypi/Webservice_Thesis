import re
from pathlib import Path
import spacy
from spacy import displacy
from spacy.tokens import Span
import spacy_universal_sentence_encoder

import html_processing

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
test_one_link = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02013R0347-20220428" # M: 0 + 0 + 0 + 1 + 1 + 0 + 1


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

def add_labels(param_doc: spacy.tokens.doc.Doc): # More Entities todo
    """
    param:
    return:
    function:
    """
    spans = []
    count = 0
    for token in param_doc: # todo it does not work
        if re.match('\d{4}/\d{2,4}|\d{2,4}/\d{4}|L\s\d{2,4}|paragraph\s\d+', token.text):
            spans.append(Span(param_doc, count, count + 1, label="LAW"))
        if re.match("Corrigendum|CORRIGENDUM|C\d+$|C\s\d+$", token.text):
            spans.append(Span(param_doc, count, count + 1, label="CORRIGENDUM"))
        if re.match("Amendment|AMENDMENT|M\d+$|M\s\d+$|A\d+$|A\s\d+$", token.text):
            spans.append(Span(param_doc, count, count + 1, label="AMENDMENT"))
        count += 1
    for span in spans:
        param_doc.set_ents([span], default="unmodified")
    return param_doc

def find_old_passage(a, r, content):
    """
    param:
    return:
    function:
    """
    result = ""
    sentence_encoder = spacy_universal_sentence_encoder.load_model('en_use_lg')
    doc_c = sentence_encoder(text_strip(content))
    doc_a = sentence_encoder(a)
    sent_a = []  # not .text for similarity test
    doc_r = sentence_encoder(r)
    sent_r = []  # .teext for concat
    frame = [0, 0]

    c = 0
    start = -1
    end = -1
    first = True
    for sent in doc_a.sents:
        sent_a.append(sent)
        if "▼" in sent.text or "►" in sent.text or "◄" in sent.text:
            if first:
                start = c
                first = False
            else:
                end = c
        c += 1
    if start > 0:
        frame[0] = sent_a[start - 1]
    elif start == 0:
        frame[0] = sent_a[start]
    else: # error
        print("Error start")
    if end == -1:
        frame[1] = sent_a[start + 1]
    elif end < len(sent_a) - 1:
        frame[1] = sent_a[end + 1]
    elif end < len(sent_a):
        frame[1] = sent_a[end]
    else: # error
        print("Error end")
    c = 0
    start = -1
    end = -1
    found = False
    finish = False
    for sent in doc_r.sents:
        sent_r.append(sent.text)
        if sent.similarity(doc_c) > 0.7: # updated / corrected
            print("AN UPDATED/CORRECTION")
            return sent.text
        if len(sent) > 2 * len(doc_c): # if the content is a part of a sentence
            for s in range(len(sent) - len(doc_c)):
                p = sent[s : s + len(doc_c)]
                if p.similarity(doc_c) > 0.7:  # updated / corrected
                    print("AN UPDATED/CORRECTION")
                    return p.text
        if sent.similarity(frame[0]) > 0.9 and not found:
            start = c
            found = True
        if sent.similarity(frame[1]) > 0.9 and not finish:
            end = c
            finish = True
        c += 1

    if found:
        if end < 0:
            end = len(sent_r) - 1
        if start < 0:
            print("START NOT FOUND")
        if 0 < start < end < len(sent_r) - 2:
            result = "\n".join(sent_r[start - 1 : end + 1])
        elif 0 < start < end < len(sent_r):
            result = "\n".join(sent_r[start : end])
        else:
            print("weird error")
    else:
        print("Help")
    return result

def process_changes(html_processing_result: list[4], spacy_model: bool): # # [change_name, change_content, change_position, diffs]
    """
    param:
    return:
    function:
    """

    if spacy_model is False:
        nlp = spacy.load("en_core_web_trf") #todo does not work
    else:
        nlp = spacy.load("en_core_web_sm")  # https://spacy.io/usage/spacy-101 #todo
    result = ["""
{% extends "layout.html" %}
{% block title %}
    Run
{% endblock %}
{% block content %}
    <p>Following things were found</p>
<div class="accordion" id="changes">
"""]
    change_name = html_processing_result[0]
    change_content = html_processing_result[1]
    change_position = html_processing_result[2]
    diffs = html_processing_result[3]
    added = []
    removed = []
    old = ""
    for diff in diffs:
        if "--- \n" in diff and "+++ \n" in diff:
            print("Diff with " + diff[2]) #ToDo Footnotes that are shifted
            pass
        for change in diff[3:]:
            print(change)
            '''if change.startswith("-"):
                removed.append(change[1:])
            elif change.startswith("+"):
                added.append(change[1:])
            else:
                print("WHAT?" + change)  # todo error?'''
    # ▼ ► ◄
    count = 0
    while count < len(change_name) and count < len(change_content) and count < len(change_position): # General safety test
        name = change_name[count]
        if "\xa0—————" in name: # Deletion
            name = name.replace("\xa0—————", "")
        content = change_content[count]
        if "◄" in content: # the end of little addings
            p = content.find("◄")
            content = content[:p + 1]
        elif "\xa0—————" in content:
            content = content[:content.find("\xa0—————") + 7]
        c_len = len(content)
        position = change_position[count]

        print("--------------------------------------------")
        print(name)
        print(content)
        print(position)
        if position == "":
            position = "Tabel of content"
            print("Tabel of content")
        else:
            for a in added:
                if ("▼" + name in a or "►" + name in a) and "Amended by:" not in a and "Corrected by:" not in a :
                    r = removed[added.index(a)]
                    a_pos = a.find(content)
                    if a[a_pos : a_pos + c_len] != content:
                        print("ERROR: CONTENT NOT FOUND")
                    print("NEW: " + a)
                    print("OLD: " + r)

                    #old = find_old_passage(a, r, content)
                    #print(old)

        doc = nlp(text_strip(content))
        ents = displacy.render(add_labels(doc), style="ent")
        result.append('''
        <div class="accordion-item">
            <h2 class="accordion-header">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#''' + name + '''" aria-expanded="false" aria-controls="''' + name + '''">
        ''' + name + '''
      </button>
    </h2>
    <div id="''' + name + '''" class="accordion-collapse collapse" data-bs-parent="#accordionExample">
      <div class="accordion-body">
        <strong>''' + position + '''</strong> 
        <br>
        ''' + ents )
        if position != "Tabel of content":
            result.append('''
            <strong> the corresponding old passage: </strong> 
            <br>
            ''' + '''<div class="text-black-50">... ''' + old + ''' ...</div>''')
        result.append('''
      </div>
    </div>
  </div>''')

        print("--------------------------------------------")

        count += 1

    result.append("""
</div>
{% endblock %}
    """)

    output_path = Path("templates/run.html")
    output_path.open("w", encoding="utf-8").write("".join(result))

    return

process_changes(html_processing.all_in(url_first, url_latest), True)