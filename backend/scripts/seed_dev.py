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
        print(f"Created 2 users, 2 courses.")

        # --- Quests + Artifacts ---
        import json, hashlib, hmac

        quests_data = [
            # Course 1: Skynet Breaker
            (beginner_id, 1, "Dark Network Setup", "command_output",
             "ORACLE: Ghost, set up your dev environment. Run 'node --version && docker --version' and paste the output.",
             "Excellent. Your workstation is combat-ready.", ["setup", "cli"], [], "Developer's Badge", "Your workstation is armed."),
            (beginner_id, 2, "Signal Intercept", "url_check",
             "ORACLE: Create a REST API with a health endpoint. Deploy it and submit the URL. NEXUS must not detect downtime.",
             "API is live. NEXUS is blind to us.", ["nodejs", "api", "express"], [0], "API Access Key", "Your backend is operational."),
            (beginner_id, 3, "Enemy Map", "text_answer",
             "ORACLE: Design a database schema for tracking NEXUS activity. Describe your tables and relationships.",
             "Solid schema. We can track their movements now.", ["database", "sql", "schema"], [1], "Database Blueprint", "You can model the enemy's data."),
            (beginner_id, 4, "Command Center UI", "text_answer",
             "ORACLE: Build a dashboard frontend. Describe the components and layout you chose.",
             "The C&C Center has a face. Operators can use it.", ["react", "frontend", "ui"], [2], "Dashboard Schematics", "The interface is designed."),
            (beginner_id, 5, "Security Checkpoint", "quiz",
             "ORACLE: Quick check — What's the most secure way to store API keys? (A) Hardcode in source (B) .env file with .gitignore (C) Browser localStorage (D) URL parameters",
             "Correct. Never expose secrets.", ["security"], [], "Security Clearance", "You understand operational security."),
            (beginner_id, 6, "Final Strike", "url_check",
             "ORACLE: Deploy the full C&C Center to production. This is it, Ghost. Submit the live URL.",
             "MISSION COMPLETE. The C&C Center is operational. The resistance has a foothold.", ["deployment", "devops"], [3, 4], "Skynet Kill Switch", "You've completed the mission."),
            # Course 2: Pandemic Shield
            (advanced_id, 1, "Patient Zero", "text_answer",
             "DR. CHEN: Load the WHO dataset. Calculate total cases, deaths, and mortality rate. Submit as JSON.",
             "Good. Now we know the scale.", ["python", "pandas", "eda"], [], "Epidemiologist's Lens", "You see the data clearly."),
            (advanced_id, 2, "Prediction Engine", "text_answer",
             "DR. CHEN: Train a forecasting model. Report model type, R² score, and MAE.",
             "Your predictions are in. We can act now.", ["ml", "forecasting"], [6], "Prediction Engine Seal", "You built a crystal ball."),
            (advanced_id, 3, "Hotspot Detection", "text_answer",
             "DR. CHEN: Use clustering to identify 3-5 high-risk regions. Submit cluster details as JSON.",
             "Hotspots identified. Resources are being deployed.", ["clustering", "geospatial"], [7], "Hotspot Detector", "You know where danger lies."),
            (advanced_id, 4, "Model Critique", "text_answer",
             "DR. CHEN: What assumptions did your model make? Are they realistic? 3-4 sentences.",
             "A good analyst knows their weaknesses. Well done.", ["critical-thinking"], [], "Analytical Wisdom", "You question everything."),
            (advanced_id, 5, "ML Theory Quiz", "quiz",
             "DR. CHEN: What is overfitting? (A) Training too long (B) Too many features (C) Model memorizes training data (D) All of the above",
             "Correct. Overfitting is the silent killer.", ["ml-fundamentals"], [], "ML Theory Badge", "You know the pitfalls."),
            (advanced_id, 6, "WHO Briefing", "text_answer",
             "DR. CHEN: Write a one-page executive summary for WHO leadership. Include predictions, confidence intervals, and recommendations.",
             "She nods. 'This could save millions.' Well done, analyst.", ["communication", "leadership"], [8, 9], "WHO Advisor Certificate", "The world trusts your analysis."),
        ]

        quest_ids = []
        artifact_ids = []
        for course_id, order, title, eval_type, briefing, success, skills, req_idx, art_name, art_desc in quests_data:
            qid = uuid.uuid4()
            aid = uuid.uuid4()
            required = [str(artifact_ids[i]) for i in req_idx] if req_idx else []

            await db.execute(text("""
                INSERT INTO quests (id, course_id, sort_order, title, briefing, evaluation_type, skills,
                    success_response, evaluation_criteria, failure_states, max_hints, required_artifact_ids)
                VALUES (:id, :cid, :ord, :title, :brief, :etype, cast(:skills as jsonb), :success,
                    cast('{}' as jsonb), cast('[]' as jsonb), 3, cast(:req as jsonb))
            """), {"id": str(qid), "cid": str(course_id), "ord": order, "title": title, "brief": briefing,
                   "etype": eval_type, "skills": json.dumps(skills), "success": success,
                   "req": json.dumps(required)})

            await db.execute(text("""
                INSERT INTO artifact_definitions (id, course_id, quest_id, name, description)
                VALUES (:id, :cid, :qid, :name, :desc)
            """), {"id": str(aid), "cid": str(course_id), "qid": str(qid), "name": art_name, "desc": art_desc})

            quest_ids.append(qid)
            artifact_ids.append(aid)

        await db.commit()
        print(f"Created 12 quests + 12 artifacts")

        # --- Enrollments ---
        for cid in [beginner_id, advanced_id]:
            await db.execute(text("INSERT INTO enrollments (user_id, course_id) VALUES (:u, :c)"),
                             {"u": str(student_id), "c": str(cid)})
        await db.commit()

        # --- Quest States (mix of states for visual variety) ---
        states_config = [
            # Skynet: quest 0=COMPLETED, 1=IN_PROGRESS, 2=AVAILABLE, 3-5=LOCKED
            ("COMPLETED", 2, 1), ("IN_PROGRESS", 1, 0), ("AVAILABLE", 0, 0),
            ("LOCKED", 0, 0), ("LOCKED", 0, 0), ("LOCKED", 0, 0),
            # Pandemic: quest 6=COMPLETED, 7=FAILED_ATTEMPT, 8=AVAILABLE, 9-11=LOCKED
            ("COMPLETED", 1, 1), ("FAILED_ATTEMPT", 2, 0), ("AVAILABLE", 0, 0),
            ("LOCKED", 0, 0), ("LOCKED", 0, 0), ("LOCKED", 0, 0),
        ]
        for i, (state, attempts, hints) in enumerate(states_config):
            await db.execute(text("""
                INSERT INTO quest_states (id, user_id, quest_id, state, hints_used, attempts)
                VALUES (:id, :uid, :qid, :state, :hints, :attempts)
            """), {"id": str(uuid.uuid4()), "uid": str(student_id), "qid": str(quest_ids[i]),
                   "state": state, "hints": hints, "attempts": attempts})
        await db.commit()

        # --- User Artifacts (for completed quests) ---
        def sign(uid, aid):
            return hmac.new(settings.JWT_SECRET_KEY.encode(), f"{uid}:{aid}".encode(), hashlib.sha256).hexdigest()

        for idx in [0, 6]:  # quest 0 (Skynet) and quest 6 (Pandemic) are COMPLETED
            await db.execute(text("""
                INSERT INTO user_artifacts (id, user_id, artifact_definition_id, signature)
                VALUES (:id, :uid, :aid, :sig)
            """), {"id": str(uuid.uuid4()), "uid": str(student_id), "aid": str(artifact_ids[idx]),
                   "sig": sign(str(student_id), str(artifact_ids[idx]))})
        await db.commit()

        # --- Submissions ---
        subs = [
            (student_id, quest_ids[0], "command_output", {"command": "node --version", "output": "v20.11.0"}, "passed",
             json.dumps({"completeness": 9, "understanding": 8, "efficiency": 10, "creativity": 5})),
            (student_id, quest_ids[4], "quiz", {"selected_option_id": "B"}, "passed", None),
            (student_id, quest_ids[6], "text_answer", {"answer": '{"total_cases": 6900000, "mortality_rate": 0.099}'}, "passed",
             json.dumps({"completeness": 8, "understanding": 9, "efficiency": 7, "creativity": 6})),
            (student_id, quest_ids[7], "text_answer", {"answer": "I used linear regression"}, "failed", None),
        ]
        for uid, qid, etype, payload, status, quality in subs:
            await db.execute(text("""
                INSERT INTO submissions (id, user_id, quest_id, evaluation_type, payload, status, quality_scores)
                VALUES (:id, :uid, :qid, :etype, :payload, :status, :quality)
            """), {"id": str(uuid.uuid4()), "uid": str(uid), "qid": str(qid), "etype": etype,
                   "payload": json.dumps(payload), "status": status, "quality": quality})
        await db.commit()

        # --- Comms Log ---
        comms = [
            (student_id, beginner_id, quest_ids[0], "briefing", "ORACLE: Ghost — your dev environment must be ready in 2 hours. NEXUS is scanning."),
            (student_id, beginner_id, quest_ids[0], "evaluation", "ORACLE: Node.js confirmed. Docker running. You're combat-ready, Ghost."),
            (student_id, beginner_id, quest_ids[1], "hint", "ORACLE: Think about Express.js. What does app.listen() do?"),
            (student_id, beginner_id, None, "system", "Enrolled in Operation: Skynet Breaker."),
            (student_id, advanced_id, quest_ids[6], "briefing", "DR. CHEN: We have 72 hours. Load the data. Tell me what we're dealing with."),
            (student_id, advanced_id, quest_ids[6], "evaluation", "DR. CHEN: Good numbers. Now we need predictions."),
            (student_id, advanced_id, quest_ids[7], "evaluation", "DR. CHEN: Linear regression? For pandemic data? Think about time series patterns."),
        ]
        for uid, cid, qid, mtype, content in comms:
            await db.execute(text("""
                INSERT INTO comms_log (id, user_id, course_id, quest_id, message_type, content)
                VALUES (:id, :uid, :cid, :qid, :mtype, :content)
            """), {"id": str(uuid.uuid4()), "uid": str(uid), "cid": str(cid),
                   "qid": str(qid) if qid else None, "mtype": mtype, "content": content})
        await db.commit()

        print(f"\nFull seed complete!")
        print(f"Admin: {admin_id} | Student: {student_id}")
        print(f"Skynet: {beginner_id} | Pandemic: {advanced_id}")
        print(f"12 quests, 12 artifacts, 12 quest_states, 2 user_artifacts, 4 submissions, 7 comms_log")


if __name__ == "__main__":
    asyncio.run(seed())
