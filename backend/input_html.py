import datetime
import difflib
import urllib3
from bs4 import BeautifulSoup

def pars_html(url):
    """
    param: a URL in either HTTP format or a local file-path.
    return: a Beautiful Soup parsed HTML document.
    function: via urllib3 a pool manager is started and the URL is opened and the file is fetched. If no URL is entered, the local file is opened and read.
    """
    http = urllib3.PoolManager()

    print(url)
    # Fetch the html file via URL
    if url.startswith('http'):
        response = http.urlopen('GET',url)
        html_doc = response.data
    else: # local tests
        html_doc = open(url).read()

    # Parse and format the html file using bs4
    parsed_doc = BeautifulSoup(html_doc, 'html.parser')

    return parsed_doc

def print_out(parsed_doc):
    """
    param: a Beautiful Soup parsed html document.
    function: prints out the HTML document in "prettified" form on the console.
    """
    print(parsed_doc.prettify())

def make_diff(parsed_doc_old, parsed_doc_new):
    '''
        param: an old and a new Beautiful Soup parsed HTML document.
        return: a list containing the diff (added starts with "+" and deleted starts with "-").
        function: all the differences between the old and the new HTML document are found via difflib and put into a list.
    '''
    diff = difflib.unified_diff(str(parsed_doc_old).splitlines(), str(parsed_doc_new).splitlines())
    #todo obsolete?
    return list(diff)

def make_pointer_list(lines: list):
    """
    param: a list of lines from a parsed html document; reduced by the bs4 function '.text' and the built-in python string function '.splitlines()' (like: "parsed_doc.text.splitlines()").
    return: a list of pointers in form of integers indicating the line/position in line-list.
    function: the pointers are found by choosing lines which start with Article, ANNEX or Appendix to find points which outline the structure of a document independent of line-numbers to compare newer, longer documents to the old versions. The AAAs mostly output the expected "Chapter-Lines" but sometime independent sentences are found, too. Those are not problematic, because either they are in both documents and only help by being another anchor, or they are only in one, then they are being skipped in the matching process.
    """
    pointers = []
    count = 0
    for line in lines:
        if line.startswith("Article") or line.startswith("ANNEX") or line.startswith("Appendix"):
            pointers.append(count)
        count += 1
    return pointers

def find_surrounding_pointers(pointers: list, position: int):
    """
        param: a list of pointers in form of integers and an integer position. All integers represent lines/positions in line-list.
        return: a list of two integer pointer from the list surrounding the input position closest.
        function: via a binary search the surrounding pointers are found.
    """
    lower_bound = 0
    upper_bound = len(pointers) - 1
    # Pointer start in the furthest apart position from the first line to the last pointer available. If the position is outside the range filled with pointers todo because somehow it works
    surrounding_pointers = [0, pointers[len(pointers) - 1]]
    if position > pointers[len(pointers) - 1]:
        print(f"Position {position} is bigger than the last pointer {pointers[len(pointers) - 1]}. UNFIXED PROBLEM!") #TODO

    # Binary search from lecture GAD
    while lower_bound <= upper_bound:
        middle = (upper_bound + lower_bound) // 2

        if pointers[middle] == position: # should not happen, because of how pointers and change positions are found (textual)
            print(f"FAIL (in f_sur_poin with param {pointers} and {position}): The Position is right on a pointer!")
            return [pointers[middle], pointers[middle]]
        elif pointers[middle] < position:
            lower_bound = middle + 1
        else:
            upper_bound = middle - 1

        if pointers[middle] < position:
            surrounding_pointers[0] = pointers[middle]
        elif pointers[middle] > position:
            surrounding_pointers[1] = pointers[middle]

    return surrounding_pointers

