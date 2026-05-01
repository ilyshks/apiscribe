from unittest.mock import MagicMock, patch, call
import pytest

from apiscribe.storage.memory import InMemoryStorage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_endpoint(path="/api/v1/users", method="GET", request_count=1,
                  request_field_counts=None, request_schema=None,
                  responses=None):
    """Factory for a mock EndpointModel."""
    ep = MagicMock()
    ep.path = path
    ep.method = method
    ep.request_count = request_count
    ep.request_field_counts = request_field_counts or {}
    ep.request_schema = request_schema or {"type": "object"}
    ep.responses = responses or {}
    return ep


# ---------------------------------------------------------------------------
# get_all
# ---------------------------------------------------------------------------

class TestGetAll:
    def test_empty_storage_returns_empty_list(self):
        storage = InMemoryStorage()
        assert storage.get_all() == []

    def test_returns_list_not_dict(self):
        storage = InMemoryStorage()
        storage._endpoints[("/a", "GET")] = make_endpoint("/a", "GET")
        result = storage.get_all()
        assert isinstance(result, list)

    def test_returns_all_stored_endpoints(self):
        storage = InMemoryStorage()
        ep1 = make_endpoint("/a", "GET")
        ep2 = make_endpoint("/b", "POST")
        storage._endpoints[("/a", "GET")] = ep1
        storage._endpoints[("/b", "POST")] = ep2
        assert set(storage.get_all()) == {ep1, ep2}


# ---------------------------------------------------------------------------
# save — new endpoint (no existing key)
# ---------------------------------------------------------------------------

class TestSaveNewEndpoint:
    @pytest.mark.parametrize("path,method", [
        ("/users", "GET"),
        ("/users", "POST"),
        ("/items/1", "DELETE"),
        ("/", "PATCH"),
    ])
    def test_new_endpoint_is_stored_under_correct_key(self, path, method):
        storage = InMemoryStorage()
        ep = make_endpoint(path, method)
        storage.save(ep)
        assert (path, method) in storage._endpoints

    def test_new_endpoint_stored_as_is(self):
        storage = InMemoryStorage()
        ep = make_endpoint()
        storage.save(ep)
        assert storage._endpoints[("/api/v1/users", "GET")] is ep

    @pytest.mark.parametrize("path,method", [
        ("/a", "GET"),
        ("/b", "POST"),
    ])
    def test_merge_schema_not_called_for_new_endpoint(self, path, method):
        storage = InMemoryStorage()
        ep = make_endpoint(path, method)
        with patch("apiscribe.utils.schema_merge.merge_schema") as mock_merge:
            storage.save(ep)
            mock_merge.assert_not_called()

    def test_different_methods_stored_separately(self):
        storage = InMemoryStorage()
        ep_get = make_endpoint("/x", "GET")
        ep_post = make_endpoint("/x", "POST")
        storage.save(ep_get)
        storage.save(ep_post)
        assert len(storage._endpoints) == 2


# ---------------------------------------------------------------------------
# save — existing endpoint (merge path)
# ---------------------------------------------------------------------------

class TestSaveExistingEndpoint:

    def test_request_count_incremented(self):
        storage = InMemoryStorage()
        existing = make_endpoint(request_count=3)
        storage._endpoints[("/api/v1/users", "GET")] = existing
        storage.save(make_endpoint())
        assert existing.request_count == 4

    @pytest.mark.parametrize("fields,expected_counts", [
        ({"name": 1}, {"name": 1}),
        ({"name": 1, "age": 1}, {"name": 1, "age": 1}),
        ({}, {}),
    ])
    def test_request_field_counts_updated_for_new_fields(
            self, fields, expected_counts):
        storage = InMemoryStorage()
        existing = make_endpoint(request_field_counts={})
        storage._endpoints[("/api/v1/users", "GET")] = existing

        incoming = make_endpoint(request_field_counts=fields)
        with patch("apiscribe.storage.memory.merge_schema", return_value={}):
            storage.save(incoming)

        assert existing.request_field_counts == expected_counts

    def test_request_field_counts_accumulated_for_repeated_fields(self):
        storage = InMemoryStorage()
        existing = make_endpoint(request_field_counts={"name": 2, "age": 1})
        storage._endpoints[("/api/v1/users", "GET")] = existing

        incoming = make_endpoint(request_field_counts={"name": 1, "email": 1})
        with patch("apiscribe.storage.memory.merge_schema", return_value={}):
            storage.save(incoming)

        assert existing.request_field_counts == {"name": 3, "age": 1, "email": 1}


    @pytest.mark.parametrize("existing_responses,incoming_responses,expected_new_keys", [
        ({}, {"200": {"type": "object"}}, {"200"}),
        ({"200": {}}, {"404": {}}, {"404"}),
        ({"200": {}, "500": {}}, {"201": {}}, {"201"}),
    ])
    def test_new_response_status_added_without_merge(
            self, existing_responses, incoming_responses, expected_new_keys):
        storage = InMemoryStorage()
        existing = make_endpoint(responses=existing_responses)
        storage._endpoints[("/api/v1/users", "GET")] = existing

        incoming = make_endpoint(responses=incoming_responses)
        with patch("apiscribe.storage.memory.merge_schema", return_value={}) as mock_merge:
            storage.save(incoming)

        for key in expected_new_keys:
            assert key in existing.responses
        mock_merge.assert_called_once()


    # --- storage integrity ---

    def test_endpoint_reassigned_after_merge(self):
        """After merging, the existing object must be written back to the dict."""
        storage = InMemoryStorage()
        existing = make_endpoint(responses={})
        storage._endpoints[("/api/v1/users", "GET")] = existing

        with patch("apiscribe.storage.memory.merge_schema", return_value={}):
            storage.save(make_endpoint(responses={}))

        assert storage._endpoints[("/api/v1/users", "GET")] is existing

    def test_total_endpoint_count_unchanged_on_duplicate_save(self):
        storage = InMemoryStorage()
        storage.save(make_endpoint())
        with patch("apiscribe.storage.memory.merge_schema", return_value={}):
            storage.save(make_endpoint())
        assert len(storage._endpoints) == 1

    def test_request_schema_merged_when_exists(self):
        storage = InMemoryStorage()
        existing = make_endpoint(request_schema={"type": "object", "old": "field"})
        storage._endpoints[("/api/v1/users", "GET")] = existing
        incoming = make_endpoint(request_schema={"type": "object", "new": "value"})
        
        with patch("apiscribe.storage.memory.merge_schema") as mock_merge:
            mock_merge.return_value = {"type": "object", "old": "field", "new": "value"}
            storage.save(incoming)
        
        mock_merge.assert_called_once_with({"type": "object", "old": "field"}, {"type": "object", "new": "value"})
        assert existing.request_schema == {"type": "object", "old": "field", "new": "value"}
    
