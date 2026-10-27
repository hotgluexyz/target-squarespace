from unittest.mock import Mock, call

from target_squarespace.sinks import ContactsSink


def test_upsert_looks_up_and_updates_contact_by_email_without_id():
    sink = ContactsSink.__new__(ContactsSink)
    query_response = Mock()
    query_response.json.return_value = {
        "contacts": [
            {
                "id": "squarespace-contact-id",
                "primaryEmail": {"email": "existing@example.com"},
            }
        ]
    }
    patch_response = Mock()
    patch_response.json.return_value = {"contact": {"id": "squarespace-contact-id"}}
    patch_response.ok = True
    sink.request_api = Mock(side_effect=[query_response, patch_response])

    result = sink.upsert_record(
        {
            "firstName": "Existing",
            "lastName": "Contact",
            "primaryEmail": {"email": "existing@example.com"},
        },
        context={},
    )

    assert result == ("squarespace-contact-id", True, {})
    assert sink.request_api.call_args_list == [
        call(
            "POST",
            endpoint="/contacts/query",
            request_data={"searchString": "existing@example.com", "pageSize": 50},
        ),
        call(
            "PATCH",
            endpoint="/contacts/squarespace-contact-id",
            request_data={
                "firstName": "Existing",
                "lastName": "Contact",
                "primaryEmail": {"email": "existing@example.com"},
            },
            headers={"Content-Type": "application/merge-patch+json"},
        ),
    ]
