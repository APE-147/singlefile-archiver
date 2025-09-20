"""Atomic key-value writing service."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.paths import get_project_dir


class StateWriter:
    """Atomic writer for application state."""
    
    def __init__(self, state_file: Optional[Path] = None):
        """Initialize the state writer."""
        if state_file is None:
            project_dir = get_project_dir()
            state_file = project_dir / "state.json"
        
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _read_state(self) -> Dict[str, Any]:
        """Read the current state from file."""
        if not self.state_file.exists():
            return {}
        
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _write_state(self, state: Dict[str, Any]) -> None:
        """Atomically write state to file."""
        # Write to temporary file first
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            dir=self.state_file.parent,
            delete=False
        ) as tmp_file:
            json.dump(state, tmp_file, indent=2)
            tmp_path = Path(tmp_file.name)
        
        # Atomic move to final location
        tmp_path.replace(self.state_file)
    
    def write(self, key: str, value: Any) -> None:
        """Write a key-value pair to the state file."""
        state = self._read_state()
        state[key] = value
        self._write_state(state)
    
    def read(self, key: str, default: Any = None) -> Any:
        """Read a value from the state file."""
        state = self._read_state()
        return state.get(key, default)
    
    def delete(self, key: str) -> bool:
        """Delete a key from the state file."""
        state = self._read_state()
        if key in state:
            del state[key]
            self._write_state(state)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all state."""
        self._write_state({})
    
    def get_all(self) -> Dict[str, Any]:
        """Get all state data."""
        return self._read_state()