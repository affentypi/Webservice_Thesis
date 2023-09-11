import spacy

nlp = spacy.load("en_core_web_sm")

doc = nlp('3.  This Regulation also lays down provisions on data quality requirements, on a universal message format (UMF), on a central repository for reporting and statistics (CRRS) and on the responsibilities of the Member States and of the European Agency for the operational management of large-scale IT systems in the area of freedom, security and justice (eu-LISA), with respect to the design, development and operation of the interoperability components. This is a test. Does is recognize sentences?')

