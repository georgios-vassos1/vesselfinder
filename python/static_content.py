def get_static_content(base_url: str, headers: dict):

 req = urllib.request.Request(base_url, None, headers)

 with urllib.request.urlopen(req) as response:
  page_content = response.read()

 parsed_html = BeautifulSoup(page_content, 'html.parser')

 return (
  parsed_html.find_all("h2", class_=['bar']),
  parsed_html.find_all("table", class_=['aparams','tparams'])
 )


def scrape_static_table(titles: bs4.element.ResultSet, tables: bs4.element.ResultSet, idx:list = [0,3,3]) -> dict:

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


def get_vesselfinder_static(IMOs: list, headers: dict=None, limit: int=10) -> dict:

 vf_details = {}
 exceptions = {}

 for j, IMO in enumerate(IMOs[:limit]):
  base_url = f"https://www.vesselfinder.com/en/vessels/details/{IMO}"

  try:
   static_content = get_static_content(base_url, headers)
   vf_details[IMO] = scrape_static_table(*static_content)
  except Exception as e:
   print(f"An exception occurred for {IMO}: {e}")
   exceptions[IMO] = e

  print(f"{j+1} Vessels Completed", end='\r', flush=True)

 return vf_details, exceptions
