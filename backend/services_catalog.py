"""Static services + fixed pricing packages for LABOS Technologies."""

SERVICES = [
    {
        "slug": "website-building",
        "title": "Website Building",
        "tagline": "Bespoke marketing sites & landing pages that convert.",
        "description": (
            "From single-page portfolios to multi-page corporate sites, we design, "
            "build, and ship modern responsive websites with clean code and SEO baked in."
        ),
        "image": "https://images.unsplash.com/photo-1760548425425-e42e77fa38f1?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1OTN8MHwxfHNlYXJjaHwxfHx3ZWIlMjBkZXZlbG9wZXIlMjBjb2RpbmclMjBkYXJrJTIwbW9kZXJufGVufDB8fHx8MTc4NzU4MTgwN3ww&ixlib=rb-4.1.0&q=85",
        "packages": [
            {
                "package_id": "website_starter",
                "name": "Starter Site",
                "description": "Single-page site, up to 4 sections. Ideal for launches.",
                "amount": 15000.0,
                "highlights": ["3-page design", "Mobile ready", "Deployed in 10 days"],
            },
            {
                "package_id": "website_business",
                "name": "Business Site",
                "description": "Multi-page marketing site with CMS.",
                "amount": 25000.0,
                "highlights": ["Up to 6 pages", "Basic CMS", "SEO setup", "Analytics"],
            },
            {
                "package_id": "website_premium",
                "name": "Premium Site",
                "description": "Advanced marketing site with animations & integrations.",
                "amount": 35000.0,
                "highlights": ["Custom design", "Advanced animations", "3rd-party integrations", "Priority support"],
            },
        ],
    },
    {
        "slug": "site-maintenance",
        "title": "Site Maintenance",
        "tagline": "Keep your website fast, secure, and always up.",
        "description": (
            "Uptime monitoring, security patches, backups, content updates, and "
            "performance tuning — so you can focus on your business."
        ),
        "image": "https://images.pexels.com/photos/37730211/pexels-photo-37730211.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "packages": [
            {
                "package_id": "maint_basic_monthly",
                "name": "Basic Care (Monthly)",
                "description": "Essential maintenance, backups, and small tweaks.",
                "amount": 1000.0,
                "highlights": ["Weekly backups", "Security patches", "Up to 2 hrs edits/mo"],
            },
            {
                "package_id": "maint_pro_monthly",
                "name": "Pro Care (Monthly)",
                "description": "Advanced monitoring, performance & content ops.",
                "amount": 3000.0,
                "highlights": ["Daily backups", "24/7 uptime monitoring", "Up to 6 hrs edits/mo", "Priority response"],
            },
        ],
    },
    {
        "slug": "application-building",
        "title": "Application Building",
        "tagline": "Full-stack web apps engineered to scale.",
        "description": (
            "Custom SaaS dashboards, portals, and internal tools built with React, "
            "FastAPI, and Mongo. Auth, payments, and integrations included."
        ),
        "image": "https://images.pexels.com/photos/20694602/pexels-photo-20694602.png?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "packages": [
            {
                "package_id": "app_mvp",
                "name": "MVP Build",
                "description": "Full-stack MVP with auth, DB, and 3 core features.",
                "amount": 18000.0,
                "highlights": ["Auth + DB", "3 core features", "Deployed live", "Source code included"],
            },
            {
                "package_id": "app_pro",
                "name": "Pro Build",
                "description": "Production-grade app with payments & integrations.",
                "amount": 30000.0,
                "highlights": ["Payments (Razorpay)", "3rd-party integrations", "Admin dashboard", "8-week timeline"],
            },
        ],
    },
]


def get_service(slug: str) -> dict | None:
    for s in SERVICES:
        if s["slug"] == slug:
            return s
    return None


def get_package(service_slug: str, package_id: str) -> dict | None:
    svc = get_service(service_slug)
    if not svc:
        return None
    for p in svc["packages"]:
        if p["package_id"] == package_id:
            return p
    return None
