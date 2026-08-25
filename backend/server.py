from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from models import (
    RegisterRequest, LoginRequest, EmergentSessionRequest,
    BookingCreate, BookingUpdate, CheckoutRequest, ContactCreate,
    utcnow, new_id,
)
from auth_utils import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    set_auth_cookies, set_session_cookie, clear_auth_cookies,
    get_current_user, require_admin, fetch_emergent_session_data,
    _decode,
)
from services_catalog import SERVICES, get_service, get_package

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest,
)
import razorpay
import hmac
import hashlib

# ---------- Setup ----------
mongo_url = os.environ["MONGO_URL"]
mongo_client = AsyncIOMotorClient(mongo_url)
db = mongo_client[os.environ["DB_NAME"]]

app = FastAPI(title="LABOS Technologies API")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("labos")


# ---------- Startup ----------
@app.on_event("startup")
async def on_startup():
    # Indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id", unique=True)
    await db.user_sessions.create_index("session_token", unique=True)
    await db.user_sessions.create_index("expires_at", expireAfterSeconds=0)
    await db.bookings.create_index("booking_id", unique=True)
    await db.payment_transactions.create_index("order_id", sparse=True)

    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@labos.tech").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    admin_name = os.environ.get("ADMIN_NAME", "Admin")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "user_id": new_id("user_"),
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": admin_name,
            "role": "admin",
            "auth_provider": "password",
            "created_at": utcnow().isoformat(),
        })
        logger.info("Seeded admin user %s", admin_email)
    else:
        # Keep password in sync with .env
        if not existing.get("password_hash") or not verify_password(admin_password, existing["password_hash"]):
            await db.users.update_one({"email": admin_email},
                                      {"$set": {"password_hash": hash_password(admin_password),
                                                "role": "admin"}})


@app.on_event("shutdown")
async def on_shutdown():
    mongo_client.close()


# ---------- Helpers ----------
def _clean_user(doc: dict) -> dict:
    doc.pop("_id", None)
    doc.pop("password_hash", None)
    return doc


async def _current_user_dep(request: Request) -> dict:
    return await get_current_user(request, db)


async def _admin_dep(request: Request) -> dict:
    return await require_admin(request, db)


# ---------- Root ----------
@api.get("/")
async def root():
    return {"service": "LABOS Technologies API", "status": "ok"}


# ---------- Auth ----------
@api.post("/auth/register")
async def register(payload: RegisterRequest, response: Response):
    email = payload.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = new_id("user_")
    doc = {
        "user_id": user_id,
        "email": email,
        "password_hash": hash_password(payload.password),
        "name": payload.name.strip(),
        "role": "client",
        "auth_provider": "password",
        "created_at": utcnow().isoformat(),
    }
    await db.users.insert_one(doc)
    access = create_access_token(user_id, email, "client")
    refresh = create_refresh_token(user_id)
    set_auth_cookies(response, access, refresh)
    return _clean_user(doc)


@api.post("/auth/login")
async def login(payload: LoginRequest, response: Response):
    email = payload.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not user.get("password_hash") or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access = create_access_token(user["user_id"], email, user.get("role", "client"))
    refresh = create_refresh_token(user["user_id"])
    set_auth_cookies(response, access, refresh)
    return _clean_user(user)


@api.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    clear_auth_cookies(response)
    return {"ok": True}


@api.get("/auth/me")
async def me(user: dict = Depends(_current_user_dep)):
    return _clean_user(user)


