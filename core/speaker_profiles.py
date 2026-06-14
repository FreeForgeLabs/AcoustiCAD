import math
import json
import logging
import shutil
import sys
from pathlib import Path
from datetime import datetime

import __version__ as _version_module

_APP_NAME = _version_module.APP_NAME


class SpeakerProfile:
    """
    Class representing a speaker profile with properties needed for acoustic calculations.
    """

    def __init__(self, name="Generic Speaker", manufacturer="Generic",
                 model_type="In-Ceiling", sensitivity=89.0, power_taps=None,
                 impedance=8.0, frequency_range=(80, 20000),
                 dispersion_angle_h=90, dispersion_angle_v=90,
                 directivity_factor=None, diameter=6.0,
                 dimensions=None):
        """
        Initialize a speaker profile with default values

        Args:
            name (str): Name of the speaker profile
            manufacturer (str): Manufacturer name
            model_type (str): Type of speaker (In-Ceiling, Pendant, Surface Mount)
            sensitivity (float): Sensitivity in dB (1W/1m)
            power_taps (list): List of power taps in Watts
            impedance (float): Impedance in Ohms
            frequency_range (tuple): Low and high frequency range in Hz
            dispersion_angle_h (float): Horizontal dispersion angle in degrees
            dispersion_angle_v (float): Vertical dispersion angle in degrees
            directivity_factor (float): Q factor, if None will be calculated from dispersion
            diameter (float): Diameter in inches (for In-Ceiling and Pendant speakers)
            dimensions (dict): Dimensions in inches (width, height, depth) for Surface Mount speakers
        """
        self.name = name
        self.manufacturer = manufacturer
        self.model_type = model_type
        self.sensitivity = sensitivity

        # Default power taps if none provided (In-Ceiling and Pendant)
        if power_taps is None:
            if diameter <= 4:
                self.power_taps = [1.0, 2.0, 5.0]
            elif diameter <= 6:
                self.power_taps = [2.0, 5.0, 10.0, 15.0]
            else:
                self.power_taps = [5.0, 10.0, 15.0, 30.0, 60.0]
        else:
            self.power_taps = power_taps

        # For backward compatibility
        self.power_rating = self.power_taps[-1] if self.power_taps else 30.0

        self.impedance = impedance
        self.frequency_range = frequency_range
        self.dispersion_angle_h = dispersion_angle_h
        self.dispersion_angle_v = dispersion_angle_v

        self.diameter = diameter

        # Calculate Q factor if not provided
        if directivity_factor is None:
            self.directivity_factor = self._calculate_directivity_factor()
        else:
            self.directivity_factor = directivity_factor

        # Metadata for tracking
        self.metadata = {
            "source": "custom",
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "modified_date": datetime.now().strftime("%Y-%m-%d")
        }

        # Will store frequency-specific data when available
        self.frequency_data = {}

    def _calculate_directivity_factor(self):
        """Calculate the directivity factor (Q) based on dispersion angles"""
        # Simple approximation based on dispersion angles
        # Q ≈ 180° / (horizontal angle × vertical angle) × 4π
        horizontal_radians = math.radians(self.dispersion_angle_h)
        vertical_radians = math.radians(self.dispersion_angle_v)
        solid_angle = horizontal_radians * vertical_radians
        return min(4 * math.pi / solid_angle, 20.0)  # Cap at reasonable value

    def calculate_spl_at_distance(self, distance_meters, power_watts=1.0):
        """
        Calculate SPL at a given distance using inverse square law

        Args:
            distance_meters (float): Distance from speaker in meters
            power_watts (float): Power applied to speaker in watts

        Returns:
            float: SPL in dB at the specified distance
        """
        # SPL calculation using inverse square law with directivity
        # SPL = Sensitivity + 10*log10(Power/1W) - 20*log10(distance/1m) + 10*log10(Q/4π)
        power_factor = 10 * math.log10(power_watts) if power_watts > 0 else 0
        distance_factor = 20 * math.log10(distance_meters) if distance_meters > 0 else 0
        directivity_factor = 10 * math.log10(self.directivity_factor / (4 * math.pi))

        return self.sensitivity + power_factor - distance_factor + directivity_factor

    def calculate_coverage_radius(self, ceiling_height, listener_height=4.0):
        """
        Calculate coverage radius based on dispersion angle and mounting height

        Args:
            ceiling_height (float): Height of ceiling/speaker mounting in feet
            listener_height (float): Height of listener ears in feet

        Returns:
            float: Coverage radius in feet
        """
        coverage_height = ceiling_height - listener_height
        if coverage_height <= 0:
            return 0

        # Use smaller dispersion angle for conservative estimate
        dispersion_angle = min(self.dispersion_angle_h, self.dispersion_angle_v)
        angle_rad = math.radians(dispersion_angle / 2)
        coverage_radius = coverage_height * math.tan(angle_rad)

        return coverage_radius

    def to_dict(self):
        """Convert profile to dictionary for serialization"""
        return {
            'name': self.name,
            'manufacturer': self.manufacturer,
            'model_type': self.model_type,
            'sensitivity': self.sensitivity,
            'power_taps': self.power_taps,
            'power_rating': self.power_rating,  # For backward compatibility
            'impedance': self.impedance,
            'frequency_range': self.frequency_range,
            'dispersion_angle_h': self.dispersion_angle_h,
            'dispersion_angle_v': self.dispersion_angle_v,
            'directivity_factor': self.directivity_factor,
            'diameter': self.diameter,
            'metadata': self.metadata,
            'frequency_data': self.frequency_data
        }

    @classmethod
    def from_dict(cls, data):
        """Create profile from dictionary"""
        # Extract power_taps if available, otherwise create from power_rating
        power_taps = data.get('power_taps')
        if power_taps is None and 'power_rating' in data:
            power_taps = [data.get('power_rating', 30.0)]

        # Treat any legacy Surface Mount profiles as In-Ceiling for backward compatibility
        model_type = data.get('model_type', 'In-Ceiling')
        if model_type == 'Surface Mount':
            model_type = 'In-Ceiling'

        profile = cls(
            name=data.get('name', 'Unknown Speaker'),
            manufacturer=data.get('manufacturer', 'Generic'),
            model_type=model_type,
            sensitivity=data.get('sensitivity', 89.0),
            power_taps=power_taps,
            impedance=data.get('impedance', 8.0),
            frequency_range=tuple(data.get('frequency_range', (80, 20000))),
            dispersion_angle_h=data.get('dispersion_angle_h', 90),
            dispersion_angle_v=data.get('dispersion_angle_v', 90),
            directivity_factor=data.get('directivity_factor', None),
            diameter=data.get('diameter', 6.0),
        )

        # Load frequency data if available
        if 'frequency_data' in data:
            profile.frequency_data = data['frequency_data']

        # Load metadata if available
        if 'metadata' in data:
            profile.metadata = data['metadata']

        return profile

    def validate(self):
        """
        Validate that the profile has all required fields with valid values

        Returns:
            tuple: (is_valid, error_message)
        """
        # Check required fields
        if not self.name:
            return (False, "Speaker name is required")

        if not self.model_type:
            return (False, "Speaker type is required")

        # Check value ranges
        if not (70 <= self.sensitivity <= 110):
            return (False, "Sensitivity must be between 70 and 110 dB")

        if not self.power_taps:
            return (False, "At least one power tap must be defined")

        for power in self.power_taps:
            if not (1 <= power <= 1000):
                return (False, f"Power tap {power}W is outside valid range (1-1000W)")

        if not (30 <= self.dispersion_angle_h <= 180):
            return (False, "Horizontal dispersion angle must be between 30 and 180 degrees")

        if not (30 <= self.dispersion_angle_v <= 180):
            return (False, "Vertical dispersion angle must be between 30 and 180 degrees")

        # Validate diameter (applies to both In-Ceiling and Pendant)
        if not (2 <= self.diameter <= 24):
            return (False, "Speaker diameter must be between 2 and 24 inches")

        return (True, "")


