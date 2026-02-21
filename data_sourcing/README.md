# data-sourcing

Market data sourcing for B2B procurement / BOM / invoice price validation.

## Cloud Pricing Scraper

**`clients/cloud_pricing_scraper.py`** scrapes on-demand compute pricing from [cloudprice.net](https://cloudprice.net) for AWS, GCP, and Azure.

**How it works:** Playwright launches a headless Chromium browser, navigates to each provider's pricing page, waits for the JS-rendered table to populate, then extracts all rows via DOM queries. Each provider's column layout is mapped to a unified schema (`provider`, `instance_type`, `vcpus`, `memory_gib`, `price_usd_hr`, ...). Results are written to JSON.

```bash
uv run python -m clients.cloud_pricing_scraper --out data/cloud_pricing.json
```

Output: `~2922 records` across AWS (1169), GCP (480), Azure (1273), timestamped and tagged `pricing_type: on_demand`.

### Output Schema

Top-level JSON envelope:

| Field | Type | Description |
|---|---|---|
| `scraped_at` | string (ISO 8601) | UTC timestamp of scrape |
| `source` | string | `"cloudprice.net"` |
| `pricing_type` | string | `"on_demand"` |
| `currency` | string | `"USD"` |
| `records` | array | List of instance records (all providers) |

Per-record fields (all providers):

| Field | Type | Providers | Description |
|---|---|---|---|
| `provider` | string | all | `"aws"` / `"gcp"` / `"azure"` |
| `instance_type` | string | all | e.g. `m5.xlarge`, `n2-standard-4`, `Standard_D4s_v5` |
| `family` | string | aws, gcp | Instance family / category |
| `vcpus` | float | all | Number of vCPUs |
| `memory_gib` | float | all | RAM in GiB |
| `price_usd_hr` | float | all | On-demand price in USD/hr (Linux for Azure) |
| `arch` | string | aws | CPU architecture e.g. `x86_64`, `arm64` |
| `gpu` | bool | aws | Whether instance has a GPU |
| `best_region` | string | all | Cheapest region and % diff e.g. `"US East (Virginia) / 0%"` |
| `linux_price_usd_hr` | float | azure | Linux on-demand price USD/hr |
| `windows_price_usd_hr` | float | azure | Windows on-demand price USD/hr |
