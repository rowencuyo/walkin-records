"""
JSON-based autosave draft storage.
Drafts are stored as JSON files in data/drafts/ and are completely
isolated from the main database records.
"""
import json
from pathlib import Path
from app.database import DRAFTS_DIR
from app.utils.logger import get_logger
from core.audit_logger import log_action

logger = get_logger(__name__)


class DraftService:
    """Manages autosave drafts for record forms."""

    def save_draft(self, draft_key: str, form_data: dict) -> bool:
        """Save form data as a JSON draft. Returns True on success."""
        try:
            DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
            path = DRAFTS_DIR / f"{draft_key}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(form_data, f, ensure_ascii=False, indent=2)
            log_action("admin", "SAVE_DRAFT", "drafts", None,
                       f"Saved draft: {draft_key}")
            return True
        except Exception as e:
            logger.error("Failed to save draft '%s': %s", draft_key, e)
            return False

    def load_draft(self, draft_key: str) -> dict | None:
        """Load a draft by key. Returns dict or None if not found."""
        path = DRAFTS_DIR / f"{draft_key}.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load draft '%s': %s", draft_key, e)
            return None

    def delete_draft(self, draft_key: str) -> bool:
        """Delete a draft file. Returns True if deleted."""
        path = DRAFTS_DIR / f"{draft_key}.json"
        try:
            if path.exists():
                path.unlink()
                log_action("admin", "DELETE_DRAFT", "drafts", None,
                           f"Deleted draft: {draft_key}")
                return True
        except Exception as e:
            logger.error("Failed to delete draft '%s': %s", draft_key, e)
        return False

    def has_draft(self, draft_key: str) -> bool:
        """Check if a draft exists."""
        return (DRAFTS_DIR / f"{draft_key}.json").exists()
