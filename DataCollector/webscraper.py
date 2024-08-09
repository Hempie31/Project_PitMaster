# import requests
from tika import parser
import numpy
import tabula
import pymongo
from datetime import datetime
from collections import defaultdict
import time
import requests
import fastf1
import sys

DATABASE_URI = "mongodb+srv://admin:admin@f1-cluster.bn1crlr.mongodb.net/?retryWrites=true&w=majority&appName=F1-Cluster"

DRIVER_INFO_URL = "https://www.fia.com/sites/default/files/doc_15_-_2022_saudi_arabian_grand_prix_-_entry_list.pdf"
LAP_TIMES_URL = "https://www.fia.com/sites/default/files/2022_02_ksa_f1_r0_timing_racelapanalysis_v01.pdf"
STARTING_YEAR = 2016
CURRENT_YEAR = int(datetime.today().strftime('%Y'))

fastf1.Cache.enable_cache('FastF1-Cache')


class WebScraper:

    def __init__(self):
        self._mongo_client = pymongo.MongoClient(DATABASE_URI)
        self.driverInformationDF = {}

    def iterate_through_races(self, year):
        database = self._mongo_client["F1-Lap-Data"]
        collection = database[str(year)]

        # try:
            # Attempt to load the event schedule for the given year
        schedule = fastf1.get_event_schedule(year)
        if schedule.empty:
            print(f"No schedule data available for {year}.")
        else:
            print(f"\nEvent schedule for {year}:\n")

            more_races = True
            race_number = 1
            while (more_races):
                # try:
                event_name = schedule.get_event_by_round(race_number)["EventName"]
                session_type = 'R'
                race_dict = {"Name": event_name, "Drivers": {}}

                session = get_session_with_retry(year, event_name, session_type)

                # Get laps data
                laps = session.laps
                results = session.results

                # Extract pit stop data
                pit_stops = laps[laps['PitOutTime'].notnull() | laps['PitInTime'].notnull()]

                lap_dict = defaultdict(list)
                # Print pit stop times
                offset = False
                lap_in_info = ()
                for _, pit_stop in pit_stops.iterrows():
                    driver = pit_stop['Driver']
                    pit_in = pit_stop['PitInTime']
                    pit_out = pit_stop['PitOutTime']
                    lap_number = pit_stop['LapNumber']

                    if (offset):
                        if (driver == lap_in_info[0]):
                            pit_lap_in = laps[(laps['Driver'] == driver) & (laps['LapNumber'] == lap_in_info[1])]
                            if not pit_lap_in.empty:
                                old_compound = pit_lap_in.iloc[0]['Compound']

                            pit_lap_out = laps[(laps['Driver'] == driver) & (laps['LapNumber'] == lap_number)]
                            if not pit_lap_out.empty:
                                new_compound = pit_lap_out.iloc[0]['Compound']

                            lap_dict[driver].append({"lap": lap_in_info[1], "duration": (pit_out - lap_in_info[2]), "oldTire": old_compound, "newTire": new_compound})
                            offset = False
                        else:
                            lap_in_info = (driver, lap_number, pit_in)
                    else:
                        lap_in_info = (driver, lap_number, pit_in)
                        offset = True

                # print(lap_dict["GAS"])
                for driver_num in session.drivers:
                    driver_details = session.get_driver(driver_num)

                    driver_code = driver_details['Abbreviation']
                    driver_name = driver_details['FullName']
                    position = driver_details['Position']
                    race_dict["Drivers"][driver_name] = {}

                    driver_result = results[results['Abbreviation'] == driver_code]
                    if not driver_result.empty:
                        status = driver_result.iloc[0]['Status']

                    laps = session.laps.pick_driver(driver_code)
                    lap_numbers = laps['LapNumber'].tolist()
                    lap_times = laps['LapTime'].tolist()
                    sector1_times = laps['Sector1Time'].tolist()
                    sector2_times = laps['Sector2Time'].tolist()
                    sector3_times = laps['Sector3Time'].tolist()

                    race_dict["Drivers"][driver_name]["Laps"] = {}
                    race_dict["Drivers"][driver_name]["PitStops"] = {}
                    race_dict["Drivers"][driver_name]["Team"] = driver_details['TeamName']
                    race_dict["Drivers"][driver_name]["Finishing Position"] = position
                    race_dict["Drivers"][driver_name]["Race Status"] = status
                    for i in range(len(lap_numbers)):
                        time_obj = {'lap_time': str(lap_times[i]),
                                    'sector_1': str(sector1_times[i]),
                                    'sector_2': str(sector2_times[i]),
                                    'sector_3': str(sector3_times[i])}
                        race_dict["Drivers"][driver_name]["Laps"][f"lap {i+1}"] = time_obj

                    for i in range(len(lap_dict[driver_code])):
                        pit_obj = {'duration': str(lap_dict[driver_code][i]['duration']),
                                    'oldTire': lap_dict[driver_code][i]['oldTire'],
                                    'newTire': lap_dict[driver_code][i]['newTire']
                                    }
                        race_dict["Drivers"][driver_name]["PitStops"][f"lap {lap_dict[driver_code][i]['lap']}"] = pit_obj

                collection.insert_one(race_dict)
                race_number += 1

                    # except (ValueError):
                    #     print("round does not exist in " + str(year))
                    #     more_races = False

        # except Exception as e:
        #     print(f"Could not retrieve schedule for {year}: {e}")

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

        # for time in self.driverInformationDF.loc[18, 'lapTimes']:
        #     print(time)


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


def get_session_with_retry(year, grand_prix, session_type, retries=3, delay=5):
    for attempt in range(retries):
        try:
            session = fastf1.get_session(year, grand_prix, session_type)
            session.load()
            return session
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503:
                print(f"Attempt {attempt + 1} failed with 503 error. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                raise
    raise Exception(f"Failed to load session after {retries} attempts")
