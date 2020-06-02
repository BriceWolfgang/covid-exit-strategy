import json
import os

import pandas as pd
import requests

from covid.constants import PATH_TO_SERVICE_ACCOUNT_KEY
from covid.load import get_sheets_client


DATE_SOURCE_FIELD = "date"
STATE_SOURCE_FIELD = "state"
CAPITAL_STATE_SOURCE_FIELD = "State"
TOTAL_CASES_SOURCE_FIELD = "positive"
NEW_CASES_NEGATIVE_SOURCE_FIELD = "negativeIncrease"
NEW_CASES_POSITIVE_SOURCE_FIELD = "positiveIncrease"
LAST_UPDATED_SOURCE_FIELD = "dateModified"

# For bed utilization data
MASTER_DATA_GOOGLE_SHEET_KEY = (
    "1ZhwP0GZTz50myibSaWsMXOVQKx9DQaJO4rN1i58Rrjc"  # covidexitstrategy.org sheet
)
INPATIENT_BEDS_TAB_NAME = "cdc.gov - % inpatient beds"
ICU_BEDS_TAB_NAME = "cdc.gov - % icu beds"
PERCENT_ICU_BEDS_OCCUPIED_FIELD = "% of ICU Beds Occupied"
PERCENT_INPATIENT_BEDS_OCCUPIED = "% of Inpatient Beds Occupied"


def _df_from_tab_name(sheet, tab_name, index_column):
    worksheet = sheet.worksheet(tab_name)
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    if index_column is not None:
        df = df.set_index(index_column)
    return df


def extract_covidtracking_current_data():
    current_url = "https://covidtracking.com/api/v1/states/current.json"
    current_data = requests.get(current_url).json()
    current_df = pd.DataFrame(current_data)

    return current_df


def extract_covidtracking_historical_data():
    historical_url = "https://covidtracking.com/api/v1/states/daily.json"
    historical_data = requests.get(historical_url).json()
    historical_df = pd.DataFrame(historical_data)

    historical_df[DATE_SOURCE_FIELD] = historical_df[DATE_SOURCE_FIELD].astype(str)

    return historical_df


def extract_gsheets_hospital_bed_data():
    client, _ = get_sheets_client(
        credential_file_path=os.path.abspath(PATH_TO_SERVICE_ACCOUNT_KEY)
    )
    master_sheet = client.open_by_key(MASTER_DATA_GOOGLE_SHEET_KEY)

    bed_dfs = []
    for worksheet_title in [INPATIENT_BEDS_TAB_NAME, ICU_BEDS_TAB_NAME]:
        df = _df_from_tab_name(
            master_sheet, worksheet_title, index_column=CAPITAL_STATE_SOURCE_FIELD
        )
        bed_dfs.append(df)

    bed_df = pd.concat(bed_dfs, axis=1)
    bed_df_subset = bed_df[
        [PERCENT_ICU_BEDS_OCCUPIED_FIELD, PERCENT_INPATIENT_BEDS_OCCUPIED]
    ]
    bed_df_decimals = bed_df_subset.applymap(
        lambda x: round(float(x.strip("%")) / 100, 2)
    )
    return bed_df_decimals


def extract_state_population_data():
    # Note that the working directory is assumed to be the repository root.
    df = pd.read_csv("./covid/data/population.csv")

    df = df.set_index(keys=[STATE_SOURCE_FIELD])

    return df


def get_state_abbreviations_to_names():
    with open("./covid/data/us_state_abbreviations.json") as state_abbreviations_file:
        abbreviations = json.load(state_abbreviations_file)

    return abbreviations
