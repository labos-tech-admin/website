"""Email OTP verification flow tests (Resend key is a placeholder — no real emails sent).

Positive verify-otp path is tested by seeding db.otps with a bcrypt-hashed code.
"""
import os
import re
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

sys.path.insert(0, "/app/backend")
from auth_utils import hash_password  # noqa: E402

frontend_env = dotenv_values("/app/frontend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL")
            or frontend_env["REACT_APP_BACKEND_URL"]).rstrip("/")
API = f"{BASE_URL}/api"
BE = dotenv_values("/app/backend/.env")


def _creds():
    content = Path("/app/memory/test_credentials.md").read_text(encoding="utf-8")
    email = re.search(r'(?im)^\s*[-*]\s*\*\*Email\*\*\s*:\s*`?([^`\s]+)', content)
    pwd = re.search(r'(?im)^\s*[-*]\s*\*\*Password\*\*\s*:\s*`?([^`\s]+)', content)
    return {"email": email.group(1), "password": pwd.group(1)}


ADMIN = _creds()


@pytest.fixture(scope="module")
def db():
    from pymongo import MongoClient
    mc = MongoClient(BE["MONGO_URL"])
    yield mc[BE["DB_NAME"]]
    mc.close()


@pytest.fixture
def created_emails(db):
    emails = []
    yield emails
    for e in emails:
        db.users.delete_one({"email": e})
        db.otps.delete_one({"email": e})


def register(session, email, password="Test@1234", name="TEST OTP User"):
    return session.post(f"{API}/auth/register",
                        json={"email": email, "password": password, "name": name}, timeout=30)


def seed_otp(db, email, code="123456", attempts=0, ttl_min=10, last_sent_offset_sec=None,
             email_sent=False):
    now = datetime.now(timezone.utc)
    doc = {
        "email": email,
        "code_hash": hash_password(code),
        "expires_at": now + timedelta(minutes=ttl_min),
        "attempts": attempts,
        "last_sent_at": (now - timedelta(seconds=last_sent_offset_sec or 0)).isoformat(),
        "email_sent": email_sent,
    }
    db.otps.update_one({"email": email}, {"$set": doc}, upsert=True)


LEAK_TOKENS = ("RESEND_API_KEY", ".env", "Set ", "resend.com")


def assert_no_internal_leak(text):
    for token in LEAK_TOKENS:
        assert token not in text, f"internal detail leaked ({token!r}): {text}"


# ---------------- Register / OTP issuance ----------------
class TestRegisterOtp:
    def test_register_new_user_200_email_sent_false(self, db, created_emails):
        email = f"test_otp_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        s = requests.Session()
        r = register(s, email)
        assert r.status_code == 200, f"expected 200 got {r.status_code}: {r.text[:300]}"
        body = r.json()
        assert body["ok"] is True, body
        assert body["email"] == email, body
        assert body["verification_required"] is True, body
        assert body["email_sent"] is False, body
        # user row created, unverified
        u = db.users.find_one({"email": email})
        assert u is not None and u["email_verified"] is False
        # no auth cookies
        cookies = r.headers.get("set-cookie", "")
        assert "access_token" not in cookies and "refresh_token" not in cookies
        assert "access_token" not in s.cookies and "refresh_token" not in s.cookies

    def test_otp_stored_hashed_not_plaintext(self, db, created_emails):
        email = f"test_otphash_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        register(requests.Session(), email)
        doc = db.otps.find_one({"email": email})
        assert doc is not None, "OTP doc should be created even though send failed"
        assert "code" not in doc, f"plaintext code leaked: {doc}"
        assert doc["code_hash"].startswith("$2b$")
        assert doc["attempts"] == 0
        assert doc.get("email_sent") is False, doc
        assert "expires_at" in doc and "last_sent_at" in doc

    def test_register_lowercases_email_and_no_leak_in_body(self, db, created_emails):
        raw = f"TEST_Case_{uuid.uuid4().hex[:8]}@Labos.DEV"
        email = raw.lower()
        created_emails.append(email)
        r = register(requests.Session(), raw)
        assert r.status_code == 200, r.text
        assert r.json()["email"] == email, r.text
        assert_no_internal_leak(r.text)
        assert db.users.find_one({"email": email}) is not None
        assert db.otps.find_one({"email": email}) is not None

    def test_register_existing_verified_email_400(self):
        r = register(requests.Session(), ADMIN["email"], ADMIN["password"], "Dup")
        assert r.status_code == 400
        assert r.json()["detail"] == "Email already registered"

    def test_register_existing_unverified_updates_password(self, db, created_emails):
        email = f"test_reunverified_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        register(requests.Session(), email, "Test@1234")
        old = db.users.find_one({"email": email})["password_hash"]
        # cooldown must NOT apply because the previous send failed (email_sent=False)
        r = register(requests.Session(), email, "NewPass@9876", "TEST Renamed")
        assert r.status_code == 200, r.text
        assert r.json()["email_sent"] is False, r.text
        u = db.users.find_one({"email": email})
        assert u["password_hash"] != old, "password should be updated on re-register"
        assert u["name"] == "TEST Renamed"
        assert u["email_verified"] is False

    def test_resend_within_cooldown_returns_429(self, db, created_emails):
        """Cooldown applies only when the previous send succeeded."""
        email = f"test_cooldown_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        register(requests.Session(), email)
        seed_otp(db, email, "999999", last_sent_offset_sec=0, email_sent=True)
        r = requests.post(f"{API}/auth/resend-otp", json={"email": email}, timeout=30)
        assert r.status_code == 429, f"expected 429 got {r.status_code}: {r.text[:300]}"
        assert re.search(r"Please wait \d+s", r.json()["detail"]), r.json()["detail"]
        # existing OTP must not be rotated while rate-limited
        assert db.otps.find_one({"email": email})["email_sent"] is True

    def test_resend_not_cooldown_limited_when_previous_send_failed(self, db, created_emails):
        email = f"test_nocooldown_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        register(requests.Session(), email)  # leaves email_sent=False, last_sent_at=now
        r = requests.post(f"{API}/auth/resend-otp", json={"email": email}, timeout=30)
        assert r.status_code == 400, f"expected 400 got {r.status_code}: {r.text[:300]}"
        detail = r.json()["detail"]
        assert detail == ("Couldn't send the verification email right now. "
                          "Please try again in a moment."), detail
        assert_no_internal_leak(detail)


