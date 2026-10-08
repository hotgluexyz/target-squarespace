"""Squarespace target sink class, which handles writing streams."""

from datetime import datetime, timezone
from typing import Optional

from hotglue_models_crm.crm import Contact
from singer_sdk.exceptions import FatalAPIError
from target_squarespace.client import SquarespaceSink

# ISO 3166-1 alpha-3 -> alpha-2 for common three-letter codes.
_ISO3_TO_ISO2 = {
    "USA": "US",
    "CAN": "CA",
    "GBR": "GB",
    "AUS": "AU",
    "MEX": "MX",
    "BRA": "BR",
    "DEU": "DE",
    "FRA": "FR",
    "ESP": "ES",
    "ITA": "IT",
    "NLD": "NL",
    "IRL": "IE",
    "NZL": "NZ",
    "IND": "IN",
    "JPN": "JP",
    "CHN": "CN",
    "KOR": "KR",
    "SGP": "SG",
    "ZAF": "ZA",
    "ARE": "AE",
    "PHL": "PH",
    "PRT": "PT",
    "SWE": "SE",
    "CHE": "CH",
    "AUT": "AT",
    "BEL": "BE",
    "DNK": "DK",
    "NOR": "NO",
    "FIN": "FI",
    "POL": "PL",
}

# E.164 calling code -> ISO alpha-2. Longer codes first for greedy match.
# Ambiguous codes (e.g. +1) resolve to the primary country.
_CALLING_CODE_TO_COUNTRY = (
    ("971", "AE"),
    ("966", "SA"),
    ("886", "TW"),
    ("880", "BD"),
    ("852", "HK"),
    ("353", "IE"),
    ("351", "PT"),
    ("358", "FI"),
    ("61", "AU"),
    ("64", "NZ"),
    ("65", "SG"),
    ("63", "PH"),
    ("60", "MY"),
    ("66", "TH"),
    ("81", "JP"),
    ("82", "KR"),
    ("84", "VN"),
    ("86", "CN"),
    ("91", "IN"),
    ("92", "PK"),
    ("90", "TR"),
    ("55", "BR"),
    ("52", "MX"),
    ("54", "AR"),
    ("57", "CO"),
    ("56", "CL"),
    ("51", "PE"),
    ("44", "GB"),
    ("49", "DE"),
    ("33", "FR"),
    ("34", "ES"),
    ("39", "IT"),
    ("31", "NL"),
    ("32", "BE"),
    ("41", "CH"),
    ("43", "AT"),
    ("45", "DK"),
    ("46", "SE"),
    ("47", "NO"),
    ("48", "PL"),
    ("27", "ZA"),
    ("7", "RU"),
    ("1", "US"),
)


def _normalize_country_code(country_code: str) -> str:
    """Return an ISO 3166-1 alpha-2 country code."""
    code = country_code.strip().upper()
    if len(code) == 2:
        return code
    if len(code) == 3:
        return _ISO3_TO_ISO2.get(code, "US")
    return "US"


def _infer_country_code_from_phone(phone_number: Optional[str]) -> str:
    """Infer ISO alpha-2 country code from an E.164 phone number; default US."""
    if not phone_number:
        return "US"

    stripped = phone_number.strip()
    if stripped.startswith("00"):
        digits = "".join(ch for ch in stripped[2:] if ch.isdigit())
    elif stripped.startswith("+"):
        digits = "".join(ch for ch in stripped[1:] if ch.isdigit())
    else:
        return "US"

    for calling_code, country in _CALLING_CODE_TO_COUNTRY:
        if digits.startswith(calling_code):
            return country
    return "US"


