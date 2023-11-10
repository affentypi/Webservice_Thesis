import datetime
import difflib
import urllib3 # 20 seconds for both reach files
import requests # 10 seconds for both reach files
from bs4 import BeautifulSoup
import re

def pars_html(url):
    """
    param: a URL in either HTTP format or a local file-path.
    return: a Beautiful Soup parsed HTML document.
    function: the URL is opened and the file is fetched. IN the first attempt via the request lib, in case of an error via the slower urllib. If no URL is entered, the local file is opened and read.
    """
    celex = url[url.find("?uri=") + 11:]
    if "&" in celex:
        celex = celex[:celex.find("&")]
    """print("> HTML Parsing -----------------------")
    print(url)
    print(celex)
    print("-----------------------")"""
    if not re.match("[03](A0)?\d{4}[RLDS]\d{4}([(]\d+[)])?(-\d{4}\d{2}\d{2})?", celex): # todo A0?
        print(f"ERROR: CELEX is in wrong format!")
    html_doc = "null"
    if url.startswith('http'):
        # Fetch the html file via URL
        if not url.startswith("https://eur-lex.europa.eu/legal-content/"):
            print(f"ERROR: the URL does not reference a eur-lex html site!")
        try: # the faster way
            response = requests.get(url)
            response.raise_for_status()
            html_doc = response.text
        except Exception as e:
            print(f"ERROR (after opening the url): Exception {e} was thrown. Now another attempt will be made!")
            print(e.__traceback__)
            try: # a slower todo obsolete?
                http = urllib3.PoolManager()
                response = http.urlopen('GET', url)
                html_doc = response.data
            except Exception as e2:
                print(f"ERROR (after opening the url again): Exception {e2} was thrown. The program ends here!")
                print(e2.__traceback__)
        finally:
            if html_doc == "null":
                print(f"ERROR (after both url attempts): The URL {url} could to be corrupted!")
    else:  # local tests
        try:
            html_doc = open(url).read()
        except Exception as e:
            print(f"ERROR (after parsing local test): Exception {e} was thrown. The Path {url} could to be corrupted!")
            print(e.__traceback__)

    # Parse and format the html file using bs4
    parsed_doc = BeautifulSoup(html_doc, 'html.parser')

    return celex, parsed_doc

def find_newest(url):
    """
    param: a URL in either HTTP format or a local file-path.
    return: a Beautiful Soup parsed HTML document of the newest available consolidated document.
    function: first, the celex number is extracted and the document overview is opened (without /HTML in URL).
    The HTML tag for the "newest document" is used to create the new URL, which is then parsed by the function pars_html(url)
    """
    celex = url[url.find("?uri=") + 11:]
    save = celex
    if "&" in celex:
        celex = celex[:celex.find("&")]
    if "-" in celex:
        celex = celex[:celex.find("-")]
    else:
        celex = "0" + celex[1:]
    try:
        ref = pars_html(url.replace("/HTML", ""))[1].findAll("p", class_="accessCurrent")
        date = re.findall("\d\d/\d\d/\d\d\d\d", ref[0].text)[0]
        celex = celex + "-" + date[6] + date[7] + date[8] + date[9] + date[3] + date[4] + date[0] + date[1]
    except Exception as e1:
        try:
            ref = pars_html(url.replace("/HTML", ""))[1].findAll("p", class_="forceIndicator")
            date = re.findall("\d\d/\d\d/\d\d\d\d", ref[0].text)[0]
            celex = celex + "-" + date[6] + date[7] + date[8] + date[9] + date[3] + date[4] + date[0] + date[1]
        except Exception as e2:
            print(f"FAILURE in finding the latest CELEX! With forceIndicator:{e2} when {e1} did not work!")

    if celex == save:
        print(f"FAIL: The URL already links to the newest version")
    print(f"Old URL: {url} and new URL: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{celex}")
    return pars_html("https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:" + celex)

def print_out(parsed_doc):
    """
    param: a Beautiful Soup parsed html document.
    function: prints out the HTML document in "prettified" form on the console.
    """
    print(parsed_doc.prettify())

