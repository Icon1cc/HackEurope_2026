from app.api.routers.extraction import _get_or_create_vendor, _normalize_iban
from app.models.vendor import Vendor


class TestVendorIbanPersistence:
    def test_normalize_iban(self):
        assert _normalize_iban("DE89 3704 0044 0532 0130 00") == "DE89370400440532013000"
        assert _normalize_iban("de89-3704-0044-0532-0130-00") == "DE89370400440532013000"
        assert _normalize_iban("not-an-iban") is None
        assert _normalize_iban("12345") is None

    async def test_create_vendor_persists_iban(self, db_session):
        vendor = await _get_or_create_vendor(
            db=db_session,
            vendor_name="Acme Cloud",
            vendor_iban="DE89 3704 0044 0532 0130 00",
            vendor_address="Test Address",
        )
        assert vendor.registered_iban == "DE89370400440532013000"
        assert vendor.known_iban_changes is None

    async def test_existing_vendor_without_iban_gets_filled(self, db_session):
        vendor = Vendor(name="No Iban Vendor", category="computing")
        db_session.add(vendor)
        await db_session.flush()

        updated = await _get_or_create_vendor(
            db=db_session,
            vendor_name="No Iban Vendor",
            vendor_iban="FR76 3000 6000 0112 3456 7890 189",
            vendor_address=None,
        )

        assert updated.id == vendor.id
        assert updated.registered_iban == "FR7630006000011234567890189"
        assert updated.known_iban_changes is None

    async def test_existing_vendor_iban_change_is_tracked_once(self, db_session):
        vendor = Vendor(
            name="Tracked Iban Vendor",
            category="computing",
            registered_iban="FR7630006000011234567890189",
        )
        db_session.add(vendor)
        await db_session.flush()

        updated = await _get_or_create_vendor(
            db=db_session,
            vendor_name="tracked iban vendor",
            vendor_iban="DE89 3704 0044 0532 0130 00",
            vendor_address=None,
        )

        assert updated.registered_iban == "DE89370400440532013000"
        assert isinstance(updated.known_iban_changes, list)
        assert len(updated.known_iban_changes) == 1
        assert updated.known_iban_changes[0]["previous_iban"] == "FR7630006000011234567890189"
        assert updated.known_iban_changes[0]["new_iban"] == "DE89370400440532013000"
        assert updated.known_iban_changes[0]["detected_at"]

        updated_again = await _get_or_create_vendor(
            db=db_session,
            vendor_name="Tracked Iban Vendor",
            vendor_iban="DE89370400440532013000",
            vendor_address=None,
        )
        assert isinstance(updated_again.known_iban_changes, list)
        assert len(updated_again.known_iban_changes) == 1

    async def test_invalid_iban_does_not_overwrite_existing(self, db_session):
        vendor = Vendor(
            name="Stable Iban Vendor",
            category="computing",
            registered_iban="DE89370400440532013000",
        )
        db_session.add(vendor)
        await db_session.flush()

        updated = await _get_or_create_vendor(
            db=db_session,
            vendor_name="Stable Iban Vendor",
            vendor_iban="INVALID",
            vendor_address=None,
        )

        assert updated.registered_iban == "DE89370400440532013000"
        assert updated.known_iban_changes is None
