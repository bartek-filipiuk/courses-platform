"""Ensure exactly one admin user exists (idempotent) — used at prod boot before
seed_shadow_course.py, which needs an admin as the course creator. Unlike
seed_dev.py this creates NO demo courses/students, so it is safe to run on every
boot of the production container.

Usage:
    python scripts/ensure_admin.py
"""

import asyncio
import uuid

from sqlalchemy import text

from app.database import async_session_factory


async def ensure_admin() -> None:
    async with async_session_factory() as db:
        result = await db.execute(text("SELECT id FROM users WHERE role = 'admin' LIMIT 1"))
        if result.scalar():
            print("Admin user already exists. Skipping.")
            return
        admin_id = uuid.uuid4()
        await db.execute(
            text(
                """
                INSERT INTO users (id, email, display_name, avatar_url, provider, provider_id, role)
                VALUES (:id, :email, :name, NULL, :provider, :pid, 'admin')
                """
            ),
            {
                "id": str(admin_id),
                "email": "admin@devince.dev",
                "name": "NDQS Admin",
                "provider": "system",
                "pid": "ndqs-admin",
            },
        )
        await db.commit()
        print(f"Created admin user (id: {admin_id})")


if __name__ == "__main__":
    asyncio.run(ensure_admin())
