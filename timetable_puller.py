from selenium import webdriver
import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import pandas as pd

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode


def extract_PIB_LECTURE(text):
    if text == "Фізичне виховання":
        return ["", text]
    name = []
    lecture = ""
    splitted_text = text.split(" ")

    for part in splitted_text:
        if part[0].isupper() and part[1].islower():
            name.append(part)
        if len(name) == 3:
            break
    if len(name) != 3:
        name = []

    if name != []:
        name_end = text.find(name[-1])
        lecture = text[name_end + len(name[-1]) + 1 :]

    return [" ".join(name), lecture]


def extract_data(row):
    splitted_row = row.split("  ")
    res = [""]
    while splitted_row:
        if splitted_row[0].isnumeric():
            res.append(splitted_row[0])
        elif len(splitted_row) != 1 and (
            splitted_row[1].isnumeric() or extract_PIB_LECTURE(splitted_row[1])[0] == ""
        ):
            if not res[-1].isnumeric():
                res.append("0")
            res.append(extract_PIB_LECTURE(splitted_row[0])[0])
            res.append(splitted_row[1])
            splitted_row.pop(1)
        else:
            if not res[-1].isnumeric():
                res.append("0")
            res.extend(extract_PIB_LECTURE(splitted_row[0]))

        splitted_row.pop(0)

    res.pop(0)
    return res


def normalize_data(table):
    timetable = []
    for nm, hours, row in zip(table[0], table[1], table[2]):
        if isinstance(row, float):
            continue
        splitted_hours = hours.split(" ")
        edited_hours = splitted_hours[0] + "-" + splitted_hours[1]
        temp_row = {"number": nm, "hours": edited_hours}

        extracted_data = extract_data(row)
        planning = []

        for i in range(0, len(extracted_data), 3):
            temp_plan = {}
            temp_plan["classroom"] = extracted_data[0 + i]
            temp_plan["lecturer"] = extracted_data[1 + i]
            temp_plan["subject"] = extracted_data[2 + i]
            planning.append(temp_plan)

        temp_row["plannings"] = planning

        timetable.append(temp_row)

    return timetable


def get_timetable(teacher="", group="", sdate="", edate=""):
    params = {
        "faculty": "",
        "teacher": teacher,
        "course": "",
        "group": group,
        "sdate": sdate,
        "edate": edate,
    }
    encoded_data = urlencode(params, encoding="Windows-1251")

    response = requests.post(
        "https://desk.nuwm.edu.ua/cgi-bin/timetable.cgi?n=700", data=encoded_data
    )

    response.encoding = "windows-1251"
    soup = BeautifulSoup(response.text, features="lxml")

    divs = soup.select(".col-md-6.col-sm-6.col-xs-12.col-print-6")

    tables = [div.table for div in divs]
    dates = [div.h4.text for div in divs]

    if tables == []:
        return [], []

    parsed_data = [pd.read_html(str(table), flavor="bs4")[0] for table in tables]

    normalized_tables = [normalize_data(table) for table in parsed_data]

    return normalized_tables, dates


def change_table_to_str(table):
    output = ""
    for row in table:
        output += f"Пара №{row['number']} {row['hours']}\n"
        for subj in row["plannings"]:
            if subj["classroom"] == "0":
                output += f"     Аудиторія: Дистанційно\n     Викладач: {subj['lecturer']}\n     Предмет: {subj['subject']}\n\n"
            else:
                output += f"     Аудиторія: {subj['classroom']}\n     Викладач: {subj['lecturer']}\n     Предмет: {subj['subject']}\n\n"
    return output


if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
    timetable, dates = get_timetable(
        group="АКІТ-11фб",
        sdate="01.07.24",
    )
    print(timetable)
    print(dates)
