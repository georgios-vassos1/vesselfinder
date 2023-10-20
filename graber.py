from vessel_tracker.ais_data_scraper import client
from datetime import datetime
import os, json
import asyncio


if __name__ == '__main__':

 ais_data = asyncio.run(client('Linux'))
 # Serialize the ais_data to a JSON string
 json_data = json.dumps(ais_data, indent=4)

 # Define the base directory where you want to store the files
 base_dir = "/app/data"
 # Get the current date
 current_date = datetime.now()
 # Create the directory name in the format 'mtraf_%Y%m'
 dir_name = current_date.strftime("mtraf_%Y%m")
 # Create the full path for the directory
 full_dir_path = os.path.join(base_dir, dir_name)
 # Check if the directory exists, and if not, create it
 if not os.path.exists(full_dir_path):
  os.mkdir(full_dir_path)

 # Generate a timestamp for the JSON filename
 timestamp = current_date.strftime("%Y.%m.%d-%H.%M")
 # Define the path to the JSON file with the timestamp inside the created directory
 json_file_path = os.path.join(full_dir_path, f"mtraf_{timestamp}.json")
 # json_file_path = f"~/vessel_track/data/mtraf_{timestamp}.json"
 # Save the JSON data to a file
 with open(json_file_path, "w") as json_file:
  json_file.write(json_data)

 # Check if the file was saved
 if os.path.exists(json_file_path):
  print(f"DataFrame saved to {json_file_path}")
 else:
  print(f"Failed to save DataFrame to {json_file_path}")
