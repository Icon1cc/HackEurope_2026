from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.services.payment import PaymentService
from app.schemas.payment import (
    PaymentCreate, PaymentUpdate, PaymentResponse,
    PaymentConfirmationResponse, StripeConfirmation,
)
from app.core.dependencies import get_payment_service
from app.models.payment import Payment
from app.models.invoice import Invoice

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/", response_model=list[PaymentResponse])
async def get_all(skip: int = 0, limit: int = 100, service: PaymentService = Depends(get_payment_service)):
    return await service.get_all_payments(skip, limit)


@router.get("/invoice/{invoice_id}", response_model=list[PaymentResponse])
async def get_by_invoice(invoice_id: UUID, service: PaymentService = Depends(get_payment_service)):
    return await service.get_by_invoice_id(invoice_id)


@router.get("/status/{status}", response_model=list[PaymentResponse])
async def get_by_status(status: str, skip: int = 0, limit: int = 100, service: PaymentService = Depends(get_payment_service)):
    return await service.get_by_status(status, skip, limit)


@router.get("/{payment_id}/confirmation", response_model=PaymentConfirmationResponse)
async def get_confirmation(payment_id: UUID, db: AsyncSession = Depends(get_db)):
    """Return vendor IBAN + Stripe confirmation for a confirmed payment."""
    payment = await db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status != "confirmed":
        raise HTTPException(status_code=400, detail="Payment not yet confirmed")

    # Load invoice -> vendor to get IBAN
    invoice = await db.get(
        Invoice, payment.invoice_id, options=[selectinload(Invoice.vendor)]
    )
    iban = invoice.vendor.registered_iban if invoice and invoice.vendor else None

    return PaymentConfirmationResponse(
        iban_vendor=iban,
        stripe_confirmation=StripeConfirmation(
            transfer_id=payment.stripe_payout_id,
            payment_id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            initiated_at=payment.initiated_at,
            confirmed_at=payment.confirmed_at,
        ),
    )


@router.get("/{id}", response_model=PaymentResponse)
async def get_one(id: UUID, service: PaymentService = Depends(get_payment_service)):
    payment = await service.get_payment(id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/", response_model=PaymentResponse, status_code=201)
async def create(data: PaymentCreate, service: PaymentService = Depends(get_payment_service)):
    return await service.create_payment(data)


@router.patch("/{id}", response_model=PaymentResponse)
async def update(id: UUID, data: PaymentUpdate, service: PaymentService = Depends(get_payment_service)):
    payment = await service.update_payment(id, data)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.delete("/{id}", status_code=204)
async def delete(id: UUID, service: PaymentService = Depends(get_payment_service)):
    if not await service.delete_payment(id):
        raise HTTPException(status_code=404, detail="Payment not found")
