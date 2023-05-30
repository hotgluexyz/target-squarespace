"""Squarespace target sink class, which handles writing streams."""


from target_squarespace.client import SquarespaceSink


class OrdersSink(SquarespaceSink):
    """Squarespace target sink class."""

    name = "Orders"
    endpoint = "/orders"

    def preprocess_record(self, record: dict, context: dict) -> dict:
        
        payload = {
            "id": record.get("id"),
            "order_number": record.get("order_number"),
            "tracking_number": None,
            "carrier": None,
            "fulfilled": True,
            "delivery_status": "delivered",
            "status": "completed",
            "transaction_date": record.get("transaction_date").strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        return payload

    def upsert_record(self, record: dict, context: dict) -> None:
        """Process the record."""
        endpoint = f"/orders/{record.get('id')}/fulfillments"
        state_updates = dict()
        if record:
            try:
                payload = record.copy()
                del payload["id"]
                payload = {
                        "SalesOrders": [
                            payload
                        ]
                }
                response = self.request_api(
                    "POST", endpoint=endpoint, request_data=payload
                )
                id = response.json()["id"]
                self.logger.info(f"{self.name} created with id: {id}")
            except:
                raise KeyError
            return id, True, state_updates