from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.invoice import Invoice
from app.services.stripe_service import execute_vendor_payment

router = APIRouter(prefix="/invoices", tags=["invoices"], dependencies=[Depends(get_current_user)])


@router.post("/{invoice_id}/approve")
async def approve_invoice(invoice_id: UUID, db: AsyncSession = Depends(get_db)):
    invoice = await db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status == "approved" or invoice.status == "paid":
        raise HTTPException(status_code=400, detail=f"Invoice already {invoice.status}")

    invoice.status = "approved"
    await db.commit()
    await db.refresh(invoice)

    payment_result = None
    if invoice.vendor_id and invoice.total:
        payment_result = await execute_vendor_payment(
            invoice_id=invoice.id,
            vendor_id=invoice.vendor_id,
            amount_euros=float(invoice.total),
            db=db,
        )

    return {"approved": True, "invoice_id": str(invoice.id), "payment": payment_result}
