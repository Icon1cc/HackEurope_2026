"""Seed script: creates 4 vendors, 1 client, and 15 invoices per vendor with payments."""
import asyncio
import uuid
import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.core.database import engine, AsyncSessionLocal, Base
import app.models  # noqa: F401
from app.models.client import Client
from app.models.vendor import Vendor
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.override import Override

STATUSES = ["pending", "flagged", "overcharge", "approved", "rejected", "paid"]


async def seed():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created")

    async with AsyncSessionLocal() as db:
        # Create client
        client = Client(
            id=uuid.uuid4(),
            name_of_business="TechCorp International",
        )
        db.add(client)

        # Create 4 vendors
        vendors_data = [
            {"name": "CloudHost Pro", "category": "computing", "email": "billing@cloudhost.com", "registered_iban": "DE89370400440532013000"},
            {"name": "DataCenter EU", "category": "computing", "email": "invoices@datacenter.eu", "registered_iban": "FR7630006000011234567890189"},
            {"name": "NetServe Solutions", "category": "computing", "email": "accounts@netserve.io", "registered_iban": "GB29NWBK60161331926819"},
            {"name": "InfraScale Ltd", "category": "computing", "email": "finance@infrascale.com", "registered_iban": "NL91ABNA0417164300"},
        ]

        vendors = []
        for vd in vendors_data:
            vendor = Vendor(
                id=uuid.uuid4(),
                name=vd["name"],
                category=vd["category"],
                email=vd["email"],
                registered_iban=vd["registered_iban"],
                trust_score=Decimal(str(round(random.uniform(0.3, 0.95), 2))),
            )
            db.add(vendor)
            vendors.append(vendor)

        await db.flush()
        print(f"Created client: {client.name_of_business} ({client.id})")
        for v in vendors:
            print(f"Created vendor: {v.name} ({v.id})")

        # Create 15 invoices per vendor
        for vendor in vendors:
            for i in range(15):
                status = random.choice(STATUSES)
                amount = Decimal(str(round(random.uniform(500, 25000), 2)))
                days_ago = random.randint(1, 90)
                created = datetime.now(timezone.utc) - timedelta(days=days_ago)

                invoice = Invoice(
                    id=uuid.uuid4(),
                    vendor_id=vendor.id,
                    client_id=client.id,
                    raw_file_url=f"https://storage.example.com/invoices/{vendor.name.lower().replace(' ', '-')}/inv-{i+1:03d}.pdf",
                    extracted_data={
                        "invoice_number": f"INV-{i+1:03d}",
                        "line_items": [
                            {"description": "Cloud compute hours", "quantity": random.randint(100, 5000), "unit_price": round(random.uniform(0.05, 0.50), 2)},
                            {"description": "Storage (GB-months)", "quantity": random.randint(50, 2000), "unit_price": round(random.uniform(0.01, 0.10), 2)},
                        ],
                        "total": float(amount),
                        "currency": "EUR",
                    },
                    anomalies=[{"type": "price_spike", "severity": "medium"}] if status in ["flagged", "overcharge"] else None,
                    market_benchmarks={"compute_avg": 0.12, "storage_avg": 0.03} if status != "pending" else None,
                    confidence_score=random.randint(20, 100) if status != "pending" else None,
                    status=status,
                    claude_summary=f"Invoice from {vendor.name} for cloud services." if status != "pending" else None,
                    negotiation_email=f"Dear {vendor.name},\n\nWe noticed pricing above market rates..." if status == "overcharge" else None,
                    auto_approved=status in ["approved", "paid"] and random.random() > 0.5,
                    created_at=created,
                    updated_at=created + timedelta(hours=random.randint(1, 48)),
                )
                db.add(invoice)

                # Create payment for approved/paid invoices
                if status in ["approved", "paid"]:
                    payment = Payment(
                        id=uuid.uuid4(),
                        invoice_id=invoice.id,
                        amount=amount,
                        currency="EUR",
                        stripe_payout_id=f"po_{uuid.uuid4().hex[:24]}" if status == "paid" else None,
                        status="confirmed" if status == "paid" else "initiated",
                        initiated_at=created + timedelta(hours=random.randint(2, 24)),
                        confirmed_at=created + timedelta(days=random.randint(1, 5)) if status == "paid" else None,
                    )
                    db.add(payment)

                # Create override for flagged/overcharge/rejected
                if status in ["flagged", "overcharge", "rejected"]:
                    override = Override(
                        id=uuid.uuid4(),
                        invoice_id=invoice.id,
                        vendor_id=vendor.id,
                        agent_recommendation="reject" if status == "overcharge" else "review",
                        human_decision="reject" if status == "rejected" else None,
                        agreed=True if status == "rejected" else None,
                        override_reason="Pricing significantly above market rate" if status == "rejected" else None,
                        timestamp=created + timedelta(hours=random.randint(1, 12)),
                    )
                    db.add(override)

        await db.commit()
        print(f"\nSeeded 60 invoices (15 per vendor) with payments and overrides")

        # Print summary
        for vendor in vendors:
            print(f"\n--- {vendor.name} ---")
            from sqlalchemy import select, func
            count_result = await db.execute(
                select(func.count(Invoice.id)).where(Invoice.vendor_id == vendor.id)
            )
            print(f"  Invoices: {count_result.scalar()}")


if __name__ == "__main__":
    asyncio.run(seed())