def make_pointer_list(lines: list):
    """
    param: a list of lines from a parsed html document; reduced by the bs4 function '.text' and the built-in python string function '.splitlines()' (like: "parsed_doc.text.splitlines()").
    return: a list of pointers in form of integers indicating the line/position in line-list and the line-list.
    function: the pointers are found by choosing lines which start with Article, ANNEX or Appendix to find points which outline the structure of a document independent of line-numbers to compare newer, longer documents to the old versions. The AAAs mostly output the expected "Chapter-Lines" but sometime independent sentences are found, too. Those are not problematic, because either they are in both documents and only help by being another anchor, or they are only in one, then they are being skipped in the matching process.
    For old documents, where the whole document is in one line, 0 pointers will be found, so the lines are overwritten by a new line array, where the lines are usable for extracting the pointers.
    For this, the line with where the all the text is in, the line is split by delimiters (that are re-appended to not change the text itself.
    """
    pointers = []
    count = 0
    for line in lines:
        if re.match("Article\s\d+$", line) or re.match("ANNEX(\s[IVXLCD])*$", line) or re.match("Appendix(\s\d+)$", line):
            pointers.append(count)
        count += 1
    # For some old Texts
    if len(pointers) <= 0:
        new_lines = []
        for line in lines:
            "The lines are split into parts and by parts appended to the new_lines list."
            split_line = line.split(".")
            if len(split_line) == 1 and line:
                new_lines.append(line)
            else:
                for part in split_line:
                    part = part.strip()
                    if "HAS ADOPTED THIS" in part:
                        "The first article is often right behind the introduction, so the get the first article, this needs an extra processing."
                        split_first_part = part.split(":") # tmp list
                        for sfp in split_first_part:
                            sfp = sfp.strip()
                            if "HAS ADOPTED THIS" in sfp:
                                new_lines.append(sfp + ":")
                            elif sfp.startswith("Article") or sfp.startswith("ANNEX") or sfp.startswith("Appendix"):
                                split_part_sfp = sfp.split(" ") # tmp list
                                if len(split_part_sfp) > 2:
                                    "Appending the first two parts of the parts ( Article and its number or name)."
                                    new_lines.append(split_part_sfp[0] + " " + split_part_sfp[1])
                                    tmp = []
                                    "Everything behind the first two parts are put together to again represent the paragraph and appended to the list."
                                    for sp in split_part_sfp[2:]:
                                        tmp.append(sp)
                                    new_lines.append(" ".join(tmp) + ".")
                                elif len(split_part_sfp) > 1:
                                    "If there are only two parts (for example  'Article 1. ipsum...')."
                                    new_lines.append(split_part_sfp[0] + " " + split_part_sfp[1])
                                else:
                                    print("Error with split part" + sfp)
                            else:
                                print("Error with line part" + part)
                    elif part.startswith("Article") or part.startswith("ANNEX") or part.startswith("Appendix"):
                        "Same process as before just for every (not first) article."
                        split_part = part.split(" ") # tmp list
                        if len(split_part) > 2:
                            new_lines.append(split_part[0] + " " + split_part[1])
                            tmp = []
                            for sp in split_part[2:]:
                                tmp.append(sp)
                            new_lines.append(" ".join(tmp) + ".")
                        elif len(split_part) > 1:
                            new_lines.append(split_part[0] + " " + split_part[1])
                        else:
                            print("Error with article split part" + part)
                    elif part and part != " ":
                        "Appending the normal text parts (and re-adding the delimiter."
                        new_lines.append(part + ".")
                    else:
                        if part != "" and part != " " and part != '':
                            print("weird" + part)
        lines = new_lines
        pointers = []
        count = 0
        for line in lines:
            "Again the pointers with the new lines."
            if re.match("Article\s\d+", line) or re.match("ANNEX(\s[IVXLCD])*", line) or re.match("Appendix(\s\d+)*", line):
                pointers.append(count)
            count += 1
        # General safety test:
        if len(pointers) <= 0:
            print(f"FAIL (after making pointer list): No pointers in {lines}!") # empty or repealed

    return pointers, lines

