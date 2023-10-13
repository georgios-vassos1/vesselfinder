import requests
import json


def scrape_dynamic_table(api_url: str, headers: dict=None, params: dict=None) -> dict:

 session = requests.Session()

 response = session.get(api_url, params=params, headers=headers)
 response.raise_for_status()

 return response.json()


def get_vesselfinder_dynamic(MMSIs: list, headers: dict=None, limit: int=10) -> dict:

 vf_details = {}
 exceptions = {}

 for j, MMSI in enumerate(MMSIs[:limit]):
  api_url = f"https://www.vesselfinder.com/api/pub/pcext/v4/{MMSI}?d"

  try:
   dynamic_content = get_dynamic_content(base_url, headers)
  except Exception as e:
   print(f"An exception occurred for {IMO}: {e}")
   exceptions[IMO] = e

  print(f"{j+1} Vessels Completed", end='\r', flush=True)

 return dynamic_content, exceptions

