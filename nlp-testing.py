#import re # regex
from pathlib import Path

import spacy # spaCy
from spacy import displacy

"----------------------------------"
# spaCy (intro)
nlp = spacy.load("en_core_web_trf")
# https://spacy.io/models/en # ToDo not downloaded

text = "This Regulation, together with Regulation (EU) 2019/818 of the European Parliament and of the Council ( 1 ), establishes a framework to ensure interoperability between the Entry/Exit System (EES), the Visa Information System (VIS), the European Travel Information and Authorisation System (ETIAS), Eurodac, the Schengen Information System (SIS), and the European Criminal Records Information System for third-country nationals (ECRIS-TCN). Jacob is the best Bro, brah brother in the world!"
det_changes = '''['►M1     REGULATION (EU) 2021/1152 OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL\xa0of 7\xa0July 2021    \xa0\xa0L\xa0249   15   14.7.2021       Corrected by:         ', 
'►C1     Corrigendum, OJ\xa0L\xa0010, 15.1.2020, p. \xa04\xa0(2019/817)            ', 
'▼C1    (a)\xa0   in paragraph 1, the following point is inserted:  ‘(db)\xa0Interoperability Advisory Group;’;    ', 
'▼M1   1b.\xa0\xa0 Without prejudice to paragraph 1 of this Article, the ESP shall start operations, for the purposes of the automated verifications pursuant to Article\xa020, Article\xa023, point (c)(ii) of Article\xa024(6), Article\xa041 and point (b) of Article\xa054(1) of Regulation (EU) 2018/1240 only, once the conditions laid down in Article\xa088 of that Regulation have been met.  ']'''

doc = nlp(det_changes)
img_ent = displacy.render(doc, style="ent")
output_path = Path("output/entities_" + "test" + ".html")
output_path.open("w", encoding="utf-8").write(img_ent)

"-------"
# spaCy's tokenization (part of pre-processing)
'''
tokens = [token.text for token in doc] # gimme is one token not two (give me)
print(tokens)
# customize tokens
nlp.tokenizer.add_special_case("gimme", [
    {spacy.symbols.ORTH: "gim"}, # cant be give, because it would modify the text
    {spacy.symbols.ORTH: "me"}
])
doc = nlp(text)
tokens = [token.text for token in doc] # gimme is one token not two (give me)
print(tokens)
'''
"-------"
# spaCy's pipeline
'''
print(nlp.pipeline)
print(nlp.pipe_names)

for token in doc:
    print(token, "::", token.pos_, "::", token.lemma_, "::", token.dep_, "::", spacy.explain(token.dep_)) # token, part-of-speech, lemma (word base), ... || spacy.explain() is important!!!

print(spacy.displacy.render(doc, style="ent")) # displays in HTML (in this case entities)
'''
"-------"
# spaCy's lemmatization (stemming works only with NLTK, Ep10)
'''
# customize lemmas:
ar = nlp.get_pipe('attribute_ruler')
ar.add([[{"TEXT":"Bro"}], [{"TEXT":"Brah"}]], {"LEMMA": "Brother"}) # Gross-Kleinschreibung matters

doc = nlp(text)

for token in doc:
    print(token, token.lemma_)
'''
"-------"
# spaCy's Part of Speech
'''
for token in doc:
    print(token, token.pos_, token.tag_, spacy.explain(token.tag_))

for x,y in doc.count_by(spacy.attrs.POS).items(): # count function (in this case for Parts of speech)
    print(x, doc.vocab[x].text,"Amount:", y)
'''
"-------"
# spaCy's Named Entity Recognition (NER)
'''
for ent in doc.ents:
    print(ent, ent.label_, spacy.explain(ent.label_)) # ent == ent.text

print(nlp.pipe_labels['ner'])
# add a Word as an Entity
span = spacy.tokens.Span(doc, 0, 1, label="ORG")
doc.set_ents([span], default="unmodified")

for ent in doc.ents:
    print(ent.text, ent.label_, spacy.explain(ent.label_)) # ent == ent.text
'''
"-------"
# BagOfWords

