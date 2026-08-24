"""Pydantic models for LABOS Technologies backend."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List, Literal
import uuid

from pydantic import BaseModel, Field, EmailStr, ConfigDict


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str = "") -> str:
    uid = uuid.uuid4().hex[:16]
    return f"{prefix}{uid}" if prefix else uid


class UserPublic(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: EmailStr
    name: str
    role: Literal["admin", "client"] = "client"
    picture: Optional[str] = None
    auth_provider: Literal["password", "google"] = "password"
    created_at: datetime


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=80)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class EmergentSessionRequest(BaseModel):
    session_id: str


# ---------- Services / Bookings ----------

class ServicePackage(BaseModel):
    package_id: str
    name: str
    description: str
    amount: float  # USD
    highlights: List[str] = []


class Service(BaseModel):
    slug: str
    title: str
    tagline: str
    description: str
    image: str
    packages: List[ServicePackage] = []


class BookingCreate(BaseModel):
    service_slug: str
    package_id: Optional[str] = None  # if picking a fixed package
    booking_type: Literal["package", "quote"] = "package"
    # Quote form fields
    project_title: str = Field(min_length=2, max_length=120)
    requirements: str = Field(min_length=5, max_length=4000)
    budget: Optional[float] = None
    timeline: Optional[str] = None
    contact_phone: Optional[str] = None


class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    booking_id: str
    client_id: str
    client_email: str
    client_name: str
    service_slug: str
    service_title: str
    package_id: Optional[str] = None
    package_name: Optional[str] = None
    booking_type: Literal["package", "quote"]
    project_title: str
    requirements: str
    budget: Optional[float] = None
    timeline: Optional[str] = None
    contact_phone: Optional[str] = None
    amount: Optional[float] = None  # set when package or admin quotes
    status: Literal["new", "quoted", "in_progress", "completed", "cancelled"] = "new"
    payment_status: Literal["unpaid", "pending", "paid", "refunded"] = "unpaid"
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BookingUpdate(BaseModel):
    status: Optional[Literal["new", "quoted", "in_progress", "completed", "cancelled"]] = None
    amount: Optional[float] = None
    admin_notes: Optional[str] = None


class CheckoutRequest(BaseModel):
    booking_id: str
    origin_url: str


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    subject: str = Field(min_length=1, max_length=140)
    message: str = Field(min_length=5, max_length=4000)


class Contact(BaseModel):
    model_config = ConfigDict(extra="ignore")
    contact_id: str
    name: str
    email: EmailStr
    subject: str
    message: str
    handled: bool = False
    created_at: datetime
