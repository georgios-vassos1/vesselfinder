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
   dynamic_content = scrape_dynamic_table(api_url, headers)
  except Exception as e:
   print(f"An exception occurred for {MMSI}: {e}")
   exceptions[MMSI] = e

  print(f"{j+1} Vessels Completed", end='\r', flush=True)

 return dynamic_content, exceptions


if __name__ == '__main__':

 headers = {
  'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) \
                 Chrome/91.0.4472.124 \
                 Safari/537.11',
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
  'Accept-Encoding': 'none',
  'Accept-Language': 'en-US,en;q=0.8',
  'Connection': 'keep-alive'
 }

 MMSI = 228386800
 print(get_vesselfinder_dynamic([MMSI], headers))
