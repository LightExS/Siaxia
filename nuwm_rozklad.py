from selenium import webdriver
import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import pandas as pd


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


def get_timetable(faculty, group, date):
    op = webdriver.ChromeOptions()
    op.add_argument("headless")
    driver = webdriver.Chrome(options=op)
    driver.get("https://desk.nuwm.edu.ua/cgi-bin/timetable.cgi")

    faculty_list_el = Select(driver.find_element(By.ID, "faculty"))
    faculty_list_el.select_by_visible_text(faculty)

    group_el = driver.find_element(By.ID, "group")
    group_el.send_keys(group)

    date_el = driver.find_element(By.NAME, "sdate")
    date_el.send_keys(date)

    driver.find_element(By.CLASS_NAME, "btn-success").click()

    try:
        form = driver.find_element(
            By.XPATH, "/html/body/div[1]/div/div/div/div[3]/div/div"
        )
        ht = form.get_attribute("innerHTML")
        table = pd.read_html(ht)[0]
    except selenium.common.exceptions.NoSuchElementException:
        return []
    normalized_data = normalize_data(table)
    return normalized_data


if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
    get_timetable()
