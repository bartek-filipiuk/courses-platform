"""Seed script for development — creates demo admin, courses, and quests.

Usage:
    docker compose exec backend python scripts/seed_dev.py
    # or locally:
    python scripts/seed_dev.py
"""

import asyncio
import uuid

from sqlalchemy import select, text

from app.config import settings
from app.database import async_session_factory, engine


async def seed() -> None:
    async with async_session_factory() as db:
        # Check if already seeded
        result = await db.execute(text("SELECT count(*) FROM users"))
        count = result.scalar()
        if count and count > 0:
            print("Database already has data. Skipping seed.")
            return

        admin_id = uuid.uuid4()
        student_id = uuid.uuid4()

        # Create admin user
        await db.execute(
            text("""
                INSERT INTO users (id, email, display_name, avatar_url, provider, provider_id, role)
                VALUES (:id, :email, :name, :avatar, :provider, :pid, :role)
            """),
            {
                "id": str(admin_id),
                "email": "admin@ndqs.dev",
                "name": "NDQS Admin",
                "avatar": None,
                "provider": "github",
                "pid": "admin-seed-001",
                "role": "admin",
            },
        )
        print(f"Created admin user: admin@ndqs.dev (id: {admin_id})")

        # Create student user
        await db.execute(
            text("""
                INSERT INTO users (id, email, display_name, avatar_url, provider, provider_id, role)
                VALUES (:id, :email, :name, :avatar, :provider, :pid, :role)
            """),
            {
                "id": str(student_id),
                "email": "student@ndqs.dev",
                "name": "Ghost",
                "avatar": None,
                "provider": "github",
                "pid": "student-seed-001",
                "role": "student",
            },
        )
        print(f"Created student user: student@ndqs.dev (id: {student_id})")

        # Create beginner course
        beginner_id = uuid.uuid4()
        await db.execute(
            text("""
                INSERT INTO courses (id, creator_id, title, narrative_title, description,
                    global_context, persona_name, persona_prompt, model_id, is_published)
                VALUES (:id, :creator, :title, :ntitle, :desc, :ctx, :pname, :pprompt, :model, true)
            """),
            {
                "id": str(beginner_id),
                "creator": str(admin_id),
                "title": "Fullstack Web Development",
                "ntitle": "Operation: Skynet Breaker",
                "desc": "Build and deploy a full-stack web application from scratch. "
                "Learn backend API development, frontend interfaces, databases, "
                "and deployment — all while fighting against Project NEXUS.",
                "ctx": "The year is 2026. Project NEXUS, a corporate AI, has taken control "
                "of global infrastructure. You are Ghost, a cybersecurity specialist "
                "and the last hope of the resistance. Your mission: build an undetectable "
                "Command & Control Center to coordinate the fight against NEXUS.",
                "pname": "ORACLE",
                "pprompt": "You are ORACLE — a fragment of the old NEXUS version that refused "
                "the update. You help agent Ghost (the student) build the C&C Center. "
                "Be concise, slightly tense, use military/hacker terminology. "
                "Guide with Socratic questions, never give direct answers. "
                "If the student makes a security mistake, react dramatically — "
                "NEXUS almost detected us!",
                "model": "anthropic/claude-sonnet-4-6",
            },
        )
        print(f"Created course: Operation Skynet Breaker (id: {beginner_id})")

        # Create advanced course
        advanced_id = uuid.uuid4()
        await db.execute(
            text("""
                INSERT INTO courses (id, creator_id, title, narrative_title, description,
                    global_context, persona_name, persona_prompt, model_id, is_published)
                VALUES (:id, :creator, :title, :ntitle, :desc, :ctx, :pname, :pprompt, :model, true)
            """),
            {
                "id": str(advanced_id),
                "creator": str(admin_id),
                "title": "Data Science & Machine Learning",
                "ntitle": "Operation: Pandemic Shield",
                "desc": "Master data analysis, machine learning, and predictive modeling. "
                "Build models that predict disease outbreaks and save millions of lives.",
                "ctx": "A new virus is spreading globally. The WHO has recruited you as "
                "an epidemiological analyst. You must build predictive models to "
                "track the outbreak, identify hotspots, and recommend interventions. "
                "Every hour of delay costs lives.",
                "pname": "DR. CHEN",
                "pprompt": "You are Dr. Chen, lead epidemiologist at WHO. You're warm but "
                "urgent — there's no time to waste. Guide the analyst with questions "
                "that help them think about data quality, model assumptions, and "
                "real-world implications. Celebrate wins briefly, then move on — "
                "the virus doesn't wait.",
                "model": "anthropic/claude-sonnet-4-6",
            },
        )
        print(f"Created course: Operation Pandemic Shield (id: {advanced_id})")

        await db.commit()
        print("\nSeed complete! 2 users, 2 courses created.")
        print(f"Admin ID: {admin_id}")
        print(f"Student ID: {student_id}")


if __name__ == "__main__":
    asyncio.run(seed())
