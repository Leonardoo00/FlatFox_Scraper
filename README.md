# Flatfox Real Estate Monitor

This Python script monitors the [Flatfox](https://flatfox.ch) real estate platform for new rental listings based on customizable search criteria. When a new listing is found, it sends a detailed notification to a Discord channel using a webhook. Perfect for staying updated on available apartments or shared flats in your desired area.

---

## Features

- **Customizable Search Parameters**: Define your search area, price range, moving dates, and more in a `config.json` file.
- **Real-Time Discord Notifications**: Receive instant updates in your Discord channel with detailed information about new listings.
- **Persistent Storage**: Tracks processed listings to avoid duplicate notifications.
- **Detailed Logging**: Logs all actions for easy monitoring and debugging.
- **Automatic Updates**: Runs in a loop, checking for new listings at regular intervals.

---

## Prerequisites

- Python 3.x
- `requests` library (install via `pip install requests`)

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/flatfox-monitor.git
   cd flatfox-monitor
   ```

2. Install the required Python package:
   ```bash
   pip install requests
   ```

3. Create a `config.json` file in the root directory with the following structure:
   ```json
   {
       "coordinates": {
           "north": 47.1234,
           "south": 47.0000,
           "east": 8.5678,
           "west": 8.4321
       },
       "price_range": {
           "max_price": 2000,
           "min_price": 1000
       },
       "moving_date_from": "2024-01-01",
       "moving_date_to": "2024-12-31",
       "offer_type": "rent",
       "ordering": "-published",
       "max_count": 50,
       "ad_type": ["SHARED_FLAT", "APARTMENT"],
       "webhook_url": "https://discord.com/api/webhooks/your-webhook-url"
   }
   ```
   Replace the values with your desired search parameters and Discord webhook URL.

4. Run the script:
   ```bash
   python main.py
   ```

---

## How It Works

1. The script fetches listings from the Flatfox API based on the parameters defined in `config.json`.
2. It checks if each listing has already been processed by referencing a `processed_ads.json` file.
3. If a new listing is found, it extracts details such as price, address, rooms, and key features.
4. A Discord notification is sent with an embed containing the listing details and an image.
5. The script runs in a loop, checking for new listings every 15 minutes (default).

---

## Example Discord Notification

When a new listing is found, you'll receive a notification like this in your Discord channel:

![Discord Notification Example](https://imgur.com/qzDZLmk)

---

## Customization

- **Search Area**: Adjust the `north`, `south`, `east`, and `west` coordinates in `config.json` to define your desired area.
- **Price Range**: Modify `max_price` and `min_price` to filter listings within your budget.
- **Moving Dates**: Set `moving_date_from` and `moving_date_to` to find listings available during your preferred timeframe.
- **Ad Types**: Specify the types of listings you're interested in (e.g., `SHARED_FLAT`, `APARTMENT`).
- **Check Interval**: Change the `sleep_time` variable in `main.py` to adjust how often the script checks for new listings.

---

## Logging

The script logs all actions to `flatfox_monitor.log`, with a rotating file handler to prevent large log files. Logs include timestamps, log levels, and messages for easy debugging.

---

## Contributing

Contributions are welcome! If you have suggestions or improvements, feel free to open an issue or submit a pull request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Disclaimer

This script is for personal use only. Please respect Flatfox's terms of service and avoid overloading their servers with excessive requests.

---

Happy house hunting! 🏠