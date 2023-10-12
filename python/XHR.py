import asyncio
from playwright.async_api import async_playwright


async def getXHR(brw_name: str, brw_path: str, url: str = 'https://www.marinetraffic.com/en/ais'):

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


async def client(brw: str = 'chromium'):
 if brw == 'firefox':
  path_to_brw = '/Applications/Firefox.app/Contents/MacOS/firefox'
 else:
  path_to_brw = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

 xhr_requests = await getXHR('chromium', path_to_brw)
 # Process the XHR requests here, for example, printing their URLs
 for request in xhr_requests:
  print(request.url)


if __name__ == '__main__':
    asyncio.run(client())