class SpeakerProfileManager:
    """
    Manages a collection of speaker profiles
    """

    def __init__(self, profiles_dir=None):
        """
        Initialize with profiles directory

        Args:
            profiles_dir (str): Directory to store/load profiles from
        """
        self.logger = logging.getLogger(__name__)
        self.profiles = {}

        # Set up profiles directory
        if profiles_dir is None:
            # Default to the OS user-data dir (~/Library/Application Support/AcoustiCAD
            # on macOS) — same runtime root as Storage, never the bare home folder.
            from utils.storage import _platform_app_dir
            self.profiles_dir = Path(_platform_app_dir(_APP_NAME)) / "speaker_profiles"
        else:
            self.profiles_dir = Path(profiles_dir)

        # Ensure directory exists
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        # Seed bundled default profiles (non-destructive — only copies missing files)
        self._seed_default_profiles()

        # Load any existing profiles
        self.load_profiles()

        # Log the profiles directory location
        self.logger.info(f"Using speaker profiles directory: {self.profiles_dir}")

    def load_profiles(self):
        """Load all profile files from the profiles directory"""
        self.profiles = {}

        for file_path in self.profiles_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    profile = SpeakerProfile.from_dict(data)

                    # Generate key based on manufacturer and name
                    key = f"{profile.manufacturer}_{profile.name}"
                    self.profiles[key] = profile
                    self.logger.debug(f"Loaded profile: {key}")
            except Exception as e:
                self.logger.error(f"Error loading profile {file_path}: {e}")

        self.logger.info(f"Loaded {len(self.profiles)} speaker profiles")

    # ── Default profile seeding ───────────────────────────────────────────

    @staticmethod
    def _get_bundled_profiles_dir() -> Path:
        """Return the path to the bundled default speaker profiles directory.

        Works both from source (dev) and from a PyInstaller-frozen app bundle.
        """
        if getattr(sys, 'frozen', False):
            # Running as a PyInstaller bundle — resources live under sys._MEIPASS
            base = Path(sys._MEIPASS)
        else:
            # Running from source — project root is two levels up from this file
            base = Path(__file__).parent.parent
        return base / 'data' / 'default_speaker_profiles'

    def _seed_default_profiles(self):
        """Copy any missing bundled default profiles into the user's profiles directory.

        This is intentionally non-destructive: if a file with the same name already
        exists (because the user edited it or a previous run seeded it) it is left
        untouched.  New profiles added in future app versions are picked up on the
        next launch.
        """
        bundled_dir = self._get_bundled_profiles_dir()
        if not bundled_dir.is_dir():
            self.logger.debug(f"No bundled profiles directory found at {bundled_dir}")
            return

        seeded = 0
        for src in bundled_dir.glob("*.json"):
            dest = self.profiles_dir / src.name
            if not dest.exists():
                try:
                    shutil.copy2(src, dest)
                    seeded += 1
                    self.logger.debug(f"Seeded default profile: {src.name}")
                except Exception as e:
                    self.logger.warning(f"Could not seed profile {src.name}: {e}")

        if seeded:
            self.logger.info(f"Seeded {seeded} default speaker profile(s) into {self.profiles_dir}")

    def add_profile(self, profile):
        """
        Add a profile to the collection

        Args:
            profile (SpeakerProfile): Speaker profile to add

        Returns:
            bool: True if added successfully, False otherwise
        """
        # Validate the profile
        is_valid, error_message = profile.validate()
        if not is_valid:
            self.logger.error(f"Invalid profile: {error_message}")
            return False

        # Generate key based on manufacturer and name
        key = f"{profile.manufacturer}_{profile.name}"

        # Check if profile already exists
        if key in self.profiles:
            self.logger.warning(f"Profile {key} already exists. Overwriting.")

        # Add to collection
        self.profiles[key] = profile

        # Log the actual profiles directory being used
        self.logger.info(f"Saving profile to directory: {self.profiles_dir}")

        # Save to file
        try:
            self._save_profile_to_file(profile)
            return True
        except Exception as e:
            self.logger.error(f"Error saving profile {key}: {e}")
            return False

    def _save_profile_to_file(self, profile):
        """Save a profile to a JSON file in the profiles directory"""
        # Update modified date
        profile.metadata["modified_date"] = datetime.now().strftime("%Y-%m-%d")

        # Create filename from manufacturer and name
        safe_name = profile.name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        safe_manufacturer = profile.manufacturer.replace(" ", "_").replace("/", "_").replace("\\", "_")

        filename = f"{safe_manufacturer}_{safe_name}.json"
        file_path = self.profiles_dir / filename

        # Log the full path
        self.logger.info(f"Saving profile to file: {file_path}")

        # Save as JSON
        with open(file_path, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)

        self.logger.debug(f"Saved profile to {file_path}")

    def get_profile(self, key):
        """
        Get a profile by key (manufacturer_name)

        Args:
            key (str): Profile key in format "manufacturer_name"

        Returns:
            SpeakerProfile: The profile or None if not found
        """
        return self.profiles.get(key)

    def get_profile_by_name(self, name, manufacturer=None):
        """
        Get a profile by name and optionally manufacturer

        Args:
            name (str): Profile name
            manufacturer (str, optional): Manufacturer name

        Returns:
            SpeakerProfile: The profile or None if not found
        """
        for key, profile in self.profiles.items():
            if profile.name == name and (manufacturer is None or profile.manufacturer == manufacturer):
                return profile
        return None

    def list_profiles(self):
        """
        List all available profiles

        Returns:
            list: List of (key, profile) tuples
        """
        return list(self.profiles.items())

    def remove_profile(self, key):
        """
        Remove a profile from the collection

        Args:
            key (str): Profile key in format "manufacturer_name"

        Returns:
            bool: True if removed successfully, False otherwise
        """
        if key not in self.profiles:
            self.logger.warning(f"Profile {key} not found")
            return False

        # Remove from collection
        profile = self.profiles.pop(key)

        # Remove file
        try:
            safe_name = profile.name.replace(" ", "_").replace("/", "_").replace("\\", "_")
            safe_manufacturer = profile.manufacturer.replace(" ", "_").replace("/", "_").replace("\\", "_")

            filename = f"{safe_manufacturer}_{safe_name}.json"
            file_path = self.profiles_dir / filename

            if file_path.exists():
                file_path.unlink()
                self.logger.debug(f"Deleted profile file {file_path}")

            return True
        except Exception as e:
            self.logger.error(f"Error removing profile {key}: {e}")
            return False