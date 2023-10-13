import asyncio
import aiohttp
import re

from playwright.async_api import async_playwright
from playwright.async_api._generated import Request as HTTPRequest
from typing import List


async def getXHR(brw_name: str, brw_path: str, url: str = 'https://www.marinetraffic.com/en/ais') -> list:

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
 # while True:
 #  ais_data = await asyncio.gather(*(fetch_data(session, url, headers) for url in ais))
 #  # Process the ais_data as needed
 #  await asyncio.sleep(300)  # Sleep for 5 minutes (300 seconds)


async def client():
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
 xhr_requests = await getXHR('chromium', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
 ais = await get_AIS_XHR(xhr_requests)
 ais_data = await get_ais_data(ais[:2], headers)
 return ais_data


if __name__ == '__main__':
 ais_data = asyncio.run(client())
 # print(ais_data)
 # loop = asyncio.get_event_loop()
 # loop.run_until_complete(client())


