import math
from enum import Enum

class WeightingType(Enum):
    """Enum for different weighting types"""
    Z_WEIGHTING = "Z"  # Flat - no weighting
    A_WEIGHTING = "A"  # A-weighting - common for environmental noise
    C_WEIGHTING = "C"  # C-weighting - for peak measurements


def calculate_spl(pressure, reference_pressure=2e-5):
    """
    Calculate Sound Pressure Level (SPL) in dB from pressure in pascals

    Args:
        pressure (float): Sound pressure in pascals
        reference_pressure (float): Reference pressure, typically 20 micropascals (2e-5 Pa)

    Returns:
        float: Sound pressure level in dB
    """
    # SPL formula: SPL = 20 * log10(p/p0)
    # where p is the measured pressure and p0 is the reference pressure
    if pressure <= 0:
        return 0.0

    return 20 * math.log10(pressure / reference_pressure)


def calculate_pressure_from_spl(spl, reference_pressure=2e-5):
    """
    Calculate pressure in pascals from Sound Pressure Level (SPL) in dB

    Args:
        spl (float): Sound pressure level in dB
        reference_pressure (float): Reference pressure, typically 20 micropascals (2e-5 Pa)

    Returns:
        float: Sound pressure in pascals
    """
    # Inverse of SPL formula: p = p0 * 10^(SPL/20)
    return reference_pressure * (10 ** (spl / 20))


def calculate_combined_spl(spl_values):
    """
    Calculate combined SPL from multiple SPL values

    Args:
        spl_values (list): List of SPL values in dB

    Returns:
        float: Combined SPL in dB
    """
    # The formula for combining SPL values is:
    # SPL_total = 10 * log10(sum(10^(SPL_i/10)))

    if not spl_values:
        return 0.0

    # Convert each SPL to linear scale, sum, then convert back to logarithmic scale
    total_power = sum(10 ** (spl / 10) for spl in spl_values)
    return 10 * math.log10(total_power)


def calculate_spl_at_distance(sensitivity, power, distance, directivity_factor=1.0):
    """
    Calculate SPL at a specific distance from a speaker

    Args:
        sensitivity (float): Speaker sensitivity in dB (1W/1m)
        power (float): Power applied to speaker in watts
        distance (float): Distance from speaker in meters
        directivity_factor (float): Speaker directivity factor (Q)

    Returns:
        float: SPL in dB at the specified distance
    """
    # SPL calculation using inverse square law with directivity
    # SPL = Sensitivity + 10*log10(Power/1W) - 20*log10(distance/1m) + 10*log10(Q/4π)

    if distance <= 0:
        return sensitivity  # Avoid division by zero

    power_factor = 10 * math.log10(power) if power > 0 else 0
    distance_factor = 20 * math.log10(distance) if distance > 0 else 0
    directivity_factor = 10 * math.log10(directivity_factor / (4 * math.pi))

    return sensitivity + power_factor - distance_factor + directivity_factor


def apply_a_weighting(frequency, spl):
    """
    Apply A-weighting to an SPL value at a specific frequency

    Args:
        frequency (float): Frequency in Hz
        spl (float): SPL in dB

    Returns:
        float: A-weighted SPL in dB(A)
    """
    # A-weighting approximation formula
    f2 = frequency ** 2
    numerator = 12200 ** 2 * f2 ** 2
    denominator = (f2 + 20.6 ** 2) * (f2 + 12200 ** 2) * math.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2))

    ra = numerator / denominator
    a_weight = 2.0 + 20 * math.log10(ra)

    return spl + a_weight


def apply_c_weighting(frequency, spl):
    """
    Apply C-weighting to an SPL value at a specific frequency

    Args:
        frequency (float): Frequency in Hz
        spl (float): SPL in dB

    Returns:
        float: C-weighted SPL in dB(C)
    """
    # C-weighting approximation formula
    f2 = frequency ** 2
    numerator = 12200 ** 2 * f2
    denominator = (f2 + 20.6 ** 2) * (f2 + 12200 ** 2)

    rc = numerator / denominator
    c_weight = 0.06 + 20 * math.log10(rc)

    return spl + c_weight


