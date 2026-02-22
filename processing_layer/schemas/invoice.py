from pydantic import BaseModel


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total_price: float
    unit: str | None = None


class InvoiceExtraction(BaseModel):
    invoice_number: str | None
    # invoice_date: str | None  # ISO string — not yet in DB, will add later
    due_date: str | None
    vendor_name: str | None
    vendor_address: str | None
    client_name: str | None
    client_address: str | None
    line_items: list[LineItem]
    subtotal: float | None
    tax: float | None
    total: float | None
    currency: str | None
