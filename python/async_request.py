import aiohttp
import asyncio

async def scrape_dynamic_table(api_url: str, headers: dict = None, params: dict = None) -> dict:
 async with aiohttp.ClientSession() as session:
  async with session.get(api_url, params=params, headers=headers) as response:
   response.raise_for_status()
   return await response.json()

async def get_vesselfinder_dynamic(MMSIs: list, headers: dict = None, request_delay: float = 1.0) -> dict:
 vf_details = {}
 exceptions = {}

 async with aiohttp.ClientSession() as session:
  tasks = []

  for j, MMSI in enumerate(MMSIs):
   api_url = f"https://www.vesselfinder.com/api/pub/pcext/v4/{MMSI}?d"

   try:
    task = asyncio.create_task(scrape_dynamic_table(api_url, headers))
    tasks.append(task)
   except Exception as e:
    print(f"An exception occurred for {MMSI}: {e}")
    exceptions[MMSI] = e

   # Introduce a delay between requests
   await asyncio.sleep(request_delay)

  results = await asyncio.gather(*tasks)

  for j, MMSI in enumerate(MMSIs):
   vf_details[MMSI] = results[j]

 return vf_details, exceptions

if __name__ == '__main__':
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) '
                      'Chrome/91.0.4472.124 '
                      'Safari/537.11',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'
    }

    MMSI = 228386800

    # You can adjust the request delay as needed, for example, 1.0 seconds.
    loop   = asyncio.get_event_loop()
    result = loop.run_until_complete(get_vesselfinder_dynamic([MMSI], headers, request_delay=1.0))
    print(result)

