"""Squarespace target sink class, which handles writing streams."""

from datetime import datetime, timezone

from hotglue_models_crm.crm import Contact
from singer_sdk.exceptions import FatalAPIError
from target_squarespace.client import SquarespaceSink

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

    def preprocess_record(self, record: dict, context: dict) -> dict:
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

        return payload

    def upsert_record(self, record: dict, context: dict) -> None:
        squarespace_id = record.pop("_squarespace_id", None)

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
            response = self.request_api("POST", request_data=record)

        id = response.json().get("contact", {}).get("id")
        return id, response.ok, dict()