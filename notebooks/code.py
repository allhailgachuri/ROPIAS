import requests

# The NASA POWER API endpoint
url = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Parameters for our request
# This asks for Kakamega, Kenya - March to April 2022
params = {
    "parameters": "PRECTOTCORR,GWETROOT",
    "community": "AG",
    "longitude": 34.75,
    "latitude": 0.28,
    "start": "20220301",
    "end": "20220430",
    "format": "JSON"
}

# Make the request
response = requests.get(url, params=params, timeout=15)

# Check if it worked
print("Status code:", response.status_code)
print("Success!" if response.status_code == 200 else "Something went wrong")
# ```

# You should see:
# ```
# Status code: 200
# Success!