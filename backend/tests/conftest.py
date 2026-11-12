"""Shared pytest setup: dummy env so imports and lifespan need no real secrets."""

import os

os.environ.setdefault("OPENAI_API_KEY", "ci-dummy-openai-key")
os.environ.setdefault("AUTH_DISABLED", "true")
