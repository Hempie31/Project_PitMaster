import requests
from tika import parser
import re
import pandas as pd
import tabula

info_url = "https://www.fia.com/sites/default/files/doc_15_-_2022_saudi_arabian_grand_prix_-_entry_list.pdf"
lapTimes_url = "https://www.fia.com/sites/default/files/2022_02_ksa_f1_r0_timing_racelapanalysis_v01.pdf"


def extract_driver_info(info_url):
    
    # Extract tables from PDF
    tables = tabula.read_pdf(info_url, pages='all', multiple_tables=True)

    # Assuming the relevant table is the first one extracted
    dataframe = tables[0].drop([0, 1])

    dataframe = dataframe.rename(columns={'Unnamed: 0': 'Number', 'Unnamed: 1': 'Name', 'Unnamed: 2': 'Nationality', 'Unnamed: 3': 'Team', 'Unnamed: 4': 'Constructor'})

    for i in dataframe['Number']:
        dataframe.replace(to_replace=i, value=int(i), inplace=True)

    dataframe = dataframe.sort_values(by=['Number'])

    # Display the extracted table
    # print (df.columns)
    # print(df)
    return dataframe


if __name__ == "__main__":

    df = extract_driver_info(info_url)
    print (df)
