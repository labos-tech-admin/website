"""LABOS Technologies backend API regression tests."""
import os
import re
import time
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")
API = f"{BASE_URL}/api"


def _creds():
    p = Path("/app/memory/test_credentials.md")
    content = p.read_text(encoding="utf-8")
    email = re.search(r'(?im)^\s*[-*]\s*\*\*Email\*\*\s*:\s*`?([^`\s]+)', content)
    pwd = re.search(r'(?im)^\s*[-*]\s*\*\*Password\*\*\s*:\s*`?([^`\s]+)', content)
    return {"email": email.group(1), "password": pwd.group(1)}


ADMIN = _creds()


@pytest.fixture(scope="session")
def admin_client():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=ADMIN, timeout=30)
    if r.status_code != 200:
        pytest.fail(f"Admin login failed {r.status_code}: {r.text[:300]}")
    return s


@pytest.fixture(scope="session")
def client_session():
    """Fresh registered client."""
    s = requests.Session()
    email = f"test_client_{uuid.uuid4().hex[:8]}@labos.dev"
    r = s.post(f"{API}/auth/register",
               json={"email": email, "password": "Test@1234", "name": "TEST Client"}, timeout=30)
    if r.status_code != 200:
        pytest.fail(f"Register failed {r.status_code}: {r.text[:300]}")
    s.email = email
    return s


@pytest.fixture(scope="session")
def package_booking(client_session):
    r = client_session.post(f"{API}/bookings", json={
        "service_slug": "website-building",
        "package_id": "website_starter",
        "booking_type": "package",
        "project_title": "TEST package project",
        "requirements": "test req longer than 5 chars",
    }, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="session")
