import webscraper


if __name__ == "__main__":
    webscraperObject = webscraper.WebScraper()
    # webscraperObject.extract_driver_info()
    # webscraperObject.extract_lap_info()
    webscraperObject.iterate_through_races()
