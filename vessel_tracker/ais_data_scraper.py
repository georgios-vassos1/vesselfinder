import asyncio
import aiohttp
import re

from playwright.async_api import async_playwright
from playwright.async_api._generated import Request as HTTPRequest
from typing import List


async def getXHR(brw_name: str, brw_path: str, url: str = 'https://www.marinetraffic.com/en/ais/home/centerx:22.1/centery:10.0/zoom:2') -> list:

 async with async_playwright() as p:
  browser = await p[brw_name].launch(executable_path=brw_path)
  page = await browser.new_page()

  # Enable network interception
  await page.route('**/*', lambda route, request: route.continue_())
  # Set up an event listener for XHR requests
  xhr_requests = []
  page.on('request', lambda request: xhr_requests.append(request))
  # Navigate to the web page
  await page.goto(url)
  # Wait for XHR requests to complete (you can customize this part)
  await page.wait_for_timeout(5000)  # Wait for 5 seconds (adjust as needed)

  await browser.close()

  return xhr_requests


async def is_matching_url(request, url_pattern):
 return url_pattern.search(request.url)


async def get_AIS_XHR(XHRs: List[HTTPRequest]) -> List[str]:
 url_pattern = re.compile(re.escape('/get_data_json_4/z:') + r'\d+/X:' + r'\d+/Y:' + r'\d+/station:0')

 tasks = [is_matching_url(request, url_pattern) for request in XHRs]
 matching_results = await asyncio.gather(*tasks)

 ais_xhr = [request.url for request, is_matching in zip(XHRs, matching_results) if is_matching]

 return ais_xhr


async def fetch_data(session: aiohttp.ClientSession, url: str, headers: dict = None) -> dict:
 try:
  async with session.get(url, headers=headers) as response:
   response.raise_for_status()
   return await response.json()
 except Exception as e:
  print(f"An error occurred while fetching {url}: {e}")
  return None


async def get_ais_data(ais: list, headers: dict = None) -> dict:
 async with aiohttp.ClientSession() as session:
  ais_data = await asyncio.gather(*(fetch_data(session, url, headers) for url in ais))
 return ais_data

## Bad practice
# async def get_ais_data(ais: list, headers: dict = None) -> dict:
#  while True:
#   ais_data = await asyncio.gather(*(fetch_data(session, url, headers) for url in ais))
#   # Process the ais_data as needed
#   await asyncio.sleep(300)  # Sleep for 5 minutes (300 seconds)


async def client(os_name: str='MacOS'):
 from vessel_tracker.config import headers_
 from vessel_tracker.config import chrome_

 xhr_requests = await getXHR(*chrome_[os_name])
 ais_links    = await get_AIS_XHR(xhr_requests)
 ais_data     = await get_ais_data(ais_links, headers_)

 return ais_data


async def __client(os_name: str='MacOS'):
 from config import headers_
 from config import chrome_

 xhr_requests = await getXHR(*chrome_[os_name])
 ais_links    = await get_AIS_XHR(xhr_requests)
 ais_data     = await get_ais_data(ais_links, headers_)

 return ais_data


if __name__ == '__main__':
 # loop = asyncio.get_event_loop()
 # loop.run_until_complete(client())
 import json, os
 from datetime import datetime

 ais_data = asyncio.run(__client())
 # print(ais_data)

 # Serialize the ais_data to a JSON string
 json_data = json.dumps(ais_data, indent=4)
 # Generate a timestamp for the CSV filename
 timestamp = datetime.now().strftime("%Y.%m.%d-%H.%M")
 # Define the path to the CSV file with the timestamp
 # json_file_path = f"/app/data/mtraf_{timestamp}.json"
 json_file_path = f"/Users/gva/vessel_track/data/mtraf_{timestamp}.json"
 # Save the JSON data to a file
 with open(json_file_path, "w") as json_file:
  json_file.write(json_data)

 # Check if the file was saved
 if os.path.exists(json_file_path):
  print(f"DataFrame saved to {json_file_path}")
 else:
  print(f"Failed to save DataFrame to {json_file_path}")
