from .base import Tool


class SqlDatabaseTool(Tool):
    name = "sql_database"
    description = "Query a SQL database for invoice history and commodity prices"

    def run(self, **kwargs) -> dict:
        # TODO: implement DB connection + query dispatch
        raise NotImplementedError

    def query(self, sql: str) -> dict:
        # TODO: execute arbitrary SQL
        raise NotImplementedError

    def fetch_invoice_history(self, vendor: str, date_range: tuple[str, str]) -> dict:
        # TODO: fetch invoices filtered by vendor + date range
        raise NotImplementedError

    def get_commodity_prices(self, symbol: str) -> dict:
        # TODO: fetch commodity prices from DB
        raise NotImplementedError
