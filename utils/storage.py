import os
import json
import logging
import shutil
import tempfile
import platform
from pathlib import Path
from datetime import datetime

import __version__ as _version_module

# Single source of truth for the version string — read from VERSION file via __version__.py
_APP_VERSION = _version_module.__version__
_APP_NAME = _version_module.APP_NAME
_LEGACY_APP_NAME = _version_module.LEGACY_APP_NAME


def _platform_app_dir(app_name: str) -> str:
    """Per-OS user data directory for a given app name."""
    if platform.system() == "Windows":
        return os.path.join(os.environ.get("APPDATA", str(Path.home())), app_name)
    elif platform.system() == "Darwin":  # macOS
        return os.path.join(str(Path.home()), "Library", "Application Support", app_name)
    else:  # Linux and others
        return os.path.join(str(Path.home()), f".{app_name}")


class Storage:
    """Handle data storage for the application"""
    # App version stamped into saved settings/projects.
    # Read once from the VERSION-file-backed __version__ module — no duplicated string.
    VERSION = _APP_VERSION

    def __init__(self):
        """Initialize storage with app directory"""
        self.logger = logging.getLogger(__name__)

        # Compute current + legacy paths so we can do a one-shot rename migration.
        base_dir = _platform_app_dir(_APP_NAME)
        legacy_dir = _platform_app_dir(_LEGACY_APP_NAME)

        # One-shot rename migration. Runs every startup but is a no-op once the new
        # dir exists — the dir's existence is the sentinel (no flag file needed).
        # Idempotent by construction. Only fires when legacy has content AND new is absent.
        if os.path.isdir(legacy_dir) and not os.path.exists(base_dir):
            try:
                os.rename(legacy_dir, base_dir)
                self.logger.info(
                    f"Migrated user data: {legacy_dir} → {base_dir} "
                    f"(one-shot rename from {_LEGACY_APP_NAME} → {_APP_NAME})"
                )
            except OSError as e:
                # Fall through to fresh-dir creation — user loses prior data but the app still boots
                self.logger.warning(
                    f"Could not migrate legacy data dir ({e}); creating fresh {base_dir}"
                )

        # Reports dir lives in ~/Documents/ (user-visible output, not app-internal data).
        # One-shot rename migration: same shape as the settings-dir migration above —
        # if the legacy "AudioSystem Reports" dir exists and the new one doesn't, rename it.
        # The new dir's existence is the sentinel; idempotent by construction.
        documents_dir = os.path.join(str(Path.home()), "Documents")
        reports_dir = os.path.join(documents_dir, "AcoustiCAD Reports")
        legacy_reports_dir = os.path.join(documents_dir, "AudioSystem Reports")
        if os.path.isdir(legacy_reports_dir) and not os.path.exists(reports_dir):
            try:
                os.rename(legacy_reports_dir, reports_dir)
                self.logger.info(
                    f"Migrated reports dir: {legacy_reports_dir} → {reports_dir}"
                )
            except OSError as e:
                self.logger.warning(
                    f"Could not migrate legacy reports dir ({e}); will create {reports_dir}"
                )

        # Set all paths first
        self.app_dir = base_dir
        self.projects_dir = os.path.join(self.app_dir, "projects")
        self.backups_dir = os.path.join(self.app_dir, "backups")
        self.speaker_profiles_dir = os.path.join(self.app_dir, "speaker_profiles")
        self.reports_dir = reports_dir
        self.settings_file = os.path.join(self.app_dir, "settings.json")

        # Then create directories
        self._setup_directories()

    #
    def _setup_directories(self):
        """Setup storage directories with proper error handling"""
        try:
            for directory in [self.app_dir, self.projects_dir, self.backups_dir,
                              self.speaker_profiles_dir, self.reports_dir]:
                os.makedirs(directory, exist_ok=True)

            self.logger.info(f"Storage initialized at: {self.app_dir}")

        except (OSError, PermissionError) as e:
            self.logger.error(f"Failed to create storage directories: {e}")
            raise RuntimeError(f"Cannot initialize storage: {e}")

    def get_project_assets_dir(self, project_id):
        """Get (and create) the assets directory for a specific project."""
        assets_dir = os.path.join(self.projects_dir, f"{project_id}_assets")
        os.makedirs(assets_dir, exist_ok=True)
        return assets_dir

    def copy_background_for_project(self, project_id, source_path):
        """Copy a background file into the project's assets directory.

        Returns the path of the copy on success, or None on failure.
        If source_path is already inside the assets directory, returns it unchanged.
        """
        try:
            if not source_path or not os.path.exists(source_path):
                return None

            assets_dir = self.get_project_assets_dir(project_id)
            ext = os.path.splitext(source_path)[1].lower() or ".png"
            dest_path = os.path.join(assets_dir, f"background{ext}")

            # Skip copy if already the same file
            if os.path.abspath(source_path) == os.path.abspath(dest_path):
                return dest_path

            shutil.copy2(source_path, dest_path)
            self.logger.info(f"Copied background to project assets: {dest_path}")
            return dest_path

        except Exception as e:
            self.logger.error(f"Error copying background for project {project_id}: {e}")
            return None

    def get_speaker_profiles_dir(self):
        """Get the path to the speaker profiles directory"""
        return self.speaker_profiles_dir

    def get_reports_dir(self):
        """Get the path to the reports directory"""
        return self.reports_dir

    def _atomic_write_json(self, file_path, data):
        """
        Write JSON data atomically to avoid corruption
        Args:
            file_path (str): Path to the destination file
            data (dict): Data to be written
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a temporary file in the same directory
            temp_dir = os.path.dirname(file_path)
            with tempfile.NamedTemporaryFile(mode='w', dir=temp_dir, delete=False) as temp_file:
                temp_path = temp_file.name
                # Write data to temp file
                json.dump(data, temp_file, indent=2)

            # Replace the original file (atomic operation)
            shutil.move(temp_path, file_path)
            self.logger.debug(f"Atomic write successful: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error in atomic write to {file_path}: {e}", exc_info=True)
            # Attempt to clean up the temp file if it still exists
            try:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass
            return False

    def _create_backup(self, project_id):
        """
        Create a backup of a project
        Args:
            project_id: The ID of the project to backup
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            source_path = os.path.join(self.projects_dir, f"{project_id}.json")
            if not os.path.exists(source_path):
                self.logger.warning(f"Cannot backup - project file doesn't exist: {source_path}")
                return False

            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{project_id}_{timestamp}.json"
            backup_path = os.path.join(self.backups_dir, backup_filename)

            # Copy the file
            shutil.copy2(source_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")

            # Clean up old backups (keep only last 5 per project)
            self._cleanup_old_backups(project_id)
            return True
        except Exception as e:
            self.logger.error(f"Error creating backup for project {project_id}: {e}", exc_info=True)
            return False

    def _cleanup_old_backups(self, project_id):
        """
        Keep only the 5 most recent backups for a project
        Args:
            project_id: The ID of the project
        """
        try:
            # Find all backups for this project
            backup_files = []
            for filename in os.listdir(self.backups_dir):
                if filename.startswith(f"{project_id}_") and filename.endswith(".json"):
                    backup_path = os.path.join(self.backups_dir, filename)
                    backup_files.append((backup_path, os.path.getmtime(backup_path)))

            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)

            # Delete all but the 5 newest
            if len(backup_files) > 5:
                for path, _ in backup_files[5:]:
                    os.remove(path)
                    self.logger.debug(f"Removed old backup: {path}")
        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}", exc_info=True)

    def load_settings(self):
        """
        Load application settings
        Returns:
            dict: The settings or default settings if the file doesn't exist
        """
        try:
            default_settings = {
                "recent_projects": [],
                "app_version": self.VERSION,
                "window_geometry": None,
                "window_state": None
            }

            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.logger.debug(f"Settings loaded with keys: {list(settings.keys())}")

                    # Update with any missing default keys (for backward compatibility)
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value

                    # Update version
                    settings["app_version"] = self.VERSION
                    return settings
            else:
                self.logger.info("Settings file not found, using defaults")
                return default_settings
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}", exc_info=True)
            return {"recent_projects": [], "app_version": self.VERSION}

    def save_settings(self, settings):
        """
        Save application settings
        Args:
            settings (dict): Settings to save
        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(settings, dict):
            self.logger.error("Invalid settings format: not a dictionary")
            return False

        try:
            # Ensure app_version is set
            settings["app_version"] = self.VERSION
            return self._atomic_write_json(self.settings_file, settings)
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}", exc_info=True)
            return False

    def get_all_projects(self):
        """
        Get list of all projects
        Returns:
            list: List of project data dictionaries
        """
        projects = []
        try:
            if not os.path.exists(self.projects_dir):
                self.logger.warning(f"Projects directory doesn't exist: {self.projects_dir}")
                return []

            for filename in os.listdir(self.projects_dir):
                if filename.endswith('.json'):
                    try:
                        project_path = os.path.join(self.projects_dir, filename)
                        with open(project_path, 'r') as f:
                            project_data = json.load(f)

                            # Validate minimal project structure
                            if not isinstance(project_data, dict):
                                self.logger.warning(f"Skipping invalid project: {filename} (not a dict)")
                                continue

                            if 'id' not in project_data:
                                project_id = os.path.splitext(filename)[0]
                                try:
                                    project_data['id'] = int(project_id)
                                    self.logger.warning(f"Fixed missing project ID for: {filename}")
                                except ValueError:
                                    self.logger.warning(f"Skipping project with invalid ID: {filename}")
                                    continue

                            if 'name' not in project_data:
                                project_data['name'] = f"Unnamed Project {project_data['id']}"
                                self.logger.warning(f"Added missing name for project: {filename}")

                            projects.append(project_data)
                    except json.JSONDecodeError:
                        self.logger.error(f"Invalid JSON in project file: {filename}")
                    except Exception as e:
                        self.logger.error(f"Error loading project {filename}: {e}", exc_info=True)

            self.logger.info(f"Loaded {len(projects)} projects")
            return projects
        except Exception as e:
            self.logger.error(f"Error getting projects: {e}", exc_info=True)
            return []

    def load_project(self, project_id):
        """
        Load a project by ID
        Args:
            project_id: The ID of the project to load
        Returns:
            dict: The project data or None if not found
        """
        if project_id is None:
            self.logger.error("Cannot load project: project_id is None")
            return None

        try:
            project_path = os.path.join(self.projects_dir, f"{project_id}.json")
            self.logger.debug(f"Attempting to load project from: {project_path}")

            if os.path.exists(project_path):
                self.logger.debug(f"Project file exists: {project_path}")
                with open(project_path, 'r') as f:
                    project_data = json.load(f)

                    # Add version info if not present
                    if 'app_version' not in project_data:
                        project_data['app_version'] = self.VERSION

                    self.logger.debug(f"Project loaded successfully with keys: {list(project_data.keys())}")
                    return project_data
            else:
                self.logger.warning(f"Project file does not exist: {project_path}")
                # List all files in the directory for debugging
                if os.path.exists(self.projects_dir):
                    self.logger.debug(f"Files in projects directory: {os.listdir(self.projects_dir)}")
                return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in project file {project_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading project {project_id}: {e}", exc_info=True)
            return None

    def save_project(self, project_data):
        """
        Save a project
        Args:
            project_data (dict): Project data to save
        Returns:
            dict: The saved project data or None if failed
        """
        if not isinstance(project_data, dict):
            self.logger.error("Invalid project data format: not a dictionary")
            return None

        try:
            project_id = project_data.get('id')
            if not project_id:
                self.logger.error("Project ID is required")
                return None

            # Data validation
            required_fields = ['id', 'name']
            for field in required_fields:
                if field not in project_data:
                    self.logger.error(f"Missing required project field: {field}")
                    return None

            # Add or update version info
            project_data['app_version'] = self.VERSION

            # Update modification timestamp
            project_data['last_modified'] = datetime.now().isoformat()

            # Backup the existing project if it exists
            project_path = os.path.join(self.projects_dir, f"{project_id}.json")
            if os.path.exists(project_path):
                self._create_backup(project_id)

            # Save project with atomic write
            if self._atomic_write_json(project_path, project_data):
                self.logger.info(f"Project saved successfully: {project_id}")
                return project_data
            return None
        except Exception as e:
            self.logger.error(f"Error saving project: {e}", exc_info=True)
            return None

    def delete_project(self, project_id):
        """
        Delete a project by ID
        Args:
            project_id: The ID of the project to delete
        Returns:
            bool: True if successful, False otherwise
        """
        if project_id is None:
            self.logger.error("Cannot delete project: project_id is None")
            return False

        try:
            project_path = os.path.join(self.projects_dir, f"{project_id}.json")
            if os.path.exists(project_path):
                # Create a final backup before deletion
                self._create_backup(project_id)

                # Delete the file
                os.remove(project_path)

                # Remove from recent projects
                settings = self.load_settings()
                settings["recent_projects"] = [p for p in settings.get("recent_projects", [])
                                               if p.get("id") != project_id]
                self.save_settings(settings)

                self.logger.info(f"Project deleted: {project_id}")
                return True
            else:
                self.logger.warning(f"Cannot delete, project does not exist: {project_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error deleting project {project_id}: {e}", exc_info=True)
            return False

    def add_to_recent_projects(self, project_id, project_name):
        """
        Add a project to the recent projects list
        Args:
            project_id: The ID of the project
            project_name (str): The name of the project
        Returns:
            bool: True if successful, False otherwise
        """
        if project_id is None:
            self.logger.error("Cannot add to recent projects: project_id is None")
            return False

        if not project_name:
            self.logger.warning(f"Empty project name for ID {project_id}, using 'Unnamed Project'")
            project_name = f"Unnamed Project {project_id}"

        try:
            settings = self.load_settings()

            # Remove if already in list
            settings["recent_projects"] = [p for p in settings.get("recent_projects", [])
                                           if p.get("id") != project_id]

            # Add to front of list
            settings["recent_projects"].insert(0, {
                "id": project_id,
                "name": project_name,
                "timestamp": datetime.now().isoformat()
            })

            # Keep only the 10 most recent
            settings["recent_projects"] = settings["recent_projects"][:10]

            # Save settings
            if self.save_settings(settings):
                self.logger.debug(f"Added project to recent list: {project_id} - {project_name}")
                return True
            else:
                self.logger.error(f"Failed to save settings when adding project to recent list")
                return False
        except Exception as e:
            self.logger.error(f"Error adding to recent projects: {e}", exc_info=True)
            return False

    def get_project_backups(self, project_id):
        """
        Get list of available backups for a project
        Args:
            project_id: The ID of the project
        Returns:
            list: List of backup information dictionaries with path and timestamp
        """
        backups = []
        try:
            for filename in os.listdir(self.backups_dir):
                if filename.startswith(f"{project_id}_") and filename.endswith(".json"):
                    backup_path = os.path.join(self.backups_dir, filename)

                    # Extract timestamp from filename
                    timestamp = filename.replace(f"{project_id}_", "").replace(".json", "")

                    # Convert to readable format if it's in the expected format
                    try:
                        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                        readable_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        readable_time = timestamp

                    backups.append({
                        "path": backup_path,
                        "timestamp": timestamp,
                        "readable_time": readable_time,
                        "modified": os.path.getmtime(backup_path)
                    })

            # Sort by modification time (newest first)
            backups.sort(key=lambda x: x["modified"], reverse=True)
            self.logger.debug(f"Found {len(backups)} backups for project {project_id}")
            return backups
        except Exception as e:
            self.logger.error(f"Error getting project backups: {e}", exc_info=True)
            return []

    def restore_backup(self, backup_path):
        """
        Restore a project from a backup file
        Args:
            backup_path (str): Path to the backup file
        Returns:
            dict: The restored project data or None if failed
        """
        if not os.path.exists(backup_path):
            self.logger.error(f"Backup file does not exist: {backup_path}")
            return None

        try:
            # Load backup data
            with open(backup_path, 'r') as f:
                project_data = json.load(f)

            if 'id' not in project_data:
                self.logger.error(f"Invalid backup file, missing project ID: {backup_path}")
                return None

            # Save as current project
            result = self.save_project(project_data)
            if result:
                self.logger.info(f"Project restored from backup: {backup_path}")
            return result
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in backup file: {backup_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}", exc_info=True)
            return None