# ---------------- Resend OTP ----------------
class TestResendOtp:
    def test_resend_unknown_email_silent_ok(self):
        r = requests.post(f"{API}/auth/resend-otp",
                          json={"email": f"nobody_{uuid.uuid4().hex[:8]}@labos.dev"}, timeout=30)
        assert r.status_code == 200
        assert r.json() == {"ok": True}

    def test_resend_already_verified_400(self):
        r = requests.post(f"{API}/auth/resend-otp", json={"email": ADMIN["email"]}, timeout=30)
        assert r.status_code == 400
        assert "already verified" in r.json()["detail"].lower()

    def test_resend_unverified_generic_error_no_leak(self, db, created_emails):
        email = f"test_resend_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        register(requests.Session(), email)
        db.otps.delete_one({"email": email})  # no pending OTP at all
        r = requests.post(f"{API}/auth/resend-otp", json={"email": email}, timeout=30)
        assert r.status_code == 400, f"expected 400 got {r.status_code}: {r.text[:300]}"
        detail = r.json()["detail"]
        assert detail == ("Couldn't send the verification email right now. "
                          "Please try again in a moment."), detail
        assert_no_internal_leak(detail)
        # a fresh OTP is still stored so the user can verify if the mail lands later
        doc = db.otps.find_one({"email": email})
        assert doc is not None and doc["code_hash"].startswith("$2b$")
        assert doc.get("email_sent") is False


# ---------------- Login gating ----------------
class TestLoginGating:
    def test_login_unverified_403_structured(self, db, created_emails):
        email = f"test_login403_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        register(requests.Session(), email)
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": "Test@1234"}, timeout=30)
        assert r.status_code == 403, f"expected 403 got {r.status_code}: {r.text[:300]}"
        detail = r.json()["detail"]
        assert isinstance(detail, dict), detail
        assert detail["code"] == "email_not_verified"
        assert detail["email"] == email
        assert "access_token" not in r.headers.get("set-cookie", "")

    def test_login_unverified_wrong_password_still_401(self, db, created_emails):
        email = f"test_login401_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        register(requests.Session(), email)
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": "Nope@1234"}, timeout=30)
        assert r.status_code == 401

    def test_admin_login_still_works(self):
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json=ADMIN, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["role"] == "admin"
        assert d.get("email_verified") is True
        assert "HttpOnly" in r.headers.get("set-cookie", "")


