from __future__ import annotations
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


def _make_os_client(deleted: int = 5, remaining: int = 950):
    client = MagicMock()
    client.delete_by_query.return_value = {"deleted": deleted, "version_conflicts": 0}
    client.count.return_value = {"count": remaining}
    return client


@patch("cleanup.handler.get_client")
def test_cleanup_returns_deleted_count(mock_get_client):
    mock_get_client.return_value = _make_os_client(deleted=12, remaining=981)

    from cleanup.handler import handler
    result = handler({}, None)

    assert result["deleted"] == 12
    assert result["remaining"] == 981
    assert "cutoff" in result


@patch("cleanup.handler.get_client")
def test_cleanup_cutoff_is_30_days_ago(mock_get_client):
    mock_get_client.return_value = _make_os_client()

    from cleanup.handler import handler
    result = handler({}, None)

    cutoff = datetime.strptime(result["cutoff"], "%Y-%m-%d")
    delta = (datetime.now(timezone.utc).replace(tzinfo=None) - cutoff).days
    assert 29 <= delta <= 31


@patch("cleanup.handler.get_client")
def test_cleanup_calls_delete_by_query_with_range(mock_get_client):
    mock_client = _make_os_client()
    mock_get_client.return_value = mock_client

    from cleanup.handler import handler
    handler({}, None)

    call_kwargs = mock_client.delete_by_query.call_args
    body = call_kwargs[1]["body"] if call_kwargs[1] else call_kwargs[0][1]
    assert "range" in body["query"]
    assert "posted_at" in body["query"]["range"]
