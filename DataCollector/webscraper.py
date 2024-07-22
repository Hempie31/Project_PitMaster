# import requests
from tika import parser
import numpy
import tabula
from datetime import datetime
import urllib.request
import requests


DRIVER_INFO_URL = "https://www.fia.com/sites/default/files/doc_15_-_2022_saudi_arabian_grand_prix_-_entry_list.pdf"
LAP_TIMES_URL = "https://www.fia.com/sites/default/files/2022_02_ksa_f1_r0_timing_racelapanalysis_v01.pdf"
STARTING_YEAR = 2015
CURRENT_YEAR = int(datetime.today().strftime('%Y'))


class WebScraper:

    def __init__(self):
        self.driverInformationDF = {}

    def iterate_through_races(self):
        # fp = urllib.request.urlopen("https://www.fia.com/events/fia-formula-one-world-championship/season-2023/2023-fia-formula-one-world-championship")
        fp = urllib.request.urlopen("https://www.fia.com/events/fia-formula-one-world-championship/season-2016/formula-one")
        # print(check_url("https://www.fia.com/events/fia-formula-one-world-championship/season-2021/calendar"))
        # print(check_url("https://www.fia.com/events/fia-formula-one-world-championship/season-20212/calendar"))

        mybytes = fp.read()

        mystr = mybytes.decode("utf8")
        fp.close()

        race_list = []
        contains_error = False
        for line in mystr.split("\n"):
            if ("grand-prix" in line and "<li>" not in line and "news" not in line):
                html_string_split = line.split('"')

                if (len(html_string_split) == 7):
                    print(html_string_split[3])
                    race_list.append(line)

    def extract_driver_info(self):

        # Extract tables from PDF
        tables = tabula.read_pdf(DRIVER_INFO_URL,
                                 pages='all',
                                 multiple_tables=True)

        # Assuming the relevant table is the first one extracted
        self.driverInformationDF = tables[0].drop([0, 1])

        self.driverInformationDF = self.driverInformationDF.rename(columns={
            'Unnamed: 0': 'Number',
            'Unnamed: 1': 'Name',
            'Unnamed: 2': 'Nationality',
            'Unnamed: 3': 'Team',
            'Unnamed: 4': 'Constructor'})
        self.driverInformationDF["lapTimes"] = self.driverInformationDF.apply(lambda x: [], axis=1)
        self.driverInformationDF["pitstops"] = self.driverInformationDF.apply(lambda x: [], axis=1)
        self.driverInformationDF["tiresUsed"] = self.driverInformationDF.apply(lambda x: [], axis=1)

        for driver_number in self.driverInformationDF['Number']:
            self.driverInformationDF.replace(to_replace=driver_number, value=int(driver_number), inplace=True)

        self.driverInformationDF = self.driverInformationDF.sort_values(by=['Number'])

        # Display the extracted table
        print("\n", self.driverInformationDF)

    def extract_lap_info(self):

        driver_full_names = list(self.driverInformationDF["Name"])

        print("Extracting lap info...")
        # driverNames = self.driverInformationDF['Name'].tolist()
        lap_time_data = parser.from_file(LAP_TIMES_URL)
        lap_time_data_list = lap_time_data["content"].split("\n")

        temporary_driver_index = []
        for line in lap_time_data_list:
            split_line = line.split(" ")

            if (len(split_line) == 3):
                if (split_line[1] != ""):
                    found_name = search_list_for_name(split_line[2], driver_full_names)

                    if (len(temporary_driver_index) != 0):
                        if found_name is not None:
                            temporary_driver_index = self.driverInformationDF.index[self.driverInformationDF["Name"] == found_name].tolist()

                        elif ('p' == split_line[1].lower()):
                            self.driverInformationDF.loc[temporary_driver_index[0], 'pitstops'].append(int(split_line[0]))

                    else:
                        temporary_driver_index = self.driverInformationDF.index[self.driverInformationDF["Name"] == found_name].tolist()

                if (':' in split_line[2]):
                    self.driverInformationDF.loc[temporary_driver_index[0], 'lapTimes'].append(split_line[2])
                    # print(split_line[0], "\t", split_line[1], "\t", split_line[2])

        print("\n", self.driverInformationDF)

        for time in self.driverInformationDF.loc[18, 'lapTimes']:
            print(time)


def search_list_for_name(search_string, driver_names):

    for name in driver_names:
        if search_string.lower() in name.split(" ")[-1].lower():
            return (name)
    return None


def check_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        print(f"Successfully loaded: {url}")
        return True
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            print(f"Failed to load resource: the server responded with a status of 404 ({url})")
            return False
        else:
            print(f"HTTP error occurred: {http_err} ({url})")
            return False
    except Exception as err:
        print(f"Other error occurred: {err} ({url})")
        return False
