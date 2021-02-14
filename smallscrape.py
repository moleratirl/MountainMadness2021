import requests
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError, Timeout
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

# from selenium.webdriver.chrome.options import Options
# params = year/term/dept/coursenum
# i.e 2019/spring/cmpt/300
from selenium.common.exceptions import NoSuchElementException

MATCH_LIST = ["fall", "spring", "summer"]
OUTLINE_BASE_URL = "http://www.sfu.ca/outlines.html?"


# CHROME_PATH = "D:\chromedriver_win32\chromedriver.exe" # need install chrome driver for selenium to work https://chromedriver.chromium.org/downloads

# input("list out courses format: year/<fall|spring|summer> \n or search course format: year/<fall|spring|summer>/dept/coursenumber")

def parseInputParams():
    while True:
        input_params = input("search for class in format of year/term/dept/coursenum: ")
        if input_params:
            parse_in = input_params.split("/")
            if len(parse_in) < 4:
                print("need exactly four arguments i.e in the format of year/term/dept/coursenum")
                continue
            if not parse_in[0].isnumeric():
                print("year should be numeric i.e 2019")
                continue
            if parse_in[1].lower() not in MATCH_LIST:
                print("terms must be exactly one of fall|spring|summer")
                continue
            if any(i.isdigit() for i in parse_in[2]):
                print("dept cannot contain numbers")
                continue
            if not parse_in[3].isnumeric():
                print("coursenumber should be numeric i.e 300")
                continue
            return [parse_in[0], parse_in[1].lower(), parse_in[2], parse_in[3]]


def getResp(query_list):
    query_str = "http://www.sfu.ca/bin/wcm/course-outlines?year={}&term={}&search={}%20{}".format(query_list[0],
                                                                                                  query_list[1],
                                                                                                  query_list[2],
                                                                                                  query_list[3])
    print("related results: \n")
    suffix_list = []
    try:
        res = requests.get(query_str, timeout=5)
        res.raise_for_status()
        jsonRes = res.json()
        for value in jsonRes:
            suffix_str = value["value"]
            ls = suffix_str.split("/")
            if len(ls) < 5:
                continue
            if ls[3] != query_list[3]:
                continue
            suffix_list.append(suffix_str)

    except HTTPError as httperror:
        print(f"http error raised: code: {httperror}")
    except Timeout as timeout:
        print(f"http error timed out: code: {timeout}")
    except Exception as excep:
        print(f"exception raised: code: {excep}")
    return suffix_list


# A version of scrapeOutline using BeautifulSoup, worse as it scrapes less info but required less dependencies
def scrape_outline_for_app(suffix):
    outline = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/71.0.3578.80 Safari/537.36'}
    session = requests.Session()
    session.headers.update(headers)
    url = OUTLINE_BASE_URL + suffix
    root = session.get(url)
    try:
        root_soup = BeautifulSoup(root.content, "html.parser")
        header_title = root_soup.find('div', {'class': 'custom-header'})
        course_name = header_title.find('h1', {'id': 'name'}).text + header_title.find('h2', {'id': 'title'}).text
        outline['course'] = course_name
        header_time = root_soup.find('li', {'class': 'course-times'})
        if header_time is not None:
            times_list = []
            times_raw = header_time.findAll('p')
            for time in times_raw:
                times_list.append(time.text)
            outline['time'] = times_list
        head_instr = root_soup.find('ul', {'class': 'instructorBlock1'})
        instrs = []
        if head_instr is not None:
            instrs_raw = head_instr.findAll('li', {'class': 'instructor'})
            for instr in instrs_raw:
                name_raw = instr.find_all(text=True)
                name = name_raw[2].strip()
                instrs.append(name)
            outline['instructors'] = instrs
        head_prereq = root_soup.find('li', {'class': 'prereq'})
        if head_prereq is not None:
            preq_raw = head_prereq.find_all(text=True)
            preq = preq_raw[len(preq_raw) - 1].strip()
            outline['prerequisite'] = preq
    except NoSuchElementException:
        print("some elements are not found")
    # print(outline)
    return outline


def scrapeOutline(suffix_list):
    p = ChromeDriverManager()
    outline = {}
    driver = webdriver.Chrome(executable_path=p.install())
    for suffix_val in suffix_list:
        if suffix_val:
            furl = OUTLINE_BASE_URL + suffix_val
            driver.get(furl)
            try:
                owelems = driver.find_element_by_class_name("overview-list").find_elements_by_tag_name("li")
                for owelem in owelems:
                    attrib = owelem.get_attribute("class")
                    if attrib == "course-times" or attrib == "exam-times":
                        p = owelem.text
                        outline["course-times"] = p
                        print(p)
                    elif attrib == "instructor":
                        instr = owelem.text
                        outline["instructor"] = instr
                        print(instr)
                    elif attrib == "prereq":
                        prereq = owelem.text
                        outline["prereq"] = prereq
                        print(prereq)

                caldescr = driver.find_element_by_xpath(
                    "//h4[contains(text(),'CALENDAR DESCRIPTION:')]/following-sibling::p")
                print(caldescr.text)
                outline["calender"] = caldescr

                coursedet = driver.find_element_by_xpath(
                    "//h4[contains(text(),'COURSE DETAILS:')]/following-sibling::p")
                print(coursedet.text)
                outline["detail"] = coursedet
                grading = driver.find_element_by_class_name("grading")
                glists = grading.find_element_by_class_name("grading-items").find_elements_by_tag_name("li")
                for glist in glists:
                    print("LOLOLOLOLOLOLL")
                    one = glist.find_element_by_class_name("one")
                    two = glist.find_element_by_class_name("two")
                    print(one.text)
                    print(two.text)
                notes = grading.find_elements_by_tag_name("p")
                for note in notes:
                    print(note.text)
                material = driver.find_element_by_xpath(
                    "//h4[contains(text(),'MATERIALS + SUPPLIES:')]/following-sibling::p")
                print(material.text)
                reqreading = driver.find_element_by_xpath(
                    "//h4[contains(text(),'REQUIRED READING:')]/following-sibling::div")
                ##print(reqreading.text)
            except NoSuchElementException:
                print("some elements are not found")
        print("end of query\n\n")
    driver.close()

# scrape_outline_for_app('2021/spring/cmpt/125/d100')
# out = getResp(parseInputParams())
# print(out)
# scrapeOutline(out)
