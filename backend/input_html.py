import urllib3
from bs4 import BeautifulSoup

http = urllib3.PoolManager()

# Url to the html file (REACH 17.12.2022)
url = 'https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02006R1907-20221217&qid=1680005241428&from=DE'

# Fetch the html file
if url.startswith('http'):
    response = http.urlopen('GET',url)
    html_doc = response.data
else: # local tests
    html_doc = open(url).read()

# Parse and format the html file
parsed_doc = BeautifulSoup(html_doc, 'html.parser').prettify()

print (parsed_doc)