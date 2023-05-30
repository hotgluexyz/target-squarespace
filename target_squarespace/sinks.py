"""Squarespace target sink class, which handles writing streams."""


from target_squarespace.client import SquarespaceSink
from pendulum import parse
from datetime import datetime
from datetime import timezone

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