# ---------------- Verify OTP ----------------
class TestVerifyOtp:
    def test_no_otp_record_400(self, db, created_emails):
        email = f"test_v_noopt_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        register(requests.Session(), email)
        db.otps.delete_one({"email": email})
        r = requests.post(f"{API}/auth/verify-otp", json={"email": email, "code": "123456"}, timeout=30)
        assert r.status_code == 400
        assert "No verification code pending" in r.json()["detail"]

    def test_non_digit_code_400(self, db, created_emails):
        email = f"test_v_fmt_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        register(requests.Session(), email)
        for bad in ("12345", "abcdef", "1234567"):
            r = requests.post(f"{API}/auth/verify-otp", json={"email": email, "code": bad}, timeout=30)
            assert r.status_code == 400, bad
            assert r.json()["detail"] == "Code must be 6 digits"

    def test_wrong_code_increments_attempts(self, db, created_emails):
        email = f"test_v_bad_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        register(requests.Session(), email)
        seed_otp(db, email, "654321")
        r = requests.post(f"{API}/auth/verify-otp", json={"email": email, "code": "111111"}, timeout=30)
        assert r.status_code == 400, r.text
        assert r.json()["detail"] == "Incorrect code"
        assert db.otps.find_one({"email": email})["attempts"] == 1

    def test_five_wrong_attempts_429_and_otp_deleted(self, db, created_emails):
        email = f"test_v_lock_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        register(requests.Session(), email)
        seed_otp(db, email, "654321")
        for i in range(5):
            r = requests.post(f"{API}/auth/verify-otp", json={"email": email, "code": "111111"}, timeout=30)
            assert r.status_code == 400, f"attempt {i + 1}: {r.status_code} {r.text[:200]}"
        assert db.otps.find_one({"email": email})["attempts"] == 5
        r = requests.post(f"{API}/auth/verify-otp", json={"email": email, "code": "111111"}, timeout=30)
        assert r.status_code == 429, f"expected 429 got {r.status_code}: {r.text[:200]}"
        assert "Too many attempts" in r.json()["detail"]
        assert db.otps.find_one({"email": email}) is None, "OTP must be deleted after lockout"

    def test_expired_otp_400_and_deleted(self, db, created_emails):
        email = f"test_v_exp_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        register(requests.Session(), email)
        seed_otp(db, email, "654321", ttl_min=-5)
        r = requests.post(f"{API}/auth/verify-otp", json={"email": email, "code": "654321"}, timeout=30)
        assert r.status_code == 400, r.text
        assert "expired" in r.json()["detail"].lower()
        assert db.otps.find_one({"email": email}) is None

    def test_correct_code_verifies_and_logs_in(self, db, created_emails):
        email = f"test_v_ok_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        register(requests.Session(), email)
        seed_otp(db, email, "246810")
        s = requests.Session()
        r = s.post(f"{API}/auth/verify-otp", json={"email": email, "code": "246810"}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["email"] == email
        assert d["email_verified"] is True
        assert "password_hash" not in d and "_id" not in d
        cookies = r.headers.get("set-cookie", "")
        assert "access_token" in cookies and "HttpOnly" in cookies
        assert "refresh_token" in cookies
        # OTP consumed
        assert db.otps.find_one({"email": email}) is None
        # persisted
        assert db.users.find_one({"email": email})["email_verified"] is True
        # session works
        me = s.get(f"{API}/auth/me", timeout=30)
        assert me.status_code == 200 and me.json()["email"] == email
        # login now allowed
        lr = requests.post(f"{API}/auth/login", json={"email": email, "password": "Test@1234"}, timeout=30)
        assert lr.status_code == 200, lr.text
        # reused OTP no longer valid
        r2 = requests.post(f"{API}/auth/verify-otp", json={"email": email, "code": "246810"}, timeout=30)
        assert r2.status_code == 400
        assert "No verification code pending" in r2.json()["detail"]

    def test_verify_with_no_user_account_404(self, db):
        email = f"test_v_nouser_{uuid.uuid4().hex[:8]}@labos.dev"
        seed_otp(db, email, "135790")
        try:
            r = requests.post(f"{API}/auth/verify-otp", json={"email": email, "code": "135790"}, timeout=30)
            assert r.status_code == 404, f"expected 404 got {r.status_code}: {r.text[:200]}"
        finally:
            db.otps.delete_one({"email": email})


# ---------------- Indexes / TTL ----------------
class TestOtpIndexes:
    def test_ttl_index_on_expires_at(self, db):
        idx = db.otps.index_information()
        ttl = [v for v in idx.values() if v.get("expireAfterSeconds") is not None]
        assert ttl, f"no TTL index on otps: {idx}"
        assert any(("expires_at", 1) in v["key"] for v in ttl), idx
        assert all(v["expireAfterSeconds"] == 0 for v in ttl)

    def test_unique_index_on_email(self, db):
        idx = db.otps.index_information()
        assert any(v.get("unique") and ("email", 1) in v["key"] for v in idx.values()), idx

    def test_expires_at_stored_as_bson_date(self, db, created_emails):
        """TTL monitor only expires BSON dates — string expires_at would never expire."""
        email = f"test_ttl_{uuid.uuid4().hex[:8]}@labos.dev"
        created_emails.append(email)
        register(requests.Session(), email)
        doc = db.otps.find_one({"email": email})
        assert isinstance(doc["expires_at"], datetime), type(doc["expires_at"])


# ---------------- Google OAuth code path ----------------
class TestEmergentSession:
    def test_invalid_session_id_rejected(self):
        r = requests.post(f"{API}/auth/emergent/session",
                          json={"session_id": f"bogus_{uuid.uuid4().hex}"}, timeout=60)
        assert r.status_code in (400, 401, 422, 502), f"{r.status_code}: {r.text[:200]}"
        assert r.status_code != 500, "should not be an unhandled 500"

    def test_google_users_marked_verified_in_code(self):
        src = Path("/app/backend/server.py").read_text()
        block = src[src.index('@api.post("/auth/emergent/session")'):src.index('@api.get("/services")')]
        assert block.count('"email_verified": True') == 2, "both create+update paths must set email_verified"
