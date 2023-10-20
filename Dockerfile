# Use a lightweight Linux distribution as a parent image
FROM python:3.12.0-bookworm

# Set the timezone to Spain (CET)
ENV TZ=Europe/Madrid

# Update pip
RUN apt-get update && apt-get install -y chromium &&\
    pip install --no-cache-dir --upgrade pip &&\
    pip --no-cache-dir install build installer

# Set the working directory to /app
WORKDIR /app

# Create the app/data directory
RUN mkdir -p /app/data

# Copy only the script and requirements file into the container
# Copy multiple files and directories to /app/ in one line
COPY License.txt Pipfile.txt README.md pytest.ini requirements.txt setup.cfg setup.py /app/
COPY graber.py /app/

# Copy the tests directory
COPY tests /app/tests/

# Copy the vessel_tracker directory
COPY vessel_tracker /app/vessel_tracker/

# Install any needed packages specified in requirements.txt
RUN python -m build && pip install --no-cache-dir . && python setup.py clean

# Make script executable
# RUN chmod +x toy.py

# Run script.py when the container launches
CMD ["python", "-u", "-B", "graber.py"]