# sklearn.feature_extraction.text.CountVectorizer
'''
from sklearn.feature_extraction.text import CountVectorizer

v = CounterVectorizer()

v.fit_transform(list of text/ numpy.ndarray)

# it also has naive_bayer multinomialNB with precision and recall (S2E3)
# sklearn.pipeline as fast machine learning api
'''

"----------------------------------"
# NLTK (intro)

#import nltk # NLTK
#nltk.download('punkt')
#from nltk.tokenize import sent_tokenize, word_tokenize # Tokenizer (StanfordSegmenter f.e.)

#print(sent_tokenize(text))
#print(word_tokenize(text))

"----------------------------------"
#Tutorial: \url{https://www.youtube.com/watch?v=R-AG4-qZs1A&list=PLeo1K3hjS3uuvuAXhYjV2lMEShq2UYSwX}
'''
begin{itemize}
    \item Intro:
    E01: real-life usage: spam filter, auto-correct, language translations, chatbots, search engine (BERT :: sentence embedding), and more;
    E02: hype because of free models (fasttext, TensorFlow hub, GPT3) and OpenSource Ecosystem (Python and libraries).
    \item S01E03: Regex For NLP: matching patterns (can avoid machine learning): Python "import re" and https://regex101.com => information extraction per key-words->key-information.
    \item E04: Techniques for NLP (information extraction): 
    (1) Rules and Heuristics, 
    (2) Machine Learning (statistical), 
    (3) Deep Learing example Hugging Face (sentence transformer/embedder, cosine similarity); 
    Mentioned: count vectorizer is text->numbers, naive bayes classifier(statistical machine learning).
    \item E05: NLP Tasks: 
    (1) Text classification (TF-IDF Vectorizer -> Naive Bayes Classifier); 
    (2) Text similarity (Sentence encoder, cosine similarity); (3) Information extraction (flowchart-screenshot); 
    (4) Information retrieval (TFIDF Score, BERT); 
    (5) Chatbots, (6) \dots
    \item E06: NLP Pipeline: Data Acquisition -> Text Extraction and Cleanup -> Pre-Processing (Sentence Segmentation, Word Tokenization, Stemming and Lemmatization(find word base)) -> Feature Engineering (TF-IDF Vectorizer, OneHot Encoding, Word Embedding);
    Process with Training Data -> MachineLearning(Naive Bayes, SVM, Random Forst) Model Building -> Evaluation (Pre-processing) -> Deployment -> Monitor and Update (Data Acquisition).
    \item E07: Spacy vs. NLTK: both do similar things, but have differences:
    spaCy: object-oriented ("doc.sents" for sentence segmentation); !does not have stemming support!
    NLTK: string processing library (functions to import, like Stanford Segmenter).
    \item E08: Tokenization in spaCy: splitting text into meaningful segments; Example methods: Prefix, Exception, Suffix; more infos on spaCy 101!
    \item E09: SpaCy Language Processing Pipeline (different to standard): see on spaCy 101, small vs large TODO
    \item E10: Stemming and Lemmatization (reduction to base word): based on fixed rules (efficient) or based on linguistic knowledge (accurate) to derive a base word/lemma.
    \item E11: Part Of Speech Tagging: Noun, Verb, Pronoun, Adjective, Adverb, Interjection, Conjunction, Preposition; SpaCy has more! TODO
    \item E12: Named Entity Recognition (NER): finds Entities by name, in SpaCy Small its not perfect! To make own NER: (1) look-up method, (2) rule-based, (3) Machine Learning (Condicitonal Random Fields CRF, BERT).
    \item SEASON 2
    \item S02E1: Text Representation - Basics (FEATURE ENGINEERING): Find features for words (feature vector) and compare them by cosine similarity; the vectors represent text, convertion by (1) One Hot Encoding, (2) Bag of Words, (3) TF-IDF, (4) Word Embeddings.
    \item E2: Text Representation - Label and One Hot Encoding:
\end{itemize}

- Hugging Face (sentence transformer and cosine similarity, NER)

Gensim as well as scikit learn, TensorFlow, PyThorch.'''