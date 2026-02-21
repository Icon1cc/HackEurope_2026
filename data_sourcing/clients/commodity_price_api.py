"""
CommodityPriceAPI client — https://commoditypriceapi.com
API key: set COMMODITY_PRICE_API_KEY in .env

WHAT IT GIVES YOU
-----------------
Real-time and historical prices for 130+ commodities across 6 categories:

  Metals      XAU (Gold, T.oz), XAG (Silver, T.oz), HG-SPOT (Copper, $/lb),
              AL-SPOT/AL-FUT (Aluminium, $/t), NICKEL-SPOT/NICKEL-FUT ($/t),
              ZINC ($/t), TIN ($/t), LEAD-SPOT/LEAD-FUT ($/t),
              HRC-STEEL (Hot-Rolled Coil Steel, $/t), STEEL (CNY/t),
              TIOC (Iron Ore 62%, $/t), PL (Platinum), PA (Palladium),
              COB (Cobalt), LC (Lithium, CNY/t), TITAN (Titanium, CNY/kg),
              MG (Magnesium, CNY/t), NDYM (Neodymium, CNY/t),
              CHROM (Chromium), VANPENT (Vanadium), MANGELE (Manganese),
              LMMODY (Molybdenum), SILLUMP (Silicon), XRH (Rhodium)

  Energy      WTIOIL-FUT/SPOT (WTI Crude, $/bbl), BRENTOIL-FUT/SPOT (Brent, $/bbl),
              NG-FUT/SPOT (Natural Gas, $/MMBtu), COAL, LNG, TTF-GAS,
              LGO (Gas Oil), PROP (Propane), METH (Methanol), NAPHTHA,
              UXA (Uranium), ETHANOL

  Industrial  LB-FUT (Lumber), RUBBER, COB (Cobalt), POL (Polyethylene),
              PVC, PYL (Polypropylene), SODASH (Soda Ash), BIT (Bitumen),
              K-PULP (Kraft Pulp), GA (Gallium), INDIUM, TEL (Tellurium),
              UREA, DIAPH (Diammonium Phosphate)

  Agriculture Wheat, Corn, Soybeans, Cotton, Sugar, Coffee, Cocoa, Palm Oil,
              Canola, Rice, Soybean Oil/Meal, Oats, etc.

  Livestock   Cattle, Lean Hogs, Poultry, Salmon, Eggs, Beef, etc.
  Raw Mat.    Logs, Sawnwood, Plywood, Rubber RSS3/TSR20, Phosphate Rock, etc.

HOW IT WORKS
------------
- Base URL: https://api.commoditypriceapi.com/v2
- Auth: x-api-key request header (set via COMMODITY_PRICE_API_KEY env var)
- All rates returned as direct price in the commodity's native quote currency
  (no inversion needed — e.g. XAU: 5107.23 means $5107.23 per troy oz)
- Historical data available back to 1990-01-01
- Update frequency: per-minute for most active symbols (Lite plan: 10min delay)
- Lite plan: 2000 calls/mo, max 5 symbols per request, no custom quote currency

ENDPOINTS
---------
  /usage               → quota info (no success field in response)
  /symbols             → full symbol catalog with units/currencies
  /rates/latest        → spot prices for requested symbols
  /rates/historical    → OHLC for a specific date
  /rates/time-series   → daily OHLC over a date range (max 1 year)
  /rates/fluctuation   → startRate/endRate/change/changePercent between two dates
"""

import os
import httpx
from datetime import date


BASE_URL = "https://api.commoditypriceapi.com/v2"

# B2B/BOM-relevant symbols confirmed from /symbols endpoint
# Note: HG-SPOT (Copper) is per LB — multiply by 2204.62 for $/tonne
# Note: STEEL and several minor metals are priced in CNY
BOM_METALS = ["XAU", "XAG", "HG-SPOT", "AL-SPOT", "NICKEL-SPOT", "ZINC", "TIN", "LEAD-SPOT"]
BOM_ENERGY = ["WTIOIL-FUT", "BRENTOIL-FUT", "NG-FUT"]


class CommodityPriceApiClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("COMMODITY_PRICE_API_KEY", "")
        if not self.api_key:
            raise EnvironmentError("COMMODITY_PRICE_API_KEY not set")
        self._headers = {"x-api-key": self.api_key}

    def _get(self, path: str, check_success: bool = True, **params) -> dict:
        with httpx.Client() as client:
            resp = client.get(f"{BASE_URL}/{path}", params=params, headers=self._headers)
        resp.raise_for_status()
        data = resp.json()
        if check_success and not data.get("success"):
            raise RuntimeError(f"commoditypriceapi error: {data}")
        return data

    def usage(self) -> dict:
        """Account quota. Returns: {"plan": ..., "quota": ..., "used": ...}"""
        return self._get("usage", check_success=False)

    def symbols(self) -> list[dict]:
        """Full symbol catalog with category, unit, currency, update interval."""
        return self._get("symbols")["symbols"]

    def latest(self, symbols: list[str], quote: str | None = None) -> dict:
        """
        Latest spot prices (10min delay on Lite).
        symbols: max 5 on Lite, 10 on Plus, 20 on Premium
        quote: custom quote currency e.g. "EUR" — Plus/Premium only
        Returns: {"rates": {"XAU": 5107.23, ...}, "metadata": {"XAU": {"unit": "T.oz", "quote": "USD"}}}
        """
        assert symbols, "symbols must be non-empty"
        params: dict = {"symbols": ",".join(symbols)}
        if quote:
            params["quote"] = quote
        return self._get("rates/latest", **params)

    def historical(self, day: date, symbols: list[str]) -> dict:
        """
        OHLC for a specific date (back to 1990-01-01).
        Returns: {"date": "...", "rates": {"XAU": {"open": ..., "high": ..., "low": ..., "close": ...}}}
        """
        assert symbols, "symbols must be non-empty"
        return self._get("rates/historical", symbols=",".join(symbols), date=day.isoformat())

    def timeseries(self, start: date, end: date, symbols: list[str]) -> dict:
        """
        Daily OHLC over a date range (max 1 year).
        Returns: {"rates": {"2024-01-01": {"XAU": {open/high/low/close}}, ...}}
        """
        assert symbols, "symbols must be non-empty"
        assert start <= end, "start must be <= end"
        return self._get(
            "rates/time-series",
            symbols=",".join(symbols),
            startDate=start.isoformat(),
            endDate=end.isoformat(),
        )

    def fluctuation(self, start: date, end: date, symbols: list[str]) -> dict:
        """
        Price change between two dates.
        Returns: {"rates": {"XAU": {"startRate": ..., "endRate": ..., "change": ..., "changePercent": ...}}}
        """
        assert symbols, "symbols must be non-empty"
        assert start <= end, "start must be <= end"
        return self._get(
            "rates/fluctuation",
            symbols=",".join(symbols),
            startDate=start.isoformat(),
            endDate=end.isoformat(),
        )
