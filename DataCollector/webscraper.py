# import requests
from tika import parser
# import pandas as pd
import tabula

DRIVER_INFO_URL = "https://www.fia.com/sites/default/files/" \
                "doc_15_-_2022_saudi_arabian_grand_prix_-_entry_list.pdf"
LAP_TIMES_URL = "https://www.fia.com/sites/default/files/" \
                "2022_02_ksa_f1_r0_timing_racelapanalysis_v01.pdf"


class WebScraper:

    def __init__(self):
        self.driverInformationDF = {}

    def extract_driver_info(self):

        # Extract tables from PDF
        tables = tabula.read_pdf(DRIVER_INFO_URL,
                                 pages='all',
                                 multiple_tables=True)

        # Assuming the relevant table is the first one extracted
        self.driverInformationDF = tables[0].drop([0, 1])

        self.driverInformationDF = self.driverInformationDF.rename(
            columns={'Unnamed: 0': 'Number',
                     'Unnamed: 1': 'Name',
                     'Unnamed: 2': 'Nationality',
                     'Unnamed: 3': 'Team',
                     'Unnamed: 4': 'Constructor'})

        self.driverInformationDF["lapTimes"] = ""

        for i in self.driverInformationDF['Number']:
            self.driverInformationDF.replace(to_replace=i, value=int(i),
                                             inplace=True)

        self.driverInformationDF = self.driverInformationDF.sort_values(
            by=['Number']
            )

        # Display the extracted table
        print(self.driverInformationDF)

    def extract_lap_info(self):

        print("Extracting lap info...")
        # driverNames = self.driverInformationDF['Name'].tolist()
        rawLapTimeData = parser.from_file(LAP_TIMES_URL)
        print(rawLapTimeData['content'])
