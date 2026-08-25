"""Unit tests for _get_razorpay() diagnostic messages (iteration 4 feature)."""
import sys
import pytest
from fastapi import HTTPException

sys.path.insert(0, "/app/backend")
from server import _get_razorpay  # noqa: E402


def test_missing_keys_message(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_ID", "")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "")
    with pytest.raises(HTTPException) as ei:
        _get_razorpay()
    assert ei.value.status_code == 400
    assert "not configured" in ei.value.detail


def test_placeholder_keys_message(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_placeholder")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "placeholder_secret")
    with pytest.raises(HTTPException) as ei:
        _get_razorpay()
    d = ei.value.detail
    assert ei.value.status_code == 400
    assert "placeholder" in d.lower() and "Replace" in d and "dashboard.razorpay.com" in d


def test_bad_format_key_id_message(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_ID", "someRandomSecretValue")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "rzp_test_abc123")
    with pytest.raises(HTTPException) as ei:
        _get_razorpay()
    d = ei.value.detail
    assert ei.value.status_code == 400
    assert "must start with 'rzp_test_'" in d


def test_valid_looking_keys_build_client(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_ID", '"rzp_test_abc123"')
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "someSecretValue")
    c = _get_razorpay()
    assert c is not None
    assert c.auth == ("rzp_test_abc123", "someSecretValue")