def find_surrounding_pointers(pointers: list, position: int):
    """
        param: a list of pointers in form of integers and an integer position. All integers represent lines/positions in line-list.
        return: a list of two integer pointer from the list surrounding the input position closest.
        function: via a binary search the surrounding pointers are found.
    """
    lower_bound = 0
    upper_bound = len(pointers) - 1
    "Pointer start in the furthest apart position from the first line to the last pointer available."
    surrounding_pointers = [0, pointers[len(pointers) - 1]]
    if position > pointers[len(pointers) - 1]:
        surrounding_pointers = [pointers[len(pointers) - 1], pointers[len(pointers) - 1]]
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
    return:  a list like [changes_name, change_content, change_position, diffs] where change_name, content, etc. are lists with aligning indicis for each modification.
    function:
    Step 1: Find the changes via the marking arrows '►' and '▼'!
    Step 1.2: Check if the old file also has already been changed and if yes find the changes via the marking arrows as above. The found arrows can be subtracted from the main list. Even if the changes are not the same in the version, later changes will have own arrows, thus every variation will be found.
    Step 1.3: Now finding the real changed text by only looking at the changes (not the base text) and collecting texts and positions in lists. The texts are NOT being used later on, just for control and debugging purposes.
    Step 2: Find the pointers surrounding the change and the corresponding in the old version.
    Step 2.2: [removed]
    Step 2.3: Find the old pointers matching to the main ones. If there is no old pointer fitting the main pointer (which is very possible), a new main pointer has to be found, so the text-passages stay comparable.
    Step 2.4: Check the found old pointers to match the criteria necessary to equate them to the new.
    Step 3: Concat the lines in the area between Start and End pointers to one complete single string for each document.
    Step 4: Make for every pair of (old and main) text a diff via difflib for the return.
    """
    # Old file
    lines_old = parsed_doc_old.text.splitlines() #ToDo safety check for wrong param order (new vs old) and for different celex!!
    pointers_old, lines_old = make_pointer_list(lines_old)
    lines_end_old = len(lines_old) - 1
    # Main file (the newer)
    lines_main = parsed_doc_main.text.splitlines()
    pointers_main, lines_main = make_pointer_list(lines_main)
    lines_end_main = len(lines_main) - 1

    "Step 1: Find the changes via the marking arrows '►' and '▼'!"
    arrows_main = [] # list of arrow names
    arrows_position_main = [] # list of arrow position (indicis align)
    count = 0
    for l_m in lines_main:
        if "►" in l_m or "▼" in l_m: # ◄
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
    for sa in subtract_arrows:
        for am in arrows_main:
            if am == sa or am == sa + "\xa0—————":
                arrows_position_main.pop(arrows_main.index(am))
                arrows_main.pop(arrows_main.index(am))

    "Step 1.3: Now finding the real changed text by only looking at the changes (not the base text) and collecting texts and positions in lists. The texts are NOT being used later on, just for control and debugging purposes."
    "Result"
    changes_main = [] # will contain the bare minimum of changes: from change-arrow to the next arrow! {Problems: (1) those texts have no context and (2) some arrows are placed inside sentences for little changes, where no additional arrow follows}
    change_positions_main = [] # positions of those changes; only the changes, not the base text which is also in the arrow list (indicis align)
    "Result"  # ToDo Fixate?
    changes_name = [] # the "names"/indicators of changes
    "Result"
    positions_main = [] # positions of those changes by the last pointer before the change to find in which Article, Annax or Appendix the change is
    if len(arrows_main) != len(arrows_position_main):
        print(f"ERROR (after finding arrows_main): The amount of arrow-names {len(arrows_main)} and arrow-positions {len(arrows_position_main)} are not the same, thus the indicis will not align!")
    else:
        count = 0
        list_len = len(arrows_main)
        while count < list_len:
            if arrows_main[count] == 'B':
                "Base Text: nothing is changed in those parts."
                count += 1
                continue
            else:
                changes_name.append(arrows_main[count])
                "A, M or C Text: Amendment or Corrigendum which will be processed."
                change_positions_main.append(arrows_position_main[count])
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
                "concat the lines to a single string"
                changes_main.append(" ".join(area_of_change))
            count += 1

    "Step 2: Find the pointers surrounding the change and the corresponding in the old version."
    # Find the surrounding pointers for every change-position
    text_areas_start_end_main_with_duplicates = []  # consists of [from,to] sets
    for p in change_positions_main:
        surr_pointers_main = find_surrounding_pointers(pointers_main, p)
        text_areas_start_end_main_with_duplicates.append(surr_pointers_main)
        positions_main.append(lines_main[surr_pointers_main[0]]) # only the from pointer

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
            # return if no pointer fits
            return -1

    "Step 2.2: Remove duplicates from text_areas_start_end_main, because for the diff, every text passage can be processed once, not multiple times"
    # This step was remove, due to issues reassigning the modifications to the diff.
    '''text_areas_start_end_main = []
    for ta in text_areas_start_end_main_with_duplicates:
        if ta not in text_areas_start_end_main:
            text_areas_start_end_main.append(ta)'''
    text_areas_start_end_main = text_areas_start_end_main_with_duplicates

    "Step 2.3: Find the old pointers matching to the main ones. If there is no old pointer fitting the main pointer (which is very possible), a new main pointer has to be found, so the text-passages stay comparable."
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
                if ta_old[1] == ta_old[0]:
                    if ta_old[1] == pointers_old[len(pointers_old) - 1]:
                        ta_old[1] = lines_end_old
                        ta_main[1] = lines_end_main
                        break
                    elif ta_old[1] < pointers_old[len(pointers_old) - 1] and pointers_old.index(ta_old[1]) < len(pointers_old) - 1:
                        ta_old[1] = pointers_old[pointers_old.index(ta_old[1]) + 1]
                        if pointers_main.index(ta_main[1]) < len(pointers_main) - 1:
                            ta_main[1] = pointers_main[pointers_main.index(ta_main[1]) + 1]
                        else:
                            ta_main[1] = lines_end_main
                        break
                else:
                    break # found
            else:
                # Every document has an End (of file), so this is a pointer they have in common (RESCUE)
                ta_old[1] = lines_end_old
                break

        "Step 2.4: Check the found old pointers to some criteria."
        if ta_old[0] == ta_old[1]: # start and end is the same => NULL
            print(f"NULL_FAIL: The area {ta_old} found to the area in the main document {ta_main} has the same Start and End Pointer!")
        if lines_main[ta_main[0]] == lines_old[ta_old[0]] and lines_main[ta_main[1]] == lines_old[ta_old[1]]: # main and old are matching => add
            text_areas_start_end_old.append(ta_old)
        elif ta_old[1] == lines_end_old: # might not match, but it goes up to the end of the old document => add
            text_areas_start_end_old.append(ta_old)
        elif ta_old[0] == 0 and ta_main[0] == 0:
            text_areas_start_end_old.append(ta_old)
        else: # anything else todo fails for 32007R0718 -> still works
            print(f"FAIL (after text_area checks): Final tests failed with {ta_old} for main {ta_main} WHERE main says '{lines_main[ta_main[0]]}' and '{lines_main[ta_main[1]]}' while old says '{lines_old[ta_old[0]]}' and '{lines_old[ta_old[1]]}'. ")

        "Step 3: Concat the lines in the area between Start and End pointers to one complete single string for each document."
        tmp_list = [] # temporary list
        pos = ta_main[0]
        while pos < ta_main[1]:
            tmp_list.append(lines_main[pos])
            pos += 1
        texts_main.append("\n".join(tmp_list))
        #Todo Repetition!
        tmp_list = []
        pos = ta_old[0]
        while pos < ta_old[1]:
            tmp_list.append(lines_old[pos])
            pos += 1
        texts_old.append("\n".join(tmp_list))

    "Step 4: Make for every pair of (old and main) text a diff via difflib for the return."
    "Result"
    diffs = []
    for t in texts_main:
        t_o = texts_old[texts_main.index(t)]
        diffs.append(list(difflib.unified_diff(t_o.splitlines(), t.splitlines())))

    if len(changes_name) == 0 and len(changes_main) == 0 and len(positions_main) == 0 and len(diffs) == 0:
        return ["REPEALED or no changes!", lines_main, [], []]

    "Debugging Console Print Out"
    '''print("> HTML Processing -----------------------")
    print(f"The main pointers have {len(pointers_main)} entries, the old have {len(pointers_old)}. There are {len(pointers_main)-len(pointers_old)} more pointers!")
    print(f"Len: {len(changes_name)}: changes_name:{changes_name};")
    print(f"Len: {len(changes_main)}: changes_main:{changes_main};")
    print(f"Len: {len(positions_main)}: positions_main:{positions_main};")
    print(f"Len: {len(diffs)}: diffs:{diffs};")
    print("html< -----------------------")'''
    return [changes_name, changes_main, positions_main, diffs] # [changes_name, change_content, change_position, diffs]
