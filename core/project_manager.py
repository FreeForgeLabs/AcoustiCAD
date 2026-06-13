import os
import uuid
import logging
from PySide6.QtCore import QObject, Signal
from datetime import datetime


class ProjectManager(QObject):
    """Central manager for project operations with integrated scale management"""
    # Signals
    project_loaded = Signal(object)  # Emitted when a project is loaded
    project_saved = Signal(object)  # Emitted when a project is saved
    project_changed = Signal()  # Emitted when project data is modified
    scale_changed = Signal()  # Emitted when scale factor changes

    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.logger = logging.getLogger(__name__)
        self.logger.debug("ProjectManager initialized")

        # Initialize scale manager (lazy import to avoid circular dependency)
        self.scale_manager = None
        # Callback will be added when scale manager is first accessed

        # Initialize thumbnail generator lazily to avoid circular imports
        self._thumbnail_generator = None

        # Current project state
        self.current_project_id = None
        self.current_project_data = None
        self.zones_modified = False
        self.project_modified = False

        # Flag to prevent recursive modification marking during scale-triggered operations
        self._updating_zones_from_scale = False

        # Reference to the zones view (will be set later)
        self.zones_view = None

    ### SCALE MANAGEMENT

    def get_scale_manager(self):
        """Get the scale manager for this project (lazy-loaded to avoid circular imports)"""
        if self.scale_manager is None:
            from core.scale_manager import ScaleManager
            self.scale_manager = ScaleManager(on_scale_changed_callback=self._on_scale_changed)
        return self.scale_manager

    def _on_scale_changed(self):
        """Handle scale changes from scale manager - CALCULATION OPERATION"""
        # Prevent recursive calls during zone area recalculation
        if self._updating_zones_from_scale:
            self.logger.debug("Ignoring scale change callback during zone area recalculation")
            return

        # Mark project as modified for scale changes
        self.project_modified = True
        self.scale_changed.emit()
        self.logger.debug("Scale changed, project marked as modified")

        # Recalculate all zone areas when scale changes - this is a CALCULATION, not USER MODIFICATION
        if self.zones_view and hasattr(self.zones_view, 'recalculate_zone_areas'):
            try:
                # Set flag to prevent recursive modification marking
                self._updating_zones_from_scale = True

                # This will emit zones_refreshed, not zones_modified
                self.zones_view.recalculate_zone_areas()
                self.logger.debug("Recalculated zone areas after scale change")

            except Exception as e:
                self.logger.error(f"Error recalculating zone areas after scale change: {e}")
            finally:
                # Always clear the flag
                self._updating_zones_from_scale = False

    ### PROJECT MANAGEMENT

    @property
    def thumbnail_generator(self):
        """
        Lazy-load the thumbnail generator to avoid circular imports
        Returns:
            ThumbnailGenerator: The thumbnail generator instance
        """
        if self._thumbnail_generator is None:
            # Import here to avoid circular imports
            from core.thumbnail_generator import ThumbnailGenerator
            self._thumbnail_generator = ThumbnailGenerator()
            self.logger.debug("ThumbnailGenerator initialized lazily")
        return self._thumbnail_generator

    def load_project(self, project_id):
        """Load a project - DATA LOADING OPERATION"""
        if project_id is None:
            self.logger.error("Cannot load project: project_id is None")
            return False

        try:
            # Load project data from storage
            project_data = self.storage.load_project(project_id)
            if not project_data:
                self.logger.error(f"Failed to load project {project_id}")
                return False

            # Store current project
            self.current_project_id = project_id
            self.current_project_data = project_data
            self.zones_modified = False
            self.project_modified = False

            # Load scale data - this is part of loading, not modification
            scale_data = project_data.get('scale_data', {})

            # Temporarily set flag to prevent scale change from triggering zone recalculation
            # during project loading (zones will be loaded separately)
            self._updating_zones_from_scale = True
            try:
                self.get_scale_manager().load_scale_data(scale_data)
            finally:
                self._updating_zones_from_scale = False

            self.logger.info(f"Project loaded: {project_id} - {project_data.get('name')}")

            # Emit signal that project was loaded
            self.project_loaded.emit(project_data)
            return True

        except Exception as e:
            self.logger.error(f"Error loading project: {e}", exc_info=True)
            return False

    def save_project(self):
        """Save the current project"""
        # Debug
        self.logger.debug(
            f"Saving project. zones_modified={self.zones_modified}, has zones_data={'zones_data' in self.current_project_data if self.current_project_data else False}")

        if not self.current_project_id or not self.current_project_data:
            self.logger.error("No project loaded to save")
            return False

        try:
            # Save scale data to project
            self.current_project_data['scale_data'] = self.get_scale_manager().get_scale_data()

            # If zones were modified, generate a new thumbnail
            if self.zones_modified and 'zones_data' in self.current_project_data:
                thumbnail = self.generate_thumbnail()
                if thumbnail:
                    self.current_project_data['preview_thumbnail'] = thumbnail

            # Update last modified timestamp
            self.current_project_data['last_modified'] = datetime.now().isoformat()

            # Save project data
            result = self.storage.save_project(self.current_project_data)
            if not result:
                self.logger.error("Failed to save project")
                return False

            # Reset modification flags
            self.zones_modified = False
            self.project_modified = False
            self.logger.info(f"Project saved: {self.current_project_id} - {self.current_project_data.get('name')}")

            # Emit signal that project was saved
            self.project_saved.emit(result)
            return True

        except Exception as e:
            self.logger.error(f"Error saving project: {e}", exc_info=True)
            return False

    def update_project_data(self, data, section=None):
        """Update project data - can be USER MODIFICATION or DATA LOADING"""
        if not self.current_project_data:
            self.logger.error("No project loaded to update")
            return False

        try:
            if section:
                # Update only a specific section of project data
                self.logger.debug(f"Updating project section '{section}' with data type: {type(data)}")

                # For zones_data, ensure it's a dictionary
                if section == 'zones_data' and not isinstance(data, dict):
                    self.logger.error(f"Invalid zones_data format: {type(data)}, must be dict")
                    return False

                self.current_project_data[section] = data
                self.logger.debug(f"Updated project section: {section}")

                # Mark zones as modified if that's what changed and we're not in a loading operation
                if section == 'zones_data' and not self._updating_zones_from_scale:
                    self.zones_modified = True
                    self.logger.debug("Marked zones as modified")
            else:
                # Update all project data
                if not isinstance(data, dict):
                    self.logger.error("Invalid project data: not a dictionary")
                    return False

                self.current_project_data.update(data)
                self.logger.debug("Updated multiple project sections")

            # Mark project as modified (unless we're in a scale update operation)
            if not self._updating_zones_from_scale:
                self.project_modified = True
                self.logger.debug("Marked project as modified")

                # Emit signal that project was changed
                self.project_changed.emit()

            return True

        except Exception as e:
            self.logger.error(f"Error updating project data: {e}", exc_info=True)
            return False

    def reset_modification_flags(self):
        """Reset all modification flags"""
        self.zones_modified = False
        self.project_modified = False
        self.logger.debug("Modification flags reset")

    def generate_thumbnail(self, width=300, height=200):
        """Generate thumbnail from the current zones view"""
        self.logger.debug(f"generate_thumbnail called - zones_view exists: {self.zones_view is not None}")

        if not self.zones_view:
            self.logger.debug("No zones view set, using placeholder")
            return self.thumbnail_generator.generate_placeholder(width, height)

        try:
            if hasattr(self.zones_view, 'zones') and self.zones_view.zones:
                self.logger.debug(f"Rendering {len(self.zones_view.zones)} zones")
            else:
                self.logger.debug("No zones found in zones_view")

            thumbnail = self.thumbnail_generator.generate_from_zones_view(self.zones_view, width, height)
            self.logger.debug(
                f"Thumbnail {'generated' if thumbnail else 'generation returned None'} ({width}x{height})"
            )
            return thumbnail

        except Exception as e:
            self.logger.error(f"Error generating thumbnail: {e}", exc_info=True)
            return self.thumbnail_generator.generate_placeholder(width, height)

    def set_zones_view(self, zones_view):
        """
        Set the zones view reference for thumbnail generation
        Args:
            zones_view: The zones view widget
        """
        try:
            self.zones_view = zones_view
            self.logger.debug("Zones view reference set")
        except Exception as e:
            # Safe error handling
            try:
                self.logger.error(f"Error setting zones view: {e}")
            except:
                print(f"Error setting zones view: {e}")

    def has_unsaved_changes(self):
        """Check if there are unsaved changes"""
        # Log the current state for debugging
        self.logger.debug(
            f"Checking for unsaved changes: zones_modified={self.zones_modified}, project_modified={self.project_modified}")

        return self.project_modified or self.zones_modified

    def set_zones_modified(self, modified=True):
        """
        Mark zones data as modified - USER MODIFICATION ONLY
        Args:
            modified (bool): Whether the zones are modified
        """
        # Don't process zone modifications if we're updating from a scale change
        if self._updating_zones_from_scale and modified:
            self.logger.debug("Ignoring zone modification during scale-triggered zone area recalculation")
            return

        old_state = self.zones_modified
        self.zones_modified = modified

        if modified and not old_state:
            self.project_modified = True

            # Thumbnail generation removed - will be done during save_project() instead
            # This prevents recursion issues during zone modifications

            self.project_changed.emit()
            self.logger.debug("Zones marked as modified by user action")

    def get_current_project_id(self):
        """
        Get the current project ID

        Returns:
            The current project ID or None if no project is loaded
        """
        return self.current_project_id

    def get_current_project_data(self):
        """Get the current project data"""
        return self.current_project_data

    def create_new_project(self, name, description="", **kwargs):
        """
        Create a new project with basic metadata
        Args:
            name (str): The name of the new project
            description (str, optional): Description of the project
            **kwargs: Additional project properties
        Returns:
            dict or None: The created project data or None if failed
        """
        if not name:
            self.logger.error("Project name is required")
            return None

        try:
            # Create new project data. UUID4 — wall-clock IDs (int(time.time()))
            # collide on rapid creation and leak creation time. See classroom lesson:
            # software-patterns/2026-05-26-wall-clock-as-unique-id.md
            project_id = uuid.uuid4().hex
            now = datetime.now().isoformat()

            project_data = {
                'id': project_id,
                'name': name,
                'description': description,
                'created_at': now,
                'last_modified': now,
                'app_version': getattr(self.storage, 'VERSION', '0.1.0'),  # Get version from storage if available
                'scale_data': self.get_scale_manager().get_scale_data(),
                **kwargs
            }

            # Save the new project
            result = self.storage.save_project(project_data)
            if not result:
                self.logger.error("Failed to create new project")
                return None

            # Set as current project
            self.current_project_id = project_id
            self.current_project_data = result
            self.zones_modified = False
            self.project_modified = False
            self.logger.info(f"New project created: {project_id} - {name}")

            # Add to recent projects
            self.storage.add_to_recent_projects(project_id, name)

            # Emit signal
            self.project_loaded.emit(result)
            return result

        except Exception as e:
            self.logger.error(f"Error creating new project: {e}", exc_info=True)
            return None

    def get_project_history(self):
        """
        Get the backup history for the current project
        Returns:
            list or None: List of backup information or None if no project is loaded
        """
        if not self.current_project_id:
            self.logger.warning("Cannot get project history: no project loaded")
            return None

        try:
            # Check if storage has the get_project_backups method
            if hasattr(self.storage, 'get_project_backups'):
                return self.storage.get_project_backups(self.current_project_id)
            else:
                self.logger.warning("Storage does not support get_project_backups")
                return []

        except Exception as e:
            self.logger.error(f"Error getting project history: {e}", exc_info=True)
            return []

    def restore_backup(self, backup_path):
        """
        Restore a project from a backup - DATA LOADING OPERATION
        Args:
            backup_path (str): Path to the backup file
        Returns:
            bool: True if successful, False otherwise
        """
        if not backup_path or not os.path.exists(backup_path):
            self.logger.error(f"Cannot restore backup: invalid path {backup_path}")
            return False

        try:
            # Check if storage has the restore_backup method
            if hasattr(self.storage, 'restore_backup'):
                result = self.storage.restore_backup(backup_path)

                if result:
                    # Update current project data if it's the same project
                    if result.get('id') == self.current_project_id:
                        self.current_project_data = result
                        self.zones_modified = False
                        self.project_modified = False

                        # Load scale data from restored project - this is loading, not modification
                        scale_data = result.get('scale_data', {})

                        # Set flag to prevent scale loading from triggering modifications
                        self._updating_zones_from_scale = True
                        try:
                            self.get_scale_manager().load_scale_data(scale_data)
                        finally:
                            self._updating_zones_from_scale = False

                        # Emit signals
                        self.project_loaded.emit(result)

                    self.logger.info(f"Project restored from backup: {backup_path}")
                    return True
                else:
                    self.logger.error(f"Failed to restore backup: {backup_path}")
                    return False
            else:
                self.logger.warning("Storage does not support restore_backup")
                return False

        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}", exc_info=True)
            return False