def find_changes_and_make_diff_of_surrounding_text(parsed_doc_old: BeautifulSoup, parsed_doc_main: BeautifulSoup):
    """
    param: two Beautiful Soup parsed html documents, one is called "MAIN" which is the newer version of the legal act and the old one for comparison.
    return: a [x,y] set of two lists: the first (x) is a list of diffs of text passages between old and new/main containing changes and the second (y) is a list of only the change-texts just for testing and trying.
    function: #TODO 4 steps
    """
    # Old file
    lines_old = parsed_doc_old.text.splitlines() #ToDo check for wrong param order (new vs old)!
    lines_end_old = len(lines_old) - 1
    pointers_old = make_pointer_list(lines_old)
    # Main file (the newer)
    lines_main = parsed_doc_main.text.splitlines()
    lines_end_main = len(lines_main) - 1
    pointers_main = make_pointer_list(lines_main)

    "Step 1: Find the changes via the marking arrows '►' and '▼'!" #ToDo arrow assumption...
    arrows_main = [] # list of arrow names
    arrows_position_main = [] # list of arrow position (indicis align)
    count = 0
    for l_m in lines_main:
        #TODO '►' and '▼' are not safe or are they?
        if "►" in l_m or "▼" in l_m:
            arrows_main.append(l_m[1:]) # without the arrows
            arrows_position_main.append(count)
        count += 1

    "Step 1.2: Check if the old file also has already been changed and if yes find the changes via the marking arrows as above. The found arrows can be subtracted from the main list. Even if the changes are not the same in the version, later changes will have own arrows, thus every variation will be found."
    old_is_basis = 'Amended by:' not in lines_old and 'Corrected by:' not in lines_old # alternatively html class 'hd-modifiers'
    subtract_arrows = []
    if not old_is_basis:
        for l_o in lines_old:
            if ("►" in l_o or "▼" in l_o) and 'B' not in l_o:
                subtract_arrows.append(l_o[1:]) # without the arrows
    # Subtraction
    for a in arrows_main:
        if a in subtract_arrows:
            ap = arrows_main.index(a)
            arrows_position_main.pop(ap)
            arrows_main.remove(a)

    "Step 1.3: Now finding the real changed text by only looking at the changes (not the base text) and collecting texts and positions in lists. The texts are NOT being used later on, just for control and debugging purposes."
    changes_main = [] # will contain the bare minimum of changes: from change-arrow to the next arrow! {Problems: (1) those texts have no context and (2) some arrows are placed inside sentences for little changes, where no additional arrow follows}
    positions_main = [] # positions of those changes; only the changes, not the base text which is also in the arrow list (indicis align)
    if len(arrows_main) != len(arrows_position_main):
        print(f"ERROR (after finding arrows_main): The amount of arrow-names {len(arrows_main)} and arrow-positions {len(arrows_position_main)} are not the same, thus the indicis will not align!")
    else:
        count = 0
        list_len = len(arrows_main)
        while count < list_len:
            if arrows_main[count] == 'B':
                # Base Text: nothing is changed in those parts.
                count += 1
                continue
            else:
                # A, M or C Text: Amendment or Corrigendum which will be processed.
                positions_main.append(arrows_position_main[count])
                area_of_change = []
                pos = arrows_position_main[count]
                if count > list_len - 2: # if there is no further arrow, continue to the end of the document
                    while pos <= lines_end_main:
                        area_of_change.append(lines_main[pos])
                        pos += 1
                else: # if there is another arrow, continue up to the next arrow
                    while pos < arrows_position_main[count + 1]:
                        area_of_change.append(lines_main[pos])
                        pos += 1
                # concat the lines to a single string
                changes_main.append("".join(area_of_change))
            count += 1
            #ToDo use this classification?:
            '''    
            if arrows_new[count].startswith('M'):
                # amendment
            elif arrows_new[count].startswith('A'):
                # amendment
            elif arrows_new[count].startswith('C'):
                # corrigendum
            else:
                # Fail or edge case
            '''
    if len(changes_main) != len(positions_main):
        print(f"ERROR (after finding changes_main): The amount of change-texts {len(changes_main)} and change-arrow-positions {len(positions_main)} are not the same, thus the indicis will not align!")

    "Step 2: Find the pointers surrounding the change and the corresponding in the old version"
    # Find the surrounding pointers for every change-position
    text_areas_start_end_main = []  # consists of [from,to] sets
    for p in positions_main:
        text_areas_start_end_main.append(find_surrounding_pointers(pointers_main, p))

    def find_old_pointer(corresponding_main_pointer: int):
        """
        param: a pointer as integer from the newer main document.
        return: a pointer as integer indicating the line/position in line-list with the same "value"/name in the text as the input-pointer. If there is no match '-1' is returned.
        function: at first it is assumed, that the pointers have the same index in the pointer-lists. If that is not the case, the pointers around this index are searched. If there is no match (possible if the pointer was added by a change), '-1' is returned and a new "main-pointer" has to be found.
        """
        if corresponding_main_pointer == 0:
            # if the main-pointer is the beginning of the document, so is the old-pointer
            return 0
        else:
            correct_line_main = lines_main[corresponding_main_pointer]
            # assuming the pointer lists align
            result_index = pointers_main.index(corresponding_main_pointer)
            if result_index < len(pointers_old) and lines_old[pointers_old[result_index]] == correct_line_main:
                return pointers_old[result_index]
            # if they not align, the surrounding spaces in the old pointer list are searched
            for n in range(1, len(pointers_old)):
                # next pointers
                if result_index + n < len(pointers_old) and lines_old[pointers_old[result_index + n]] == correct_line_main:
                    return pointers_old[result_index + n]
                # previous pointers
                if result_index - n < len(pointers_old) and lines_old[pointers_old[result_index - n]] == correct_line_main:
                    return pointers_old[result_index - n]
            # return if no pointer fits ToDo is that true?
            return -1

    "Step 2.1: Find the old pointers matching to the main ones. If there is no old pointer fitting the main pointer (which is very possible), a new main pointer has to be found, so the text-passages stay comparable."
    text_areas_start_end_old = []
    texts_main = []  # the string of the text between the [from, to] in text_areas_start_end_main (for step 3)
    texts_old = []
    for ta_main in text_areas_start_end_main:
        ta_old = [-1,-1]
        while ta_old[0] < 0:
            ta_old[0] = find_old_pointer(ta_main[0]) # the closest main pointer
            if ta_old[0] < 0 and pointers_main.index(ta_main[0]) - 1 >= 0:
                # Pointers further away which may match (direction -> 0)
                ta_main[0] = pointers_main[pointers_main.index(ta_main[0]) - 1]
            elif ta_old[0] >= 0:
                break # found :)
            else:
                # Every document has a start, so this is a pointer they have in common (RESCUE)
                ta_old[0] = 0
                break
        while ta_old[1] < 0:
            ta_old[1] = find_old_pointer(ta_main[1]) # the closest main pointer ( maybe just plus one '+1' to the start is possible but this is safer)
            if ta_old[1] < 0 and pointers_main.index(ta_main[1]) + 1 < len(pointers_main):
                # Pointers further away which may match (direction -> EoF)
                ta_main[1] = pointers_main[pointers_main.index(ta_main[1]) + 1]
            elif ta_old[1] >= 0:
                break # found
            else:
                # Every document has an End (of file), so this is a pointer they have in common (RESCUE)
                ta_old[1] = lines_end_old
                break

        "Step 2.2: Check the found old pointers to some criteria"
        if lines_main[ta_main[0]] == lines_old[ta_old[0]] and lines_main[ta_main[1]] == lines_old[ta_old[1]]: # main and old are matching => add
            text_areas_start_end_old.append(ta_old)
        elif ta_old[1] == lines_end_old: # might not match, but it goes up to the end of the old document => add
            text_areas_start_end_old.append(ta_old)
        elif ta_old[0] == ta_old[1]: # start and end is the same => NULL
            print(f"NULL_FAIL: The area {ta_old} found to the area in the main document {ta_main} has the same Start and End Pointer!")
        else: # anything else
            print(f"FAIL (after text_area checks): Final tests failed with {ta_old} for main {ta_main} WHERE main says '{lines_main[ta_main[0]]}' and '{lines_main[ta_main[1]]}' while old says '{lines_old[ta_old[0]]}' and '{lines_old[ta_old[1]]}'. ")

        "Step 3: Concat the lines in the area between Start and End pointers to one complete single string for each document."
        tx_tmp = []
        pos = ta_main[0]
        while pos < ta_main[1]:
            tx_tmp.append(lines_main[pos])
            pos += 1
        texts_main.append("".join(tx_tmp))
        #Todo Repetition!
        tx_tmp = []
        pos = ta_old[0]
        while pos < ta_old[1]:
            tx_tmp.append(lines_old[pos])
            pos += 1
        texts_old.append("".join(tx_tmp))
    # General safety test:
    if len(texts_old) != len(texts_main) or len(texts_main) != len(text_areas_start_end_main) or len(text_areas_start_end_main) != len(text_areas_start_end_old):
        print(f"FAIL (after text concat): Amounts of text areas and texts are different: {len(texts_main)} : {len(text_areas_start_end_main)} : {len(texts_old)} : {len(text_areas_start_end_old)}")

    "Step 4: Make for every pair of (old and main) text a diff via difflib for the return."
    diffs = []
    for t in texts_main:
        t_o = texts_old[texts_main.index(t)]
        diffs.append(list(difflib.unified_diff(t_o.splitlines(), t.splitlines())))

    #TODO [0,n] changes aussortieren und doppelte Bereiche aussortieren!

    "Debugging Console Print Out"
    print("-----------------------")
    print(f"The main pointers have {len(pointers_main)} entries, the old have {len(pointers_old)}. There are {len(pointers_main)-len(pointers_old)} more pointers!")
    print(f"The main text parts have {len(texts_main)} entries, the old have {len(texts_old)}. The difference is {abs(len(texts_main)-len(texts_old))}.")
    print(f"The main text areas have {len(text_areas_start_end_main)} entries, the old have {len(text_areas_start_end_old)}. The difference is {abs(len(text_areas_start_end_main)-len(text_areas_start_end_old))}.")
    print(f"arrows_main:{arrows_main}; Len: {len(arrows_main)}")
    #print(f"changes_main:{changes_main}; Len: {len(changes_main)}")
    #print(f"positions_main:{positions_main}; Len: {len(positions_main)}")
    #print(f"texts_main:{texts_main}; Len: {len(texts_main)}")
    print("-----------------------")
    return [diffs, changes_main]

