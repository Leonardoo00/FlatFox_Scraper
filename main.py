import json
import requests
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import os
import time


# Flatfox API 
base_url = "https://flatfox.ch/api/v1/pin/?north={}&south={}&east={}&west={}&max_count={}&max_price={}&min_price={}&moving_date_from={}&moving_date_to={}&offer_type={}&ordering={}"

# Set headers to use for the requests
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}

# Set time to sleep 
sleep_time = 900 

# Setting up logging. Use a rotating file handler to limit the size of the log file and create backups.
logging.basicConfig(
    handlers=[RotatingFileHandler('flatfox_monitor.log', maxBytes=1000000, backupCount=5)],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logging.info('Starting the flatfox monitoring system.') # Starting log

def load_config_json(file_path="config.json"):
    """Load configuration parameters from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)  # Load the full dictionary
    return {}  # Return an empty dictionary if the file doesn't exist

def load_processed_ads(file_path):
    """Load processed ads (PIDs and adDicts) from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)  # Load the full dictionary
    return {}  # Return an empty dictionary if the file doesn't exist

def save_processed_ads(file_path, processed_ads):
    """Save processed ads (PIDs and adDicts) to a JSON file."""
    with open(file_path, "w") as file:
        json.dump(processed_ads, file, indent=4)  # Indent for better readability

def req(url, retries=3, backoff_factor=2):
    """ Make the main request to the API to get the list of adPIDs. """
    for attempt in range(retries):
        try:
            r = requests.get(url=url, headers=headers, timeout=10)  # Make the GET request with a timeout
            r.raise_for_status()  # Raise an exception for HTTP errors
            return r.json()
        except requests.Timeout:
            logging.warning(f"Request timed out (Attempt {attempt + 1}/{retries}). Retrying...")
        except requests.RequestException as e:
            logging.warning(f"Request failed: {e} (Attempt {attempt + 1}/{retries}). Retrying...")

        # Exponential backoff for retries
        if attempt < retries - 1:
            time.sleep(backoff_factor ** attempt)

    logging.error(f"Failed to fetch URL after {retries} attempts.")
    return None

def get_ad_info(adPID, retries=3, backoff_factor=2):
    """ Make the request for scraping specific ad data from API. """

    for attempt in range(retries):
        try:
            req = requests.get(url=f"https://flatfox.ch/api/v1/public-listing/?pk={adPID}&expand=cover_image,author", headers=headers, timeout=10)  # Make the GET request with a timeout
            req.raise_for_status()  # Raise an exception for HTTP errors
            return req.json()
        except requests.Timeout:
            logging.warning(f"Request 2nd timed out (Attempt {attempt + 1}/{retries}). Retrying...")
        except requests.RequestException as e:
            logging.warning(f"Request 2nd failed: {e} (Attempt {attempt + 1}/{retries}). Retrying...")

        # Exponential backoff for retries
        if attempt < retries - 1:
            time.sleep(backoff_factor ** attempt)

    logging.error(f"Failed to fetch URL from 2nd request after {retries} attempts.")
    return None

def discord_notify(adDict, webhook_url):
    """Send a Discord notification for new ads."""
    # Convert the publication date to a human-readable format
    date_object = datetime.fromisoformat(adDict['Data'])
    formatted_date = date_object.strftime("%B %d, %Y %H:%M:%S")  # Example: November 25, 2024 19:29:33

    # Join attributes into a readable format
    attributes = ', '.join(adDict['Attributes']) if adDict['Attributes'] else "No key features listed"

    # Prepare the embed data
    embed = {
        "title": adDict["Title"],
        "url": adDict["URL"],
        "color": 5814783,  # Example color (light blue)
        "fields": [
            {
                "name": "Price",
                "value": f"{adDict['Price']} CHF",
                "inline": True
            },
            {
                "name": "Rooms",
                "value": f"{adDict.get('adRooms', 'N/A')} rooms",
                "inline": True
            },
            {
                "name": "Address",
                "value": adDict["Address"],
                "inline": False
            },
            {
                "name": "Agency",
                "value": adDict["Agency"] if adDict["Agency"] else "No Agency",
                "inline": False
            },
            {
                "name": "Published On",
                "value": formatted_date,
                "inline": False
            },
            {
                "name": "Key Features",
                "value": attributes,
                "inline": False
            }
        ],
        "image": {
            "url": adDict["ImageURL"]
        }
    }

    # Send the POST request to Discord
    data = {
        "username": "Real Estate Monitor",
        "embeds": [embed]  # Discord requires embeds as a list
    }

    response = requests.post(webhook_url, json=data)

    # Log result
    if response.status_code == 204:  # Successful webhook post
        logging.info(f"Webhook sent successfully for ad: {adDict['Title']}")
    else:  # Failed webhook post
        logging.error(f"Failed to send webhook for ad: {adDict['Title']}. Status code: {response.status_code}")

