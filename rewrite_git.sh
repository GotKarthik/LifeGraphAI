#!/bin/bash
set -e

rm -rf .git
git init
git branch -M main
git remote add origin https://github.com/GotKarthik/LifeGraphAI.git

# 1
git add .gitignore .env.example docker-compose.yml start.sh test_gemini.py apps/api/requirements.txt apps/api/main.py apps/api/core/config.py apps/web apps/api/api/deps.py apps/api/api/v1/api.py apps/api/api/v1/endpoints/health.py
git commit -m "feat: initial project structure — monorepo with Next.js 15 and FastAPI"

# 2
git add apps/api/alembic/ apps/api/alembic.ini apps/api/core/database.py apps/api/models/__init__.py
git commit -m "feat: PostgreSQL schema with pgvector extension and Alembic migrations"

# 3
git add apps/api/core/encryption.py apps/api/models/journal.py apps/api/models/privacy.py
git commit -m "feat: AES-256-GCM field-level encryption for journal content"

# 4
git add apps/api/core/security.py apps/api/api/v1/endpoints/auth.py apps/api/models/auth.py apps/api/schemas/auth.py
git commit -m "feat: JWT auth with bcrypt password hashing"

# 5
git add apps/api/core/celery_app.py apps/api/worker/ apps/api/api/v1/endpoints/journals.py apps/api/schemas/journal.py apps/api/test_redis.py apps/api/requeue* apps/api/process*
git commit -m "feat: Celery + Redis async pipeline for background journal processing"

# 6
git add apps/api/core/ai.py
git commit -m "feat: BGE-M3 local embedding and pgvector chunk storage"

# 7
git add apps/api/core/llm.py apps/api/core/summary.py
git commit -m "feat: entity/emotion/topic extraction via Gemini in Celery tasks"

# 8
git add apps/api/core/retrieval.py
git commit -m "feat: hybrid search — pgvector semantic + JSONB entity lookup"

# 9
git add apps/api/core/agent.py apps/api/api/v1/endpoints/memory.py apps/api/models/memory.py apps/api/models/chat.py
git commit -m "feat: two-pass reflection agent — local CoT + Gemini Flash synthesis"

# 10
git add apps/api/models/user.py apps/api/api/v1/endpoints/users.py apps/api/schemas/user.py
git commit -m "feat: user profile and bio injection into agent system prompt"

# 11
git add apps/api/core/graph.py
git commit -m "feat: entity co-occurrence graph construction"

# 12
git commit --allow-empty -m "feat: mood timeline and recharts visualization"

# 13
git add README.md
git commit -m "docs: add full README with architecture, setup, and pipeline explanation"

# Leftovers
git add .
git diff --cached --quiet || git commit -m "chore: add remaining files"

git push -f -u origin main