def apply_weighting(frequency, spl, weighting=WeightingType.Z_WEIGHTING):
    """
    Apply frequency weighting to an SPL value

    Args:
        frequency (float): Frequency in Hz
        spl (float): SPL in dB
        weighting (WeightingType): Weighting to apply

    Returns:
        float: Weighted SPL in dB
    """
    if weighting == WeightingType.A_WEIGHTING:
        return apply_a_weighting(frequency, spl)
    elif weighting == WeightingType.C_WEIGHTING:
        return apply_c_weighting(frequency, spl)
    else:  # Z-weighting (flat)
        return spl


def calculate_coverage_radius(ceiling_height, listener_height, dispersion_angle):
    """
    Calculate the coverage radius for a ceiling-mounted speaker

    Args:
        ceiling_height (float): Height of ceiling in feet
        listener_height (float): Height of listener ears in feet
        dispersion_angle (float): Speaker dispersion angle in degrees

    Returns:
        float: Coverage radius in feet
    """
    # Make sure heights are valid
    if ceiling_height <= listener_height:
        return 0.0

    # Calculate the difference in height
    height_diff = ceiling_height - listener_height

    # Convert dispersion angle to radians and calculate tangent
    angle_rad = math.radians(dispersion_angle / 2)  # Half-angle for cone radius

    # Calculate radius using tangent
    return height_diff * math.tan(angle_rad)


def calculate_atmospheric_attenuation(frequency, distance, temperature=20, humidity=60):
    """
    Calculate atmospheric attenuation for a given frequency and distance

    Args:
        frequency (float): Frequency in Hz
        distance (float): Distance in meters
        temperature (float): Temperature in Celsius
        humidity (float): Relative humidity (%)

    Returns:
        float: Attenuation in dB
    """
    # This is a simplified model based on ISO 9613-1
    # For precise calculations, the full standard should be implemented

    # Convert frequency to kHz for calculation
    freq_khz = frequency / 1000.0

    # Base attenuation factors depend on frequency
    if freq_khz < 1.0:
        # Low frequency
        base_attenuation = 0.01 * freq_khz ** 2
    elif freq_khz < 10.0:
        # Mid frequency
        base_attenuation = 0.05 * freq_khz
    else:
        # High frequency
        base_attenuation = 0.1 * freq_khz

    # Temperature and humidity adjustments (very simplified)
    temp_factor = 1.0 + (temperature - 20) * 0.01  # 1% change per degree from 20°C

    # Humidity has more effect at high frequencies
    if freq_khz < 1.0:
        humidity_factor = 1.0  # Low sensitivity to humidity at low frequencies
    else:
        # More attenuation at low humidity, less at high humidity
        humidity_factor = 2.0 - (humidity / 100)
        humidity_factor = max(0.5, min(humidity_factor, 1.5))  # Clamp between 0.5 and 1.5

    # Calculate total attenuation
    total_attenuation = base_attenuation * temp_factor * humidity_factor * distance / 100  # dB per 100m

    return total_attenuation

def calculate_speaker_spacing(sensitivity, power, target_spl, overlap_factor=0.5):
    """
    Calculate optimal speaker spacing for uniform coverage

    Args:
        sensitivity (float): Speaker sensitivity in dB (1W/1m)
        power (float): Power applied to speaker in watts
        target_spl (float): Target SPL in dB
        overlap_factor (float): Factor for speaker overlap (0-1)

    Returns:
        float: Optimal spacing in meters
    """
    # Calculate maximum distance where SPL is at target level
    # SPL = Sensitivity + 10*log10(Power) - 20*log10(distance)
    # Solving for distance:
    # distance = 10^((Sensitivity + 10*log10(Power) - target_spl) / 20)

    power_factor = 10 * math.log10(power) if power > 0 else 0
    max_distance = 10 ** ((sensitivity + power_factor - target_spl) / 20)

    # Apply overlap factor to get spacing
    return max_distance * (2 - overlap_factor)