def process_ad(adPID, ad_type):
    """Process individual ad and return its dictionary representation."""

    # Scrape detailed data for the specific ad
    adData = get_ad_info(adPID)
    if adData:
        adData = adData["results"][0]

        # Filter to catch only SHARED_FLAT and APARTMENT
        adType = adData.get("object_type", None)
        if adType not in ad_type:
            return None
        
        logging.info(f"New ad found: {adPID}. Processing...")
        
        adPrice = adData.get("price_display", None) 
        adPublication = adData.get("published", "Unknown")
        adAddress = adData.get("public_address", "Unknown Address")
        adTitle = adData.get("public_title", "No Title Available")
        adRooms = adData.get("number_of_rooms", "Unknown")
        adLink = f"https://flatfox.ch/it/{adPID}"
        adImage = adData.get("cover_image", {}).get("url", None)
        adImageURL = f"https://flatfox.ch{adImage}" if adImage else "No Image Available"


        if not adPrice or not adTitle or not adAddress:
            logging.warning(f"Ad {adPID} has missing data. Skipping...")
            return None
        
        # Process attributes
        try:
            adAttributes = adData.get("attributes", [])
            attributes = [attribute.get("name", "Unknown Attribute") for attribute in adAttributes]
        except ValueError:
            attributes = []

        # Process agency name
        try:
            adAgency = adData.get("agency", {}).get("name", "Unknown Agency")
        except ValueError:
            adAgency = None

        # Create the dictionary for the ad
        adDict = {
            "URL": adLink,               
            "Price": adPrice,             
            "Data": adPublication,
            "Title": adTitle,
            "Attributes": attributes,
            "ImageURL": adImageURL,
            "Agency": adAgency,
            "Address": adAddress,
            "adRooms": adRooms
        }

        logging.info(f"Ad data successfully processed for {adPID}")
        return adDict

def main():
    """Main function to manage the script flow."""
    processed_ads_file = "processed_ads.json"

    # -- SET SEARCH PARAMETERS ACCORDING TO CONFIG.JSON FILE -- #
    config = load_config_json()

    #NOTE: You can find them yourself on https://www.google.com/maps
    north, south, east, west = (
        config["coordinates"]["north"],
        config["coordinates"]["south"],
        config["coordinates"]["east"],
        config["coordinates"]["west"]
    )

    max_price, min_price = (
        config["price_range"]["max_price"],
        config["price_range"]["min_price"]
    )

    moving_date_from = config["moving_date_from"]
    moving_date_to = config["moving_date_to"]
    offer_type = config["offer_type"]
    ordering = config["ordering"]
    max_count = config["max_count"]
    ad_type = config["ad_type"]

    webhook_url = config["webhook_url"]

    url = base_url.format(north, south, east, west, max_count, max_price, min_price, moving_date_from, moving_date_to, offer_type, ordering)

    # Load already processed ads (PIDs and their adDicts)
    processed_ads = load_processed_ads(processed_ads_file)

    # Fetch all ads
    jsonData = req(url)
    if jsonData:
        for ad in jsonData:
            adPID = str(ad["pk"])  # Convert PID to string to match the key in the JSON file
            if adPID not in processed_ads:
                adDict = process_ad(adPID, ad_type)
                if adDict:
                    # Add PID and its adDict to the processed list
                    processed_ads[adPID] = adDict
                    # Send Discord notification
                    discord_notify(adDict, webhook_url)
            else:
                logging.info(f"Ad {adPID} has already been processed. Skipping...")

        # Save updated processed ads (PIDs and their adDicts)
        save_processed_ads(processed_ads_file, processed_ads)
    else:
        logging.warning("Failed to fetch ads. Retrying later...")

# Run the script in a loop
while True:
    main()
    time.sleep(sleep_time) # Sleep before the next check (default to 15 minutes)