def function():
    """
    param:
    return:
    function:
    """
    pass

### Debugging:
# Big file:
# URL to the html file (REACH 17.12.2022)
reach_url_new = 'https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02006R1907-20221217&from=EN'
# URL to the old html file (REACH 06.03.2013)
reach_url_old = 'https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02006R1907-20130306&from=EN'
# Small file:
# URL to online html file (32019R0817)
url_first = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019R0817&from=DE"
url_middle = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02019R0817-20190522&from=DE"
url_latest = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A02019R0817-20210803&from=DE"
# Path to local html file (32019R0817)
file_first = "/Users/jacobfehn/Documents/Uni/7. Semester/Thesis/Webservice/backend/test_daten/CELEX32019R0817_EN_TXT.html"
file_middle = "/Users/jacobfehn/Documents/Uni/7. Semester/Thesis/Webservice/backend/test_daten/CELEX02019R0817-20190522_EN_TXT.html"
file_latest = "/Users/jacobfehn/Documents/Uni/7. Semester/Thesis/Webservice/backend/test_daten/CELEX02019R0817-20210803_EN_TXT.html"
# Some Test File
t_old = pars_html("https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32003D0076")
t_middle = pars_html("https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02003D0076-20180510") # M: 2
t_new = pars_html("https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02003D0076-20210811") # M: 2 + 6


example_content_l = pars_html(file_latest) # C: 1 M: 1
example_content_m = pars_html(file_middle) # C: 1 M: 0
example_content_f = pars_html(file_first)

'''
find_changes_and_make_diff_of_surrounding_text(example_content_f, example_content_m)
print("SHOULD FIND C1")
find_changes_and_make_diff_of_surrounding_text(example_content_m, example_content_l)
print("SHOULD FIND M1")
find_changes_and_make_diff_of_surrounding_text(example_content_f, example_content_l)
print("SHOULD FIND C1 and M1")
find_changes_and_make_diff_of_surrounding_text(pars_html(reach_url_old), pars_html(reach_url_new))
print("SHOULD FIND a million things lol")
find_changes_and_make_diff_of_surrounding_text(t_old, t_middle)
print("SHOULD FIND M1 with 2 instances")
find_changes_and_make_diff_of_surrounding_text(t_middle, t_new)
print("SHOULD FIND M2 with 6 instances")
find_changes_and_make_diff_of_surrounding_text(t_old, t_new)
print("SHOULD FIND M1 and M2 with 2 and 6 instances")
'''
# ToDo: <hr class="separator"/> um die Gliederung raus zu kriegen.