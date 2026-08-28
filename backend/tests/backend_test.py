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

BACKEND_ENV_TOP = dotenv_values("/app/backend/.env")


def _mongo_db():
    from pymongo import MongoClient
    mc = MongoClient(BACKEND_ENV_TOP["MONGO_URL"])
    return mc, mc[BACKEND_ENV_TOP["DB_NAME"]]


def make_verified_client(prefix="test_client"):
    """Register a user (OTP send fails with placeholder Resend key -> 200 email_sent:false),
    mark email_verified=True directly in Mongo, then log in."""
    s = requests.Session()
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@labos.dev"
    r = s.post(f"{API}/auth/register",
               json={"email": email, "password": "Test@1234", "name": "TEST Client"}, timeout=30)
    assert r.status_code in (200, 400), f"register {r.status_code}: {r.text[:300]}"
    mc, db = _mongo_db()
    try:
        res = db.users.update_one({"email": email}, {"$set": {"email_verified": True}})
        assert res.matched_count == 1, f"user row not created for {email}"
        db.otps.delete_one({"email": email})
    finally:
        mc.close()
    lr = s.post(f"{API}/auth/login", json={"email": email, "password": "Test@1234"}, timeout=30)
    assert lr.status_code == 200, f"login after verify {lr.status_code}: {lr.text[:300]}"
    s.email = email
    return s


@pytest.fixture(scope="session")
def admin_client():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=ADMIN, timeout=30)
    if r.status_code != 200:
        pytest.fail(f"Admin login failed {r.status_code}: {r.text[:300]}")
    return s


@pytest.fixture(scope="session")
def client_session():
    """Fresh registered + verified client."""
    return make_verified_client()


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
        assert starter["amount"] == 39999.0
        assert requests.get(f"{API}/services/nope", timeout=30).status_code == 404

    # INR currency migration: verify all package amounts are the new INR values
    def test_all_package_amounts_inr(self):
        expected = {
            "website_starter": 39999.0,
            "website_business": 119999.0,
            "website_premium": 239999.0,
            "maint_basic_monthly": 7999.0,
            "maint_pro_monthly": 19999.0,
            "app_mvp": 159999.0,
            "app_pro": 399999.0,
        }
        r = requests.get(f"{API}/services", timeout=30)
        assert r.status_code == 200
        found = {p["package_id"]: p["amount"] for s in r.json() for p in s["packages"]}
        for pid, amt in expected.items():
            assert pid in found, f"missing package {pid}: got {list(found)}"
            assert found[pid] == amt, f"{pid} expected {amt} got {found[pid]}"


# ---------------- Auth ----------------
class TestAuth:
    def test_register_creates_unverified_user_without_cookies(self):
        s = requests.Session()
        email = f"test_reg_{uuid.uuid4().hex[:8]}@labos.dev"
        r = s.post(f"{API}/auth/register",
                   json={"email": email, "password": "Test@1234", "name": "TEST Reg"}, timeout=30)
        # New contract: 200 + email_sent flag even when Resend send fails
        assert r.status_code == 200, f"expected 200 got {r.status_code}: {r.text[:300]}"
        body = r.json()
        assert body["ok"] is True, body
        assert body["email"] == email, body
        assert body["verification_required"] is True, body
        assert body["email_sent"] is False, body
        assert "access_token" not in r.headers.get("set-cookie", "")
        mc, db = _mongo_db()
        try:
            u = db.users.find_one({"email": email})
            assert u is not None
            assert u["email_verified"] is False
            assert u["role"] == "client"
        finally:
            mc.close()
        assert s.get(f"{API}/auth/me", timeout=30).status_code == 401

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
        assert b["amount"] == 39999.0
        assert b["package_name"] == "Starter Site"
        assert b["service_title"] == "Website Building"
        assert b["status"] == "new" and b["payment_status"] == "unpaid"
        assert "_id" not in b
        g = client_session.get(f"{API}/bookings/{b['booking_id']}", timeout=30)
        assert g.status_code == 200 and g.json()["amount"] == 39999.0

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
        s = make_verified_client("test_other")
        r = s.get(f"{API}/bookings/{package_booking['booking_id']}", timeout=30)
        assert r.status_code == 403


# ---------------- Payments (Razorpay) ----------------
BACKEND_ENV = dotenv_values("/app/backend/.env")


def _rzp_signature(order_id: str, payment_id: str, secret: str | None = None) -> str:
    import hmac as _hmac
    import hashlib as _hashlib
    secret = secret or BACKEND_ENV["RAZORPAY_KEY_SECRET"]
    return _hmac.new(secret.encode(), f"{order_id}|{payment_id}".encode(), _hashlib.sha256).hexdigest()


