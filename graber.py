from vessel_tracker.ais_data_scraper import client
from datetime import datetime
import os, json
import asyncio


if __name__ == '__main__':
 # loop = asyncio.get_event_loop()
 # loop.run_until_complete(client())

 ais_data = asyncio.run(client('Linux'))
 # print(ais_data)

 # Serialize the ais_data to a JSON string
 json_data = json.dumps(ais_data, indent=4)
 # Generate a timestamp for the CSV filename
 timestamp = datetime.now().strftime("%Y.%m.%d-%H.%M")
 # Define the path to the CSV file with the timestamp
 json_file_path = f"/app/data/mtraf_{timestamp}.json"
 # json_file_path = f"~/vessel_track/data/mtraf_{timestamp}.json"
 # Save the JSON data to a file
 with open(json_file_path, "w") as json_file:
  json_file.write(json_data)

 # Check if the file was saved
 if os.path.exists(json_file_path):
  print(f"DataFrame saved to {json_file_path}")
 else:
  print(f"Failed to save DataFrame to {json_file_path}")
