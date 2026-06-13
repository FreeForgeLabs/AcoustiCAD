import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ConfigManager:
    """Enhanced configuration manager with validation and defaults"""

    DEFAULT_CONFIG = {
        "app": {
            "name": "AcoustiCAD",
            "version": "1.0.0",
            "organization": "Audio System Design",
            "domain": "freeforgelabs.com"
        },
        "ui": {
            "dev_mode_enabled": False,
            "theme": "light",
            "language": "en",
            "window": {
                "default_width": 1200,
                "default_height": 800,
                "min_width": 1000,
                "min_height": 700,
                "remember_size": True,
                "remember_position": True
            },
            "grid": {
                "default_size": 10,
                "enabled_by_default": True,
                "snap_enabled_by_default": True,
                "show_major_lines": True,
                "major_line_interval": 5
            },
            "drawing": {
                "line_color": "#0080FF",
                "line_width": 2,
                "point_size": 6,
                "selection_color": "#FF8C00"
            }
        },
        "dev": {
            "log_level": "INFO",
            "show_debug_console": False,
            "show_performance_metrics": False,
            "auto_save_interval": 300,  # seconds
            "backup_count": 5
        },
        "paths": {
            "speaker_profiles": "speaker_profiles",
            "projects": "projects",
            "exports": "exports",
            "logs": "logs",
            "backups": "backups",
            "temp": "temp"
        },
        "speaker_defaults": {
            "sensitivity": 89.0,
            "power_taps": [5, 10, 15, 30],
            "impedance": 8.0,
            "frequency_range": [80, 20000],
            "dispersion_angle_h": 90,
            "dispersion_angle_v": 90
        },
        "zone_defaults": {
            "target_spl": 85.0,
            "ceiling_height": 9.0,
            "listener_height": 4.0,
            "environment_type": "enclosed"
        },
        "export": {
            "default_format": "png",
            "image_quality": 95,
            "include_legend": True,
            "include_scale": True,
            "dpi": 300
        },
        "units": {
            "length": "feet",  # feet, meters
            "area": "square_feet",  # square_feet, square_meters
            "temperature": "fahrenheit"  # fahrenheit, celsius
        }
    }

    def __init__(self,
                 config_dir: Optional[Union[str, Path]] = None,
                 user_config_dir: Optional[Union[str, Path]] = None):
        """Initialize configuration manager.

        Two directories on purpose:
        - `config_dir`: bundled defaults shipped with the app. Read-only when
          installed (lives inside the .app on macOS). Holds `config.json`.
        - `user_config_dir`: user overrides. Must be writable across reinstalls.
          Holds `user_config.json`. Caller should pass an OS-standard user-data
          location (e.g. `~/Library/Application Support/AcoustiCAD/config/`).

        If `user_config_dir` is omitted, falls back to `config_dir` (legacy
        single-directory behavior) — only safe when running from source.
        """
        self.logger = logging.getLogger(__name__)

        # Bundled defaults dir (read-only in installed builds)
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config"
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"

        # User overrides dir (must be writable; falls back to bundled dir for source runs)
        self.user_config_dir = Path(user_config_dir) if user_config_dir else self.config_dir
        self.user_config_file = self.user_config_dir / "user_config.json"

        # Only create the user dir — never try to mkdir inside a read-only bundle
        try:
            self.user_config_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.logger.error(f"Could not create user config dir {self.user_config_dir}: {e}")

        # One-shot migration: when user_config moved from the bundled dir to the
        # OS user-data dir (2026-05-26), any existing dev-run user_config.json
        # left behind in `config_dir` gets copied to the new location. Runs
        # every startup but is a no-op once the new file exists — the new file's
        # existence is the sentinel (idempotent by construction).
        legacy_user_config = self.config_dir / "user_config.json"
        if (legacy_user_config.exists()
                and not self.user_config_file.exists()
                and legacy_user_config != self.user_config_file):
            try:
                self.user_config_file.write_bytes(legacy_user_config.read_bytes())
                self.logger.info(
                    f"Migrated user_config: {legacy_user_config} → {self.user_config_file}"
                )
            except OSError as e:
                self.logger.warning(f"Could not migrate legacy user_config ({e})")

        # Load configuration
        self.config = self._load_config()

        self.logger.debug(
            f"ConfigManager initialized — bundled: {self.config_dir}, "
            f"user: {self.user_config_dir}"
        )

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from files"""
        config = self.DEFAULT_CONFIG.copy()

        try:
            # Load default configuration file if it exists
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    config = self._deep_merge(config, file_config)
                    self.logger.debug(f"Loaded default config from: {self.config_file}")

            # Load user configuration file if it exists
            if self.user_config_file.exists():
                with open(self.user_config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config = self._deep_merge(config, user_config)
                    self.logger.debug(f"Loaded user config from: {self.user_config_file}")
            else:
                # Create default user config file
                self._save_user_config(config)

        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.logger.info("Using default configuration")
            config = self.DEFAULT_CONFIG.copy()

        return config

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get(self, key: str, default: Any = None, section: Optional[str] = None) -> Any:
        """Get configuration value with optional section"""
        try:
            if section:
                if section in self.config and key in self.config[section]:
                    return self.config[section][key]
            else:
                # Navigate nested keys with dot notation
                keys = key.split('.')
                value = self.config

                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return default

                return value

            return default

        except Exception as e:
            self.logger.error(f"Error getting config value '{key}': {e}")
            return default

    def set(self, key: str, value: Any, section: Optional[str] = None, save: bool = True) -> bool:
        """Set configuration value"""
        try:
            if section:
                if section not in self.config:
                    self.config[section] = {}
                self.config[section][key] = value
            else:
                # Navigate nested keys with dot notation
                keys = key.split('.')
                config_ref = self.config

                # Navigate to the parent of the final key
                for k in keys[:-1]:
                    if k not in config_ref:
                        config_ref[k] = {}
                    config_ref = config_ref[k]

                # Set the final value
                config_ref[keys[-1]] = value

            if save:
                self._save_user_config()

            self.logger.debug(f"Set config value '{key}' = {value}")
            return True

        except Exception as e:
            self.logger.error(f"Error setting config value '{key}': {e}")
            return False

    def _save_user_config(self, config: Optional[Dict] = None) -> bool:
        """Save user configuration to file"""
        try:
            config_to_save = config or self.config

            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)

            self.logger.debug(f"Saved user config to: {self.user_config_file}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving user configuration: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        try:
            self.config = self.DEFAULT_CONFIG.copy()
            self._save_user_config()
            self.logger.info("Configuration reset to defaults")
            return True

        except Exception as e:
            self.logger.error(f"Error resetting configuration: {e}")
            return False

    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate current configuration"""
        errors = []

        try:
            # Validate required sections
            required_sections = ['app', 'ui', 'paths']
            for section in required_sections:
                if section not in self.config:
                    errors.append(f"Missing required section: {section}")

            # Validate specific values
            if self.get('ui.window.default_width', 0) < 800:
                errors.append("Window width must be at least 800 pixels")

            if self.get('ui.window.default_height', 0) < 600:
                errors.append("Window height must be at least 600 pixels")

            if self.get('speaker_defaults.sensitivity', 0) < 70 or self.get('speaker_defaults.sensitivity', 0) > 110:
                errors.append("Speaker sensitivity must be between 70 and 110 dB")

            # Validate paths exist or can be created
            for path_key in ['speaker_profiles', 'projects', 'exports', 'logs']:
                path_value = self.get(f'paths.{path_key}')
                if not path_value:
                    errors.append(f"Path not specified: {path_key}")

            return len(errors) == 0, errors

        except Exception as e:
            errors.append(f"Configuration validation error: {e}")
            return False, errors

    def get_app_paths(self, base_dir: Path) -> Dict[str, Path]:
        """Get all application paths resolved to absolute paths"""
        paths = {}

        for key, relative_path in self.get('paths', {}).items():
            if relative_path:
                paths[key] = base_dir / relative_path
            else:
                paths[key] = base_dir / key

        return paths

    def export_config(self, file_path: Union[str, Path]) -> bool:
        """Export current configuration to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Configuration exported to: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False

    def import_config(self, file_path: Union[str, Path]) -> bool:
        """Import configuration from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)

            # Validate imported config
            if not isinstance(imported_config, dict):
                raise ValueError("Invalid configuration format")

            # Merge with current config
            self.config = self._deep_merge(self.config, imported_config)
            self._save_user_config()

            self.logger.info(f"Configuration imported from: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False