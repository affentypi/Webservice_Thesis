# to run the backend python code

import backend.html_processing as html
import backend.nlp as nlp

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
file_first = "backend/test_daten/CELEX32019R0817_EN_TXT.html"
file_middle = "backend/test_daten/CELEX02019R0817-20190522_EN_TXT.html" # C: 1 M: 0
file_latest = "backend/test_daten/CELEX02019R0817-20210803_EN_TXT.html" # C: 1 M: 1
# Some Test File
t_old = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32003D0076"
t_middle = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02003D0076-20180510" # M: 2
t_new = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02003D0076-20210811" # M: 2 + 6

result = html.all_in(file_first, file_latest)

def function():
    """
    param:
    return:
    function:
    """
    pass

def process_diff(html_processing_result: list[4]):
    diffs = html_processing_result[3]
    for diff in diffs:
        if "--- \n" in diff and "+++ \n" in diff:
            print("In Diff with " + diff[2] + "Changes:")
        for change in diff[3:]:
            if change.startswith("-"):
                print("REMOVED: " + change[1:])
                nlp.text_processing_and_rendering(change[1:], "removed")
            elif change.startswith("+"):
                print("ADDED: " + change[1:])
                nlp.text_processing_and_rendering(change[1:], "added")
            else:
                print("WHAT?" + change)
    return

process_diff(result)