def quote_booking(client_session):
    r = client_session.post(f"{API}/bookings", json={
        "service_slug": "application-building",
        "booking_type": "quote",
        "project_title": "TEST quote project",
        "requirements": "need mvp for saas",
        "budget": 5000,
        "timeline": "6 weeks",
    }, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


# ---------------- Health / Services ----------------
class TestServices:
    def test_root(self):
        r = requests.get(f"{API}/", timeout=30)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_services_list(self):
        r = requests.get(f"{API}/services", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3
        slugs = {s["slug"] for s in data}
        assert slugs == {"website-building", "site-maintenance", "application-building"}
        for svc in data:
            assert svc["title"] and svc["tagline"] and svc["image"]
            assert len(svc["packages"]) >= 2
            for p in svc["packages"]:
                assert isinstance(p["package_id"], str)
                assert isinstance(p["amount"], (int, float)) and p["amount"] > 0

    def test_service_detail_and_404(self):
        r = requests.get(f"{API}/services/website-building", timeout=30)
        assert r.status_code == 200
        assert r.json()["slug"] == "website-building"
        starter = [p for p in r.json()["packages"] if p["package_id"] == "website_starter"][0]
        assert starter["amount"] == 499.0
        assert requests.get(f"{API}/services/nope", timeout=30).status_code == 404


# ---------------- Auth ----------------
class TestAuth:
    def test_register_sets_cookies(self):
        s = requests.Session()
        email = f"test_reg_{uuid.uuid4().hex[:8]}@labos.dev"
        r = s.post(f"{API}/auth/register",
                   json={"email": email, "password": "Test@1234", "name": "TEST Reg"}, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["email"] == email
        assert body["role"] == "client"
        assert "password_hash" not in body and "_id" not in body
        cookie_hdrs = r.headers.get("set-cookie", "")
        assert "access_token" in cookie_hdrs and "HttpOnly" in cookie_hdrs
        assert "refresh_token" in cookie_hdrs
        me = s.get(f"{API}/auth/me", timeout=30)
        assert me.status_code == 200 and me.json()["email"] == email

    def test_register_duplicate(self, client_session):
        r = requests.post(f"{API}/auth/register",
                          json={"email": client_session.email, "password": "Test@1234", "name": "dup"},
                          timeout=30)
        assert r.status_code == 400

    def test_register_weak_password_422(self):
        r = requests.post(f"{API}/auth/register",
                          json={"email": f"test_w{uuid.uuid4().hex[:6]}@labos.dev",
                                "password": "123", "name": "x"}, timeout=30)
        assert r.status_code == 422

    def test_admin_login(self):
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json=ADMIN, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["role"] == "admin"
        assert "HttpOnly" in r.headers.get("set-cookie", "")

    def test_login_bad_password(self):
        r = requests.post(f"{API}/auth/login",
                          json={"email": ADMIN["email"], "password": "wrongwrong"}, timeout=30)
        assert r.status_code == 401

    def test_me_unauthenticated(self):
        assert requests.get(f"{API}/auth/me", timeout=30).status_code == 401

    def test_bcrypt_hash_format(self):
        import bcrypt
        from pymongo import MongoClient
        env = dotenv_values("/app/backend/.env")
        mc = MongoClient(env["MONGO_URL"])
        user = mc[env["DB_NAME"]].users.find_one({"email": ADMIN["email"]})
        assert user is not None
        assert user["password_hash"].startswith("$2b$")
        assert bcrypt.checkpw(ADMIN["password"].encode(), user["password_hash"].encode())
        mc.close()

    def test_refresh_and_logout(self):
        s = requests.Session()
        s.post(f"{API}/auth/login", json=ADMIN, timeout=30)
        r = s.post(f"{API}/auth/refresh", timeout=30)
        assert r.status_code == 200 and r.json()["ok"] is True
        r = s.post(f"{API}/auth/logout", timeout=30)
        assert r.status_code == 200
        s.cookies.clear()
        assert s.get(f"{API}/auth/me", timeout=30).status_code == 401


# ---------------- Bookings ----------------
class TestBookings:
    def test_create_package_booking(self, client_session, package_booking):
        b = package_booking
        assert b["amount"] == 499.0
        assert b["package_name"] == "Starter Site"
        assert b["service_title"] == "Website Building"
        assert b["status"] == "new" and b["payment_status"] == "unpaid"
        assert "_id" not in b
        g = client_session.get(f"{API}/bookings/{b['booking_id']}", timeout=30)
        assert g.status_code == 200 and g.json()["amount"] == 499.0

    def test_create_quote_booking(self, quote_booking):
        b = quote_booking
        assert b["amount"] is None
        assert b["budget"] == 5000
        assert b["timeline"] == "6 weeks"
        assert b["booking_type"] == "quote"

    def test_invalid_service(self, client_session):
        r = client_session.post(f"{API}/bookings", json={
            "service_slug": "bogus", "booking_type": "quote",
            "project_title": "x1", "requirements": "abcdef"}, timeout=30)
        assert r.status_code == 400

    def test_package_without_package_id(self, client_session):
        r = client_session.post(f"{API}/bookings", json={
            "service_slug": "website-building", "booking_type": "package",
            "project_title": "x1", "requirements": "abcdef"}, timeout=30)
        assert r.status_code == 400

    def test_bookings_require_auth(self):
        r = requests.post(f"{API}/bookings", json={
            "service_slug": "website-building", "booking_type": "quote",
            "project_title": "x1", "requirements": "abcdef"}, timeout=30)
        assert r.status_code == 401

    def test_mine_only_own_bookings(self, client_session, package_booking, quote_booking):
        r = client_session.get(f"{API}/bookings/mine", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 2
        emails = {b["client_email"] for b in data}
        assert emails == {client_session.email}
        ids = {b["booking_id"] for b in data}
        assert package_booking["booking_id"] in ids and quote_booking["booking_id"] in ids

    def test_other_client_cannot_read_booking(self, package_booking):
        s = requests.Session()
        s.post(f"{API}/auth/register", json={
            "email": f"test_other_{uuid.uuid4().hex[:8]}@labos.dev",
            "password": "Test@1234", "name": "TEST Other"}, timeout=30)
        r = s.get(f"{API}/bookings/{package_booking['booking_id']}", timeout=30)
        assert r.status_code == 403


# ---------------- Payments ----------------
class TestPayments:
    def test_checkout_and_status(self, client_session, package_booking):
        bid = package_booking["booking_id"]
        r = client_session.post(f"{API}/payments/checkout", json={
            "booking_id": bid, "origin_url": BASE_URL}, timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["checkout_url"].startswith("https://")
        assert isinstance(data["session_id"], str) and data["session_id"]
        b = client_session.get(f"{API}/bookings/{bid}", timeout=30).json()
        assert b["payment_status"] == "pending"

        st = requests.get(f"{API}/payments/status/{data['session_id']}", timeout=60)
        assert st.status_code == 200, st.text
        d = st.json()
        assert d["session_id"] == data["session_id"]
        assert d["payment_status"] in ("pending", "paid", "unpaid")
        assert "status" in d

    def test_status_unknown_session_404(self):
        r = requests.get(f"{API}/payments/status/sess_does_not_exist", timeout=30)
        assert r.status_code == 404

    def test_checkout_on_quote_without_amount_400(self, client_session):
        q = client_session.post(f"{API}/bookings", json={
            "service_slug": "application-building", "booking_type": "quote",
            "project_title": "TEST unquoted", "requirements": "no amount yet"}, timeout=30).json()
        r = client_session.post(f"{API}/payments/checkout", json={
            "booking_id": q["booking_id"], "origin_url": BASE_URL}, timeout=30)
        assert r.status_code == 400

    def test_checkout_missing_booking_404(self, client_session):
        r = client_session.post(f"{API}/payments/checkout", json={
            "booking_id": "bk_nope", "origin_url": BASE_URL}, timeout=30)
        assert r.status_code == 404

    def test_checkout_requires_auth(self, package_booking):
        r = requests.post(f"{API}/payments/checkout", json={
            "booking_id": package_booking["booking_id"], "origin_url": BASE_URL}, timeout=30)
        assert r.status_code == 401


# ---------------- Admin ----------------
class TestAdmin:
    def test_stats(self, admin_client):
        r = admin_client.get(f"{API}/admin/stats", timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("total_clients", "total_bookings", "active_bookings",
                  "paid_bookings", "contact_messages", "revenue"):
            assert k in d
        assert d["total_bookings"] >= 1

    def test_non_admin_forbidden(self, client_session):
        assert client_session.get(f"{API}/admin/stats", timeout=30).status_code == 403
        assert client_session.get(f"{API}/admin/bookings", timeout=30).status_code == 403
        assert client_session.get(f"{API}/admin/clients", timeout=30).status_code == 403
        assert client_session.get(f"{API}/admin/contacts", timeout=30).status_code == 403

    def test_admin_unauth_401(self):
        assert requests.get(f"{API}/admin/stats", timeout=30).status_code == 401

    def test_lists(self, admin_client):
        for path in ("clients", "bookings", "contacts"):
            r = admin_client.get(f"{API}/admin/{path}", timeout=30)
            assert r.status_code == 200, path
            assert isinstance(r.json(), list)
            for row in r.json()[:5]:
                assert "_id" not in row
                assert "password_hash" not in row

    def test_update_quote_booking_then_pay(self, admin_client, client_session, quote_booking):
        bid = quote_booking["booking_id"]
        r = admin_client.patch(f"{API}/admin/bookings/{bid}", json={
            "amount": 2500, "status": "quoted", "admin_notes": "quoted at 2500"}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["amount"] == 2500
        assert d["status"] == "quoted"
        assert d["admin_notes"] == "quoted at 2500"
        mine = client_session.get(f"{API}/bookings/mine", timeout=30).json()
        row = [b for b in mine if b["booking_id"] == bid][0]
        assert row["amount"] == 2500 and row["status"] == "quoted"
        c = client_session.post(f"{API}/payments/checkout", json={
            "booking_id": bid, "origin_url": BASE_URL}, timeout=60)
        assert c.status_code == 200, c.text
        assert c.json()["checkout_url"].startswith("https://")

    def test_update_missing_booking_404(self, admin_client):
        r = admin_client.patch(f"{API}/admin/bookings/bk_missing", json={"status": "quoted"}, timeout=30)
        assert r.status_code == 404


# ---------------- Contact ----------------
class TestContact:
    def test_submit_and_appears_in_admin(self, admin_client):
        subject = f"TEST subject {uuid.uuid4().hex[:6]}"
        r = requests.post(f"{API}/contact", json={
            "name": "TEST Contact", "email": "test_contact@labos.dev",
            "subject": subject, "message": "hello this is a test message"}, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json() == {"ok": True}
        time.sleep(0.5)
        rows = admin_client.get(f"{API}/admin/contacts", timeout=30).json()
        assert any(c["subject"] == subject for c in rows)

    def test_invalid_contact_422(self):
        r = requests.post(f"{API}/contact", json={
            "name": "x", "email": "not-an-email", "subject": "s", "message": "hi"}, timeout=30)
        assert r.status_code == 422