class OrdersSink(SquarespaceSink):
    """Squarespace target sink class."""

    name = "SalesOrders"
    endpoint = "/orders"

    def preprocess_record(self, record: dict, context: dict) -> dict:

        shipDate = record.get("transaction_date")
        if shipDate:
            shipDate = datetime.strptime(shipDate, '%Y-%m-%dT%H:%M:%SZ')
            shipDate = shipDate.replace(tzinfo=timezone.utc).timestamp()
            shipDate = datetime.fromtimestamp(shipDate).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        payload = {
            "shouldSendNotification": True,
            "shipments": [
                {       
                    "carrierName": record.get("carrier"),
                    "trackingNumber": record.get("tracking_number"),
                    "shipDate": shipDate,
                    "service": record.get("carrier")                   
                }
            ]
        }

        record = {
            "id": record.get("id"),
            "payload": payload
        }
        
        return record

    def upsert_record(self, record: dict, context: dict) -> None:
        """Process the record."""
        id = record.get("id")
        endpoint = f"/orders/{id}/fulfillments"
        state_updates = dict()
        if record:
            try:
                response = self.request_api(
                    "POST", endpoint=endpoint, request_data=record.get("payload")
                )
                if response.status_code == 204:
                    self.logger.info(f"Order No. {id} was fulfilled succesfully")
            except:
                raise KeyError
            return id, True, state_updates


class ContactsSink(SquarespaceSink):
    """Squarespace Contacts sink."""

    name = "Contacts"
    endpoint = "/contacts"
    base_url = "https://api.squarespace.com/v1"
    unified_schema = Contact

    def _build_address_book_payload(self, default_shipping_address: dict) -> dict:
        address = dict(default_shipping_address.get("address") or {})

        country_code = address.get("countryCode")
        if country_code:
            address["countryCode"] = _normalize_country_code(str(country_code))
        else:
            address["countryCode"] = _infer_country_code_from_phone(address.get("phoneNumber"))

        return {
            "address": address,
            "defaultShipping": True,
        }

    def preprocess_record(self, record: dict, context: dict) -> dict:
        if self.config.get("unified_schema", False):
            contact = Contact(**record)

            accepts_marketing = None
            if contact.unsubscribed is not None:
                accepts_marketing = not contact.unsubscribed
            elif contact.subscribe_status is not None:
                accepts_marketing = contact.subscribe_status.lower() == "subscribed"

            primary_email = {}
            if contact.email:
                primary_email["email"] = contact.email
                if accepts_marketing is not None:
                    primary_email["acceptsMarketing"] = accepts_marketing

            payload = {
                "firstName": contact.first_name or "",
                "lastName": contact.last_name or "",
                "locale": "en-US",
            }

            if primary_email:
                payload["primaryEmail"] = primary_email

            if contact.id:
                payload["_squarespace_id"] = contact.id
        else:
            payload = record

            if payload.get("id"):
                payload["_squarespace_id"] = payload.pop("id")

            default_shipping = payload.pop("defaultShippingAddress", None)
            if default_shipping:
                payload["_address_book"] = self._build_address_book_payload(default_shipping)

        return payload

    def upsert_record(self, record: dict, context: dict) -> None:
        squarespace_id = record.pop("_squarespace_id", None)
        address_book = record.pop("_address_book", None)

        response = None
        if squarespace_id:
            try:
                response = self.request_api(
                    "PATCH",
                    endpoint=f"/contacts/{squarespace_id}",
                    request_data=record,
                    headers={"Content-Type": "application/merge-patch+json"},
                )
            except FatalAPIError as e:
                # The snapshot-resolved id may point to a contact that was deleted in Squarespace.
                # In that case, recreate it via POST instead of failing the whole export.
                if "not found" in str(e).lower():
                    self.logger.info(f"Contact {squarespace_id} not found in Squarespace; recreating via POST.")
                    response = None
                else:
                    raise

        if response is None:
            try:
                response = self.request_api("POST", request_data=record)
            except FatalAPIError as e:
                if self._is_duplicate_contact_error(e):
                    email = (record.get("primaryEmail") or {}).get("email")
                    self.logger.info(
                        f"Contact already exists in Squarespace"
                        + (f" with email {email}" if email else "")
                        + "; marking as existing."
                    )
                    return None, True, {"existing": True}
                raise

        id = response.json().get("contact", {}).get("id")

        if address_book and id and response.ok:
            self.request_api(
                "POST",
                endpoint=f"/contacts/{id}/address-book",
                request_data=address_book,
            )

        return id, response.ok, dict()

    @staticmethod
    def _is_duplicate_contact_error(error: Exception) -> bool:
        message = str(error)
        return (
            "DUPLICATE_USER_CONFLICT" in message
            or "email address already exists" in message.lower()
        )
