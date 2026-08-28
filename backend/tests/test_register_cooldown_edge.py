"""Edge case: re-register an unverified email whose previous OTP send SUCCEEDED
(within cooldown). Verifies whether the password write is rolled back / whether
the caller gets a 429 after the mutation (iteration-5 finding #2)."""
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

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


@pytest.fixture(scope="module")
def db():
    from pymongo import MongoClient
    mc = MongoClient(BE["MONGO_URL"])
    yield mc[BE["DB_NAME"]]
    mc.close()


def test_reregister_within_successful_send_cooldown(db):
    email = f"test_cdreg_{uuid.uuid4().hex[:8]}@labos.dev"
    try:
        r = requests.post(f"{API}/auth/register",
                          json={"email": email, "password": "Test@1234", "name": "TEST CD"},
                          timeout=30)
        assert r.status_code == 200, r.text
        old_hash = db.users.find_one({"email": email})["password_hash"]
        now = datetime.now(timezone.utc)
        db.otps.update_one({"email": email}, {"$set": {
            "email_sent": True,
            "last_sent_at": now.isoformat(),
            "code_hash": hash_password("111222"),
            "expires_at": now + timedelta(minutes=10),
            "attempts": 0,
        }}, upsert=True)
        r2 = requests.post(f"{API}/auth/register",
                           json={"email": email, "password": "Other@9999", "name": "TEST CD2"},
                           timeout=30)
        new_hash = db.users.find_one({"email": email})["password_hash"]
        print("status:", r2.status_code, r2.text[:200])
        print("password_changed:", new_hash != old_hash)
        # document behaviour: 429 while credentials already mutated is the residual issue
        assert r2.status_code in (200, 429), r2.text
        if r2.status_code == 429:
            assert new_hash == old_hash, (
                "REGRESSION: register returned 429 but the password was already overwritten")
    finally:
        db.users.delete_one({"email": email})
        db.otps.delete_one({"email": email})
