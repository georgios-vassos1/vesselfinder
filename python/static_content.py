import bs4

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from typing import List, Tuple, Dict


def get_static_content(base_url: str, headers: dict, elements: dict) -> Tuple[List[bs4.element.Tag], bs4.BeautifulSoup]:
 try:
  req = Request(base_url, None, headers)
  with urlopen(req) as response:
   page_content = response.read()
  parsed_html = BeautifulSoup(page_content, 'html.parser')
  found_elements = tuple(parsed_html.find_all(name=k, class_=v) for k, v in elements.items())
  return found_elements, parsed_html
 except Exception as e:
  # Add appropriate error handling here, e.g., log the error
  return tuple(), None


def scrape_vesselfinder_details(titles: bs4.element.ResultSet, tables: bs4.element.ResultSet) -> Dict[str, Dict[str, any]]:
 idx = [0,3,3]
 D = {}
 for j, table in enumerate(tables[:3]):
  tbx = titles[idx[j]].text.strip()
  D[tbx] = {}
  for row in table.find_all('tr'):
   columns = row.find_all('td')
   key   = columns[0].text.strip()
   value = columns[1].text.strip()
   D[tbx][key] = value
 return D


def get_vesselfinder_static(IMOs: list, headers: dict=None) -> Tuple[Dict[int, Dict[str, Dict[str, str]]], Dict[int, str]]:
 elements = {'h2': 'bar', 'table': ['aparams','tparams']}
 vf_details = {}
 exceptions = {}

 for j, IMO in enumerate(IMOs):
  base_url = f"https://www.vesselfinder.com/en/vessels/details/{IMO}"
  try:
   static_content, _  = get_static_content(base_url, headers, elements)
   vf_details[IMO] = scrape_vesselfinder_details(*static_content)
  except Exception as e:
   print(f"An exception occurred for {IMO}: {e}")
   exceptions[IMO] = e
  print(f"{j+1} Vessels Completed", end='\r', flush=True)

 return vf_details, exceptions


if __name__ == '__main__':
 import os
 import pandas as pd

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

 data_path = os.path.join(os.getcwd(), "..", "data", "imo-vessel-codes.csv")
 if os.path.exists(data_path):
  # Read the CSV file into a DataFrame
  df = pd.read_csv(data_path)
 else:
  print(f"The CSV file '{data_path}' does not exist.")

 IMOs = list(df.imo.unique())

 vf_details, _ = get_vesselfinder_static(IMOs[:2], headers)
 print(vf_details)

