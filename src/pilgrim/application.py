from pilgrim.database import Database
from pilgrim.service.servicemanager import ServiceManager
from pilgrim.ui.ui import UIApp
from pathlib import Path
import os
import sys


class Application:
    def __init__(self):
        self.config_dir = self._ensure_config_directory()
        self.database = Database()
        session = self.database.session()
        session_manager = ServiceManager()
        session_manager.set_session(session)
        self.ui = UIApp(session_manager)

    def _ensure_config_directory(self) -> Path:
        """
        Ensures the ~/.pilgrim directory exists and has the correct permissions.
        Creates it if it doesn't exist.
        Returns the Path object for the config directory.
        """
        home = Path.home()
        config_dir = home / ".pilgrim"
        
        try:
            # Create directory if it doesn't exist
            config_dir.mkdir(exist_ok=True)
            
            # Ensure correct permissions (rwx for user only)
            os.chmod(config_dir, 0o700)
            
            # Create an empty .gitignore if it doesn't exist
            gitignore = config_dir / ".gitignore"
            if not gitignore.exists():
                gitignore.write_text("*\n")
            
            return config_dir
            
        except Exception as e:
            print(f"Error setting up Pilgrim configuration directory: {str(e)}", file=sys.stderr)
            sys.exit(1)

    def run(self):
        self.database.create()
        self.ui.run()

    def get_service_manager(self):
        session = self.database.session()
        session_manager = ServiceManager()
        session_manager.set_session(session)
        return session_manager