@api.post("/auth/refresh")
async def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = _decode(token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = await db.users.find_one({"user_id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access = create_access_token(user["user_id"], user["email"], user.get("role", "client"))
    response.set_cookie("access_token", access, httponly=True, secure=True,
                        samesite="none", max_age=60 * 60 * 24, path="/")
    return {"ok": True}


@api.post("/auth/emergent/session")
async def emergent_session(payload: EmergentSessionRequest, response: Response):
    """Exchange Emergent session_id → local session (Google OAuth flow)."""
    data = await fetch_emergent_session_data(payload.session_id)
    email = data["email"].lower()
    name = data.get("name") or email.split("@")[0]
    picture = data.get("picture")
    session_token = data["session_token"]

    existing = await db.users.find_one({"email": email})
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one({"user_id": user_id},
                                  {"$set": {"name": name, "picture": picture}})
    else:
        user_id = new_id("user_")
        await db.users.insert_one({
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "role": "client",
            "auth_provider": "google",
            "created_at": utcnow().isoformat(),
        })

    expires_at = utcnow() + timedelta(days=7)
    await db.user_sessions.update_one(
        {"session_token": session_token},
        {"$set": {"user_id": user_id, "session_token": session_token, "expires_at": expires_at}},
        upsert=True,
    )
    set_session_cookie(response, session_token)
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    return user


# ---------- Services (public) ----------
@api.get("/services")
async def list_services():
    return SERVICES


@api.get("/services/{slug}")
async def get_service_endpoint(slug: str):
    svc = get_service(slug)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    return svc


# ---------- Bookings ----------
@api.post("/bookings")
async def create_booking(payload: BookingCreate, user: dict = Depends(_current_user_dep)):
    svc = get_service(payload.service_slug)
    if not svc:
        raise HTTPException(status_code=400, detail="Invalid service")

    package = None
    amount = None
    package_name = None
    if payload.booking_type == "package":
        if not payload.package_id:
            raise HTTPException(status_code=400, detail="package_id is required for package bookings")
        package = get_package(payload.service_slug, payload.package_id)
        if not package:
            raise HTTPException(status_code=400, detail="Invalid package")
        amount = package["amount"]
        package_name = package["name"]

    booking_id = new_id("bk_")
    now = utcnow().isoformat()
    doc = {
        "booking_id": booking_id,
        "client_id": user["user_id"],
        "client_email": user["email"],
        "client_name": user.get("name", ""),
        "service_slug": svc["slug"],
        "service_title": svc["title"],
        "package_id": payload.package_id,
        "package_name": package_name,
        "booking_type": payload.booking_type,
        "project_title": payload.project_title,
        "requirements": payload.requirements,
        "budget": payload.budget,
        "timeline": payload.timeline,
        "contact_phone": payload.contact_phone,
        "amount": amount,
        "status": "new",
        "payment_status": "unpaid",
        "admin_notes": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.bookings.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api.get("/bookings/mine")
async def my_bookings(user: dict = Depends(_current_user_dep)):
    cursor = db.bookings.find({"client_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1)
    return await cursor.to_list(500)


@api.get("/bookings/{booking_id}")
async def get_booking(booking_id: str, user: dict = Depends(_current_user_dep)):
    booking = await db.bookings.find_one({"booking_id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if user.get("role") != "admin" and booking["client_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    return booking


# ---------- Payments (Razorpay) ----------
def _clean_env(name: str) -> str:
    """Read env var and strip surrounding whitespace/quotes."""
    return os.environ.get(name, "").strip().strip('"').strip("'")


def _get_razorpay() -> razorpay.Client:
    key_id = _clean_env("RAZORPAY_KEY_ID")
    key_secret = _clean_env("RAZORPAY_KEY_SECRET")

    # Sanity checks with actionable messages
    if not key_id or not key_secret:
        raise HTTPException(
            status_code=400,
            detail="Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in backend/.env",
        )
    if "placeholder" in key_id.lower() or "placeholder" in key_secret.lower():
        raise HTTPException(
            status_code=400,
            detail="Razorpay keys are still placeholders. Replace RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in backend/.env with real keys from https://dashboard.razorpay.com/app/keys",
        )
    if not (key_id.startswith("rzp_test_") or key_id.startswith("rzp_live_")):
        raise HTTPException(
            status_code=400,
            detail=f"RAZORPAY_KEY_ID must start with 'rzp_test_' or 'rzp_live_'. Got: '{key_id[:15]}...'. Copy the Key Id (NOT the secret) from Razorpay Dashboard → Settings → API Keys.",
        )
    return razorpay.Client(auth=(key_id, key_secret))


@api.post("/payments/checkout")
async def create_checkout(payload: CheckoutRequest,
                          user: dict = Depends(_current_user_dep)):
    """Create a Razorpay Order for a booking. Returns order details for the
    frontend to open the Razorpay Checkout modal."""
    booking = await db.bookings.find_one({"booking_id": payload.booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["client_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not booking.get("amount") or booking["amount"] <= 0:
        raise HTTPException(status_code=400, detail="Booking has no amount to pay yet")
    if booking.get("payment_status") == "paid":
        raise HTTPException(status_code=400, detail="Already paid")

    amount_paise = int(round(float(booking["amount"]) * 100))
    receipt = f"lb_{booking['booking_id']}"[:40]

    try:
        client = _get_razorpay()
        order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "notes": {
                "booking_id": booking["booking_id"],
                "user_id": user["user_id"],
                "project_title": booking.get("project_title", ""),
            },
        })
    except HTTPException:
        raise
    except Exception as e:
        err_msg = str(e)
        logger.error("Razorpay order.create failed: %s", err_msg)
        if "Authentication failed" in err_msg or "401" in err_msg:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Razorpay rejected your credentials (Authentication failed). "
                    "Common causes: (1) Key Id and Key Secret are swapped, "
                    "(2) extra spaces/quotes in the .env values, "
                    "(3) test keys used in Live mode or live keys in Test mode, "
                    "(4) backend not restarted after .env edit. "
                    "Regenerate keys at https://dashboard.razorpay.com/app/keys and restart uvicorn."
                ),
            )
        raise HTTPException(status_code=400, detail=f"Payment gateway error: {err_msg}")

    await db.payment_transactions.insert_one({
        "session_id": order["id"],  # kept as 'session_id' for schema continuity
        "order_id": order["id"],
        "booking_id": booking["booking_id"],
        "user_id": user["user_id"],
        "amount": float(booking["amount"]),
        "amount_paise": amount_paise,
        "currency": "INR",
        "status": "initiated",
        "payment_status": "pending",
        "created_at": utcnow().isoformat(),
        "updated_at": utcnow().isoformat(),
    })
    await db.bookings.update_one(
        {"booking_id": booking["booking_id"]},
        {"$set": {"payment_status": "pending", "updated_at": utcnow().isoformat()}},
    )
    return {
        "order_id": order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "key_id": _clean_env("RAZORPAY_KEY_ID"),
        "booking_id": booking["booking_id"],
        "project_title": booking.get("project_title", ""),
        "customer_name": user.get("name", ""),
        "customer_email": user.get("email", ""),
    }


class RazorpayVerifyRequest(__import__("pydantic").BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@api.post("/payments/verify")
async def verify_payment(payload: RazorpayVerifyRequest,
                         user: dict = Depends(_current_user_dep)):
    """Verify Razorpay Checkout signature and mark booking paid."""
    secret = _clean_env("RAZORPAY_KEY_SECRET").encode()
    body = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode()
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, payload.razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    txn = await db.payment_transactions.find_one({"order_id": payload.razorpay_order_id})
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if txn["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    await db.payment_transactions.update_one(
        {"order_id": payload.razorpay_order_id},
        {"$set": {
            "status": "completed",
            "payment_status": "paid",
            "razorpay_payment_id": payload.razorpay_payment_id,
            "updated_at": utcnow().isoformat(),
        }},
    )
    await db.bookings.update_one(
        {"booking_id": txn["booking_id"]},
        {"$set": {
            "payment_status": "paid",
            "status": "in_progress",
            "updated_at": utcnow().isoformat(),
        }},
    )
    return {"ok": True, "booking_id": txn["booking_id"]}


@api.get("/payments/status/{order_id}")
async def payment_status(order_id: str):
    record = await db.payment_transactions.find_one({"order_id": order_id}, {"_id": 0})
    if not record:
        # Backward-compat: some records might only have session_id
        record = await db.payment_transactions.find_one({"session_id": order_id}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {
        "order_id": record.get("order_id") or record.get("session_id"),
        "status": record["status"],
        "payment_status": record["payment_status"],
        "booking_id": record.get("booking_id"),
    }


@api.post("/webhook/razorpay")
async def razorpay_webhook(request: Request):
    """Fallback path in case the client never completes the verify call.
    Configure this URL in Razorpay Dashboard → Webhooks with the same secret."""
    body = await request.body()
    sig = request.headers.get("X-Razorpay-Signature", "")
    secret = _clean_env("RAZORPAY_WEBHOOK_SECRET").encode()
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not (sig and hmac.compare_digest(expected, sig)):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    import json as _json
    event = _json.loads(body.decode() or "{}")
    if event.get("event") == "payment.captured":
        payment = event.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment.get("order_id")
        payment_id = payment.get("id")
        if order_id:
            txn = await db.payment_transactions.find_one({"order_id": order_id})
            if txn and txn.get("payment_status") != "paid":
                await db.payment_transactions.update_one(
                    {"order_id": order_id},
                    {"$set": {"status": "completed", "payment_status": "paid",
                              "razorpay_payment_id": payment_id,
                              "updated_at": utcnow().isoformat()}},
                )
                await db.bookings.update_one(
                    {"booking_id": txn["booking_id"]},
                    {"$set": {"payment_status": "paid", "status": "in_progress",
                              "updated_at": utcnow().isoformat()}},
                )
    return {"received": True}


# ---------- Contact ----------
@api.post("/contact")
async def submit_contact(payload: ContactCreate):
    doc = {
        "contact_id": new_id("ct_"),
        "name": payload.name,
        "email": payload.email,
        "subject": payload.subject,
        "message": payload.message,
        "handled": False,
        "created_at": utcnow().isoformat(),
    }
    await db.contacts.insert_one(doc)
    doc.pop("_id", None)
    return {"ok": True}


# ---------- Admin ----------
@api.get("/admin/stats")
async def admin_stats(_: dict = Depends(_admin_dep)):
    total_clients = await db.users.count_documents({"role": "client"})
    total_bookings = await db.bookings.count_documents({})
    active_bookings = await db.bookings.count_documents({"status": {"$in": ["new", "quoted", "in_progress"]}})
    paid_bookings = await db.bookings.count_documents({"payment_status": "paid"})
    contacts = await db.contacts.count_documents({})
    revenue_agg = await db.payment_transactions.aggregate([
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]).to_list(1)
    revenue = revenue_agg[0]["total"] if revenue_agg else 0.0
    return {
        "total_clients": total_clients,
        "total_bookings": total_bookings,
        "active_bookings": active_bookings,
        "paid_bookings": paid_bookings,
        "contact_messages": contacts,
        "revenue": revenue,
    }


@api.get("/admin/clients")
async def admin_clients(_: dict = Depends(_admin_dep)):
    cursor = db.users.find({"role": "client"}, {"_id": 0, "password_hash": 0}).sort("created_at", -1)
    return await cursor.to_list(1000)


@api.get("/admin/bookings")
async def admin_bookings(_: dict = Depends(_admin_dep)):
    cursor = db.bookings.find({}, {"_id": 0}).sort("created_at", -1)
    return await cursor.to_list(1000)


@api.patch("/admin/bookings/{booking_id}")
async def admin_update_booking(booking_id: str, payload: BookingUpdate,
                               _: dict = Depends(_admin_dep)):
    booking = await db.bookings.find_one({"booking_id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    update = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if payload.amount is not None and booking.get("booking_type") == "quote":
        update["status"] = update.get("status", "quoted")
    update["updated_at"] = utcnow().isoformat()
    await db.bookings.update_one({"booking_id": booking_id}, {"$set": update})
    updated = await db.bookings.find_one({"booking_id": booking_id}, {"_id": 0})
    return updated


@api.get("/admin/contacts")
async def admin_contacts(_: dict = Depends(_admin_dep)):
    cursor = db.contacts.find({}, {"_id": 0}).sort("created_at", -1)
    return await cursor.to_list(500)


# ---------- Mount ----------
app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()] or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
