import re
from pathlib import Path

import spacy
from spacy import displacy
from spacy.tokens import Span

# Load the model
# nlp = spacy.load("en_blackstone_proto") # does not work! config-file is missing/empty
nlp = spacy.load("en_core_web_sm") # https://spacy.io/usage/spacy-101

def text_strip(text: str):
    """
    param:
    return:
    function:
    """
    # TODO how to replace more/all
    result = (text.replace("\xa0", " ").replace('‘', "'").replace('’', "'")
              .replace(' ̃', "''").replace('▼', " ").replace('►', " ").strip())
    return result

def add_regulations(param_doc: spacy.tokens.doc.Doc): # More Entities todo
    """
    param:
    return:
    function:
    """
    spans = []
    count = 0
    for token in param_doc:
        if re.match("\d{4}/\d{2,4}|\d{2,4}/\d{4}", token.text):
            spans.append(Span(param_doc, count, count + 1, label="REGULATION")) #ToDo Label?
        count += 1
    for span in spans:
        param_doc.set_ents([span], default="unmodified")
    return param_doc

def text_processing_and_rendering(text: str, name: str):
    """
    param:
    return:
    function:
    """
    doc = nlp(text_strip(text))

    img_dep = displacy.render(add_regulations(doc), style="dep")
    output_path = Path("output/dependencies_" + name + ".html")
    output_path.open("w", encoding="utf-8").write(img_dep)
    # ToDo for deployment: output to static ?
    img_ent = displacy.render(add_regulations(doc), style="ent")
    output_path = Path("output/entities_"+ name + ".html")
    output_path.open("w", encoding="utf-8").write(img_ent)
    return
