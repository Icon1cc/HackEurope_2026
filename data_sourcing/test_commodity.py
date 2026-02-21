"""Quick smoke test for CommodityPriceApiClient."""
import os, json
from pathlib import Path
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from clients.commodity_price_api import CommodityPriceApiClient

client = CommodityPriceApiClient()

print("=== USAGE ===")
print(json.dumps(client.usage(), indent=2))

print("\n=== ALL SYMBOLS ===")
symbols = client.symbols()
print(json.dumps(symbols, indent=2))

print("\n=== LATEST (XAU, XAG, HG-SPOT) ===")
print(json.dumps(client.latest(["XAU", "XAG", "HG-SPOT"]), indent=2))

print("\n=== HISTORICAL XAU + HG-SPOT 2025-01-15 ===")
print(json.dumps(client.historical(date(2025, 1, 15), ["XAU", "HG-SPOT"]), indent=2))

print("\n=== FLUCTUATION last 7 days ===")
end = date.today() - timedelta(days=1)
start = end - timedelta(days=7)
print(json.dumps(client.fluctuation(start, end, ["XAU", "HG-SPOT"]), indent=2))