class TestPayments:
    def test_checkout_graceful_400_with_placeholder_keys(self, client_session, package_booking):
        """Placeholder Razorpay keys -> order.create fails. Must be a clean 400, not 500/502."""
        bid = package_booking["booking_id"]
        r = client_session.post(f"{API}/payments/checkout", json={
            "booking_id": bid, "origin_url": BASE_URL}, timeout=60)
        assert r.status_code == 400, f"expected 400 got {r.status_code}: {r.text[:300]}"
        detail = r.json().get("detail", "")
        # Iteration 4: diagnostic message must be actionable for placeholder keys
        assert "placeholder" in detail.lower(), detail
        assert "Replace" in detail, detail
        assert "dashboard.razorpay.com" in detail, detail

    def test_verify_bad_signature_400(self, client_session):
        r = client_session.post(f"{API}/payments/verify", json={
            "razorpay_order_id": "order_TESTbad",
            "razorpay_payment_id": "pay_TESTbad",
            "razorpay_signature": "deadbeef",
        }, timeout=30)
        assert r.status_code == 400, r.text
        assert r.json()["detail"] == "Invalid payment signature"

    def test_verify_good_signature_no_txn_404(self, client_session):
        oid = f"order_TEST{uuid.uuid4().hex[:8]}"
        pid = f"pay_TEST{uuid.uuid4().hex[:8]}"
        r = client_session.post(f"{API}/payments/verify", json={
            "razorpay_order_id": oid,
            "razorpay_payment_id": pid,
            "razorpay_signature": _rzp_signature(oid, pid),
        }, timeout=30)
        assert r.status_code == 404, f"expected 404 got {r.status_code}: {r.text[:300]}"
        assert r.json()["detail"] == "Transaction not found"

    def test_verify_requires_auth(self):
        oid, pid = "order_TESTauth", "pay_TESTauth"
        r = requests.post(f"{API}/payments/verify", json={
            "razorpay_order_id": oid, "razorpay_payment_id": pid,
            "razorpay_signature": _rzp_signature(oid, pid)}, timeout=30)
        assert r.status_code == 401

    def test_verify_missing_fields_422(self, client_session):
        r = client_session.post(f"{API}/payments/verify", json={"razorpay_order_id": "x"}, timeout=30)
        assert r.status_code == 422

    def test_verify_full_flow_with_seeded_txn(self, client_session, quote_booking):
        """Seed a payment_transaction directly, then verify with a valid HMAC signature.
        Confirms signature math + DB updates (txn paid, booking in_progress)."""
        from pymongo import MongoClient
        me = client_session.get(f"{API}/auth/me", timeout=30).json()
        oid = f"order_TEST{uuid.uuid4().hex[:10]}"
        pid = f"pay_TEST{uuid.uuid4().hex[:10]}"
        mc = MongoClient(BACKEND_ENV["MONGO_URL"])
        col = mc[BACKEND_ENV["DB_NAME"]].payment_transactions
        col.insert_one({
            "session_id": oid, "order_id": oid,
            "booking_id": quote_booking["booking_id"],
            "user_id": me["user_id"], "amount": 50000.0, "amount_paise": 5000000,
            "currency": "INR", "status": "initiated", "payment_status": "pending",
        })
        try:
            # status endpoint should now find it
            st = requests.get(f"{API}/payments/status/{oid}", timeout=30)
            assert st.status_code == 200, st.text
            sd = st.json()
            assert sd["order_id"] == oid
            assert sd["payment_status"] == "pending"
            assert sd["booking_id"] == quote_booking["booking_id"]

            r = client_session.post(f"{API}/payments/verify", json={
                "razorpay_order_id": oid, "razorpay_payment_id": pid,
                "razorpay_signature": _rzp_signature(oid, pid)}, timeout=30)
            assert r.status_code == 200, r.text
            assert r.json()["ok"] is True
            assert r.json()["booking_id"] == quote_booking["booking_id"]

            # persistence checks
            st2 = requests.get(f"{API}/payments/status/{oid}", timeout=30).json()
            assert st2["status"] == "completed" and st2["payment_status"] == "paid"
            b = client_session.get(f"{API}/bookings/{quote_booking['booking_id']}", timeout=30).json()
            assert b["payment_status"] == "paid"
            assert b["status"] == "in_progress"
        finally:
            col.delete_one({"order_id": oid})
            mc.close()

    def test_verify_other_user_forbidden(self, quote_booking):
        """Signature valid + txn exists but owned by another user -> 403."""
        from pymongo import MongoClient
        s = make_verified_client("test_pay")
        oid = f"order_TEST{uuid.uuid4().hex[:10]}"
        pid = f"pay_TEST{uuid.uuid4().hex[:10]}"
        mc = MongoClient(BACKEND_ENV["MONGO_URL"])
        col = mc[BACKEND_ENV["DB_NAME"]].payment_transactions
        col.insert_one({
            "session_id": oid, "order_id": oid, "booking_id": quote_booking["booking_id"],
            "user_id": "user_not_this_one", "amount": 100.0, "currency": "INR",
            "status": "initiated", "payment_status": "pending"})
        try:
            r = s.post(f"{API}/payments/verify", json={
                "razorpay_order_id": oid, "razorpay_payment_id": pid,
                "razorpay_signature": _rzp_signature(oid, pid)}, timeout=30)
            assert r.status_code == 403, f"expected 403 got {r.status_code}: {r.text[:200]}"
        finally:
            col.delete_one({"order_id": oid})
            mc.close()

    # ---- Webhook ----
    def test_webhook_bad_signature_400(self):
        r = requests.post(f"{API}/webhook/razorpay", data=b'{"event":"payment.captured"}',
                          headers={"X-Razorpay-Signature": "bad", "Content-Type": "application/json"},
                          timeout=30)
        assert r.status_code == 400, r.text
        assert r.json()["detail"] == "Invalid webhook signature"

    def test_webhook_missing_signature_400(self):
        r = requests.post(f"{API}/webhook/razorpay", data=b'{}',
                          headers={"Content-Type": "application/json"}, timeout=30)
        assert r.status_code == 400

    def test_webhook_valid_signature_marks_paid(self, client_session):
        import hmac as _hmac
        import hashlib as _hashlib
        import json as _json
        from pymongo import MongoClient
        # dedicated booking so we don't clash with other tests
        b = client_session.post(f"{API}/bookings", json={
            "service_slug": "website-building", "package_id": "website_business",
            "booking_type": "package", "project_title": "TEST webhook booking",
            "requirements": "webhook flow test"}, timeout=30).json()
        me = client_session.get(f"{API}/auth/me", timeout=30).json()
        oid = f"order_TEST{uuid.uuid4().hex[:10]}"
        pid = f"pay_TEST{uuid.uuid4().hex[:10]}"
        mc = MongoClient(BACKEND_ENV["MONGO_URL"])
        col = mc[BACKEND_ENV["DB_NAME"]].payment_transactions
        col.insert_one({
            "session_id": oid, "order_id": oid, "booking_id": b["booking_id"],
            "user_id": me["user_id"], "amount": 119999.0, "currency": "INR",
            "status": "initiated", "payment_status": "pending"})
        try:
            body = _json.dumps({
                "event": "payment.captured",
                "payload": {"payment": {"entity": {"id": pid, "order_id": oid}}},
            }).encode()
            sig = _hmac.new(BACKEND_ENV["RAZORPAY_WEBHOOK_SECRET"].encode(), body,
                            _hashlib.sha256).hexdigest()
            r = requests.post(f"{API}/webhook/razorpay", data=body,
                              headers={"X-Razorpay-Signature": sig,
                                       "Content-Type": "application/json"}, timeout=30)
            assert r.status_code == 200, r.text
            assert r.json() == {"received": True}
            st = requests.get(f"{API}/payments/status/{oid}", timeout=30).json()
            assert st["payment_status"] == "paid" and st["status"] == "completed"
            bk = client_session.get(f"{API}/bookings/{b['booking_id']}", timeout=30).json()
            assert bk["payment_status"] == "paid" and bk["status"] == "in_progress"
        finally:
            col.delete_one({"order_id": oid})
            mc.close()

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

    def test_update_quote_booking_then_pay(self, admin_client, client_session):
        fresh = client_session.post(f"{API}/bookings", json={
            "service_slug": "application-building", "booking_type": "quote",
            "project_title": "TEST admin quote flow", "requirements": "quote me please"},
            timeout=30).json()
        bid = fresh["booking_id"]
        r = admin_client.patch(f"{API}/admin/bookings/{bid}", json={
            "amount": 50000, "status": "quoted", "admin_notes": "quoted at 50000"}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["amount"] == 50000
        assert d["status"] == "quoted"
        assert d["admin_notes"] == "quoted at 50000"
        mine = client_session.get(f"{API}/bookings/mine", timeout=30).json()
        row = [b for b in mine if b["booking_id"] == bid][0]
        assert row["amount"] == 50000 and row["status"] == "quoted"
        # Razorpay placeholder keys -> graceful 400
        c = client_session.post(f"{API}/payments/checkout", json={
            "booking_id": bid, "origin_url": BASE_URL}, timeout=60)
        assert c.status_code == 400, f"expected 400 got {c.status_code}: {c.text[:200]}"
        assert "placeholder" in c.json()["detail"].lower(), c.text

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
