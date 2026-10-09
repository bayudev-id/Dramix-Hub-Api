"""Local JSON session store for iQIYI authentication."""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class SessionStore:
    """Manages iQIYI session persistence to local JSON file."""

    def __init__(self, file_path: str = "data/sessions.json"):
        """
        Initialize session store.
        
        Args:
            file_path: Path to JSON session file (default: data/sessions.json)
        """
        self.file_path = Path(file_path)
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Create session file with default structure if not exists."""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_file({"active_session": None})

    def _read_file(self) -> Dict[str, Any]:
        """Read and parse JSON session file."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {"active_session": None}
                return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupt session file: {e}")

    def _write_file(self, data: Dict[str, Any]) -> None:
        """Write data to JSON session file."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def read(self) -> Optional[Dict[str, Any]]:
        """
        Read active session from file.
        
        Returns:
            Session dict or None if no active session
        """
        data = self._read_file()
        return data.get("active_session")

    def save(self, session: Dict[str, Any]) -> None:
        """
        Save session to file with auto-updated timestamp.
        
        Args:
            session: Session dict to persist
            
        Raises:
            ValueError: If session missing mandatory fields
        """
        self.validate(session)
        
        # Auto-update timestamp
        session["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        # If created_at not present, set it
        if "created_at" not in session:
            session["created_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Ensure id present
        if "id" not in session:
            session["id"] = str(uuid.uuid4())
        
        data = {"active_session": session}
        self._write_file(data)

    @staticmethod
    def validate(session: Dict[str, Any]) -> None:
        """
        Validate session has mandatory fields.
        
        Args:
            session: Session dict to validate
            
        Raises:
            ValueError: If mandatory fields missing
        """
        mandatory_fields = ["auth_cookie", "device_id"]
        missing = [f for f in mandatory_fields if f not in session]
        
        if missing:
            raise ValueError(f"Session missing mandatory fields: {missing}")

    def clear(self) -> None:
        """Clear active session."""
        self._write_file({"active_session": None})
