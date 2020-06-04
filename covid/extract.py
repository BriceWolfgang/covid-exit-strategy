import json
from io import BytesIO

import pandas as pd
import requests

from covid.extract_utils import unzip_string


# Define the names of the CSVs returned by the CDC's FluView dashboard API.
# Note: data contained in these CSVs are used to calculate influenza-like-illness (ILI) criteria.
ILI_NET_CSV = "ILINet.csv"
WHO_NREVSS_PUBLIC_HEALTH_LABS_CSV = "WHO_NREVSS_Public_Health_Labs.csv"
WHO_NREVSS_CLINICAL_LABS_CSV = "WHO_NREVSS_Clinical_Labs.csv"


DATE_SOURCE_FIELD = "date"
STATE_SOURCE_FIELD = "state"
TOTAL_CASES_SOURCE_FIELD = "positive"
NEW_CASES_NEGATIVE_SOURCE_FIELD = "negativeIncrease"
NEW_CASES_POSITIVE_SOURCE_FIELD = "positiveIncrease"
LAST_UPDATED_SOURCE_FIELD = "dateModified"


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


def extract_state_population_data():
    # Note that the working directory is assumed to be the repository root.
    df = pd.read_csv("./covid/data/population.csv")

    df = df.set_index(keys=[STATE_SOURCE_FIELD])

    return df


def get_state_abbreviations_to_names():
    with open("./covid/data/us_state_abbreviations.json") as state_abbreviations_file:
        abbreviations = json.load(state_abbreviations_file)

    return abbreviations


def extract_cdc_ili_data():
    current_url = "https://gis.cdc.gov/grasp/flu2/PostPhase02DataDownload"
    payload = {
        "AppVersion": "Public",
        "DatasourceDT": [{"ID": 0, "Name": "WHO_NREVSS"}, {"ID": 1, "Name": "ILINet"}],
        "RegionTypeId": 5,
        # Request all 59 regions.
        "SubRegionsDT": [{"ID": i, "Name": i} for i in range(1, 60)],
        "SeasonsDT": [{"ID": 59, "Name": "59"}],
    }

    response = requests.post(
        url=current_url,
        headers={"Content-Type": "application/json;charset=UTF-8"},
        data=json.dumps(payload),
    )
    filenames_to_contents_map = unzip_string(response.content)

    df = pd.read_csv(BytesIO(filenames_to_contents_map[ILI_NET_CSV]))

    return df
