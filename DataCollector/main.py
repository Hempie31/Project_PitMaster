import webscraper

DATABASE_URI = "mongodb+srv://admin:admin@f1-cluster.bn1crlr.mongodb.net/?retryWrites=true&w=majority&appName=F1-Cluster"


if __name__ == "__main__":
    webscraperObject = webscraper.WebScraper()
    # webscraperObject.extract_driver_info()
    # webscraperObject.extract_lap_info()
    # for i in range(2019, 2024, 1):
    webscraperObject.iterate_through_races(2022)
