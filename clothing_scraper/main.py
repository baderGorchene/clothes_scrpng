import argparse
import logging
import sys

from clothing_scraper.scrapers import bershka as bershka_module
from clothing_scraper.core.logging import configure_logging


def main(argv=None):
    configure_logging()
    parser = argparse.ArgumentParser(prog="clothing_scraper")
    subparsers = parser.add_subparsers(dest="command")

    # API command (placeholder)
    subparsers.add_parser("api", help="Run the FastAPI app (placeholder)")

    # Scrape command
    scrape = subparsers.add_parser("scrape", help="Run a spider")
    scrape.add_argument("--spider", required=True, help="Name of the spider to run (e.g. bershka)")
    scrape.add_argument("--url", help="Category URL to scrape")
    scrape.add_argument("--output", help="Output filename (jsonl)")

    # setup-db command (placeholder)
    subparsers.add_parser("setup-db", help="Run DB setup (placeholder)")

    args = parser.parse_args(argv)

    if args.command == "api":
        logging.info("Starting API (not implemented in this PR). Use uvicorn or run via Docker Compose.")
        return 0

    if args.command == "scrape":
        spider = args.spider.lower()
        if spider == "bershka":
            url = args.url or "https://www.bershka.com/fr/homme/vetements/t-shirts-n3294.html?celement=1010193239"
            output = args.output or "bershka_tshirts_scraped_data.jsonl"
            count = bershka_module.scrape_bershka_tshirts(url, output)
            logging.info(f"Scraped {count} products")
            return 0
        else:
            logging.error(f"Unknown spider: {spider}")
            return 2

    if args.command == "setup-db":
        logging.info("DB setup not implemented in this PR. Run migrations or setup scripts as needed.")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
