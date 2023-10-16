import re

import pandas # "./test_data/DataSet.xlsx"
import openpyxl
import unittest


import html_processing
import nlp_processing

class TestQuantitativeResults(unittest.TestCase):

    def test_old_new(self, url_old=None, url_new=None, result=None):
        if url_old is None or url_new is None or result is None:
            print("EMPTY TEST")
            pass
        else:
            if re.match("C:\s\d+\s([+]\s\d+\s)*; M:\s\d+\s([+]\s\d+\s)*;", result):
                # Corrigendums
                expected_cs = result.split(";")[0].replace("C: ", "").split("+")
                expected_cs_changes = len(expected_cs)
                expected_cs_mods_per_changes = []
                for ecs in expected_cs:
                    expected_cs_mods_per_changes.append(int(ecs))
                    if int(ecs) == 0:
                        expected_cs_changes -= 1
                print(f"C: {expected_cs_changes} and Modifications per Changes = {expected_cs_mods_per_changes}")
                # Amendments
                expected_ms = result.split(";")[1].replace("M: ", "").split("+")
                expected_ms_changes = len(expected_ms)
                expected_ms_mods_per_changes = []
                for ems in expected_ms:
                    expected_ms_mods_per_changes.append(int(ems))
                    if int(ems) == 0:
                        expected_ms_changes -= 1
                print(f"M: {expected_ms_changes} and Modifications per Changes = {expected_ms_mods_per_changes}")

                celex_old, doc_old = html_processing.pars_html(url_old)
                celex_new, doc_new = html_processing.pars_html(url_new)
                html_result = html_processing.find_changes_and_make_diff_of_surrounding_text(doc_old, doc_new)
                fast_result = nlp_processing.process_changes("testfast" + celex_old + celex_new, html_result,True)  # fast test
                accurate_result = nlp_processing.process_changes("testaccurate" + celex_old + celex_new, html_result,False)  # accurate test

                print(len(fast_result[0]) == expected_ms_changes + expected_cs_changes)
                self.assertEqual(len(fast_result[0]), expected_ms_changes + expected_cs_changes)

            else:
                print("RESULT not usable")

    def test_file(self):
        dataframe = openpyxl.load_workbook("./test_data/DataSet.xlsx")
        data = dataframe.active
        data_from_file = []
        # [celex, language, celex_link, first_date, first_url, middle_date, middle_url, last_date, last_url, amount_of_consolidated_versions, directory, topic, name, comment, ...
        # ..., retrieval_date, result_first_last, result_middle_last, result_first_middle]

        for row in range(2, data.max_row):
            print("ROW -----------------------------------")
            row_entries = list(data.iter_cols(1, data.max_column))
            celex = row_entries[1][row].value.__str__()
            print("celex: " + celex)
            language = row_entries[2][row].value.__str__()
            # print("language: " + language)
            celex_link = row_entries[3][row].value.__str__()
            # print("celex_link: " + celex_link)
            first_date = row_entries[4][row].value.__str__()
            # print("first_date: " + first_date)
            first_url = row_entries[5][row].value.__str__()
            # print("first_url: " + first_url)
            middle_date = row_entries[6][row].value.__str__()
            # print("middle_date: " + middle_date)
            middle_url = row_entries[7][row].value.__str__()
            # print("middle_url: " + middle_url)
            last_date = row_entries[8][row].value.__str__()
            # print("last_date: " + last_date)
            last_url = row_entries[9][row].value.__str__()
            # print("last_url: " + last_url)
            amount_of_consolidated_versions = row_entries[10][row].value.__str__()
            # print("amount_of_consolidated_versions: " + amount_of_consolidated_versions)
            directory = row_entries[11][row].value.__str__()
            # print("directory: " + directory)
            topic = row_entries[12][row].value.__str__()
            # print("topic: " + topic)
            name = row_entries[13][row].value.__str__()
            # print("name: " + name)
            comment = row_entries[14][row].value.__str__()
            print("comment: " + comment)
            retrieval_date = row_entries[15][row].value.__str__()
            # print("retrieval_date: " + retrieval_date)
            result_first_last = row_entries[16][row].value.__str__()
            print("result_first_last: " + result_first_last)
            result_middle_last = row_entries[17][row].value.__str__()
            # print("result_middle_last: " + result_middle_last)
            result_first_middle = row_entries[18][row].value.__str__()
            # print("result_first_middle: " + result_first_middle)

            data_from_file.append(
                [celex, language, celex_link, first_date, first_url, middle_date, middle_url, last_date, last_url,
                 amount_of_consolidated_versions, directory, topic, name, comment, retrieval_date, result_first_last,
                 result_middle_last, result_first_middle])

            if first_url is not None and last_url is not None and result_first_last is not None and "old" not in comment and "repealed" not in result_first_last:
                with self.subTest(result_first_last):
                    self.test_old_new(first_url, last_url, result_first_last)

    def test_upper(self): #testing the test
        self.assertEqual('foo'.upper(), 'FOO')


# URL to online html file (32019R0817)
url_first = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019R0817&from=DE"
url_middle = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02019R0817-20190522&from=DE" # C: 1 ; M: 0 ;
url_latest = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A02019R0817-20210803&from=DE" # C: 1 ; M: 1 ;
# Some Test File
t_old = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32003D0076"
t_middle = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02003D0076-20180510" # C: 0 ; M: 2 ;
t_new = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02003D0076-20210811" # C: 0 ; M: 2 + 6 ;

#test_first_last(t_old, t_new, "C: 0 ; M: 2 + 6 ;")
