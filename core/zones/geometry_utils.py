import math
import logging

logger = logging.getLogger(__name__)


def point_inside_polygon(point, polygon):
    """
    Determine if a point is inside a polygon using the ray casting algorithm

    Args:
        point (tuple): (x, y) tuple representing the point
        polygon (list): List of (x, y) tuples representing the polygon vertices

    Returns:
        bool: True if the point is inside the polygon, False otherwise
    """
    if not point or not polygon or len(polygon) < 3:
        logger.warning("Invalid point or polygon in point_inside_polygon")
        return False

    try:
        x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        else:
                            xinters = p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside
    except Exception as e:
        logger.error(f"Error in point_inside_polygon: {e}", exc_info=True)
        return False


def calculate_polygon_area(points):
    """
    Calculate the area of a polygon using the Shoelace formula

    Args:
        points (list): List of (x, y) tuples representing the polygon vertices

    Returns:
        float: The area of the polygon in square pixels
    """
    if not points:
        logger.warning("Empty points list in calculate_polygon_area")
        return 0.0

    n = len(points)
    if n < 3:
        logger.warning(f"Not enough points to calculate area: {n} (need at least 3)")
        return 0.0

    try:
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]

        area = abs(area) / 2.0
        logger.debug(f"Calculated polygon area: {area:.2f} square pixels for {n} points")
        return area
    except Exception as e:
        logger.error(f"Error in calculate_polygon_area: {e}", exc_info=True)
        return 0.0


def convert_area_to_square_feet(area_pixels, scale_factor):
    """
    Convert an area from square pixels to square feet

    Args:
        area_pixels (float): Area in square pixels
        scale_factor (float): Conversion factor (pixels per foot)

    Returns:
        float: The area in square feet
    """
    if area_pixels <= 0:
        logger.warning(f"Invalid area_pixels in convert_area_to_square_feet: {area_pixels}")
        return 0.0

    if scale_factor <= 0:
        logger.warning(f"Invalid scale_factor in convert_area_to_square_feet: {scale_factor}")
        return 0.0

    try:
        area_feet = area_pixels / (scale_factor * scale_factor)
        logger.debug(f"Converted area: {area_pixels:.2f} sq.px → {area_feet:.2f} sq.ft (scale factor: {scale_factor})")
        return area_feet
    except Exception as e:
        logger.error(f"Error in convert_area_to_square_feet: {e}", exc_info=True)
        return 0.0


def calculate_perimeter(points):
    """
    Calculate the perimeter of a polygon

    Args:
        points (list): List of (x, y) tuples representing the polygon vertices

    Returns:
        float: The perimeter of the polygon in pixels
    """
    if not points:
        logger.warning("Empty points list in calculate_perimeter")
        return 0.0

    n = len(points)
    if n < 2:
        logger.warning(f"Not enough points to calculate perimeter: {n} (need at least 2)")
        return 0.0

    try:
        perimeter = 0.0
        for i in range(n):
            j = (i + 1) % n
            dx = points[j][0] - points[i][0]
            dy = points[j][1] - points[i][1]
            perimeter += math.sqrt(dx * dx + dy * dy)

        logger.debug(f"Calculated polygon perimeter: {perimeter:.2f} pixels for {n} points")
        return perimeter
    except Exception as e:
        logger.error(f"Error in calculate_perimeter: {e}", exc_info=True)
        return 0.0


def convert_length_to_feet(length_pixels, scale_factor):
    """
    Convert a length from pixels to feet

    Args:
        length_pixels (float): Length in pixels
        scale_factor (float): Conversion factor (pixels per foot)

    Returns:
        float: The length in feet
    """
    if length_pixels < 0:
        logger.warning(f"Invalid length_pixels in convert_length_to_feet: {length_pixels}")
        return 0.0

    if scale_factor <= 0:
        logger.warning(f"Invalid scale_factor in convert_length_to_feet: {scale_factor}")
        return 0.0

    try:
        length_feet = length_pixels / scale_factor
        logger.debug(f"Converted length: {length_pixels:.2f} px → {length_feet:.2f} ft (scale factor: {scale_factor})")
        return length_feet
    except Exception as e:
        logger.error(f"Error in convert_length_to_feet: {e}", exc_info=True)
        return 0.0


def calculate_polygon_centroid(points):
    """
    Calculate the centroid (geometric center) of a polygon

    Args:
        points (list): List of (x, y) tuples representing the polygon vertices

    Returns:
        tuple: (x, y) tuple representing the centroid
    """
    if not points:
        logger.warning("Empty points list in calculate_polygon_centroid")
        return (0, 0)

    n = len(points)
    if n < 1:
        logger.warning("No points provided to calculate_polygon_centroid")
        return (0, 0)

    try:
        if n < 3:
            # If just 1 or 2 points, return the average
            x_sum = sum(p[0] for p in points)
            y_sum = sum(p[1] for p in points)
            return (x_sum / n, y_sum / n)

        # For polygon, use the signed-area centroid formula so the result is
        # correct regardless of vertex winding order (CW or CCW).
        signed_area = 0.0
        for i in range(n):
            j = (i + 1) % n
            signed_area += points[i][0] * points[j][1] - points[j][0] * points[i][1]
        signed_area /= 2.0

        if signed_area == 0:
            x_sum = sum(p[0] for p in points)
            y_sum = sum(p[1] for p in points)
            logger.warning("Zero area polygon in calculate_polygon_centroid, using average")
            return (x_sum / n, y_sum / n)

        cx = 0.0
        cy = 0.0
        for i in range(n):
            j = (i + 1) % n
            factor = points[i][0] * points[j][1] - points[j][0] * points[i][1]
            cx += (points[i][0] + points[j][0]) * factor
            cy += (points[i][1] + points[j][1]) * factor

        denom = 6.0 * signed_area
        cx /= denom
        cy /= denom

        logger.debug(f"Calculated polygon centroid: ({cx:.2f}, {cy:.2f}) for {n} points")
        return (cx, cy)
    except Exception as e:
        logger.error(f"Error in calculate_polygon_centroid: {e}", exc_info=True)
        # Return center of bounding box as fallback
        try:
            min_x = min(p[0] for p in points)
            max_x = max(p[0] for p in points)
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)
            return ((min_x + max_x) / 2, (min_y + max_y) / 2)
        except:
            return (0, 0)


def distance_between_points(p1, p2):
    """
    Calculate the Euclidean distance between two points

    Args:
        p1 (tuple): (x, y) tuple representing the first point
        p2 (tuple): (x, y) tuple representing the second point

    Returns:
        float: The distance between the points
    """
    if not p1 or not p2:
        logger.warning("Invalid points in distance_between_points")
        return 0.0

    try:
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        distance = math.sqrt(dx * dx + dy * dy)
        logger.debug(f"Distance between points: {distance:.2f}")
        return distance
    except Exception as e:
        logger.error(f"Error in distance_between_points: {e}", exc_info=True)
        return 0.0


def simplify_polygon(points, tolerance):
    """
    Simplify a polygon using the Ramer-Douglas-Peucker algorithm

    Args:
        points (list): List of (x, y) tuples representing the polygon vertices
        tolerance (float): Maximum distance between the original and simplified curves

    Returns:
        list: List of (x, y) tuples representing the simplified polygon vertices
    """
    if not points:
        logger.warning("Empty points list in simplify_polygon")
        return []

    if len(points) <= 2 or tolerance <= 0:
        return points.copy()

    try:
        def perpendicular_distance(point, line_start, line_end):
            """Calculate the perpendicular distance from a point to a line"""
            if line_start == line_end:
                return distance_between_points(point, line_start)

            nx = line_end[1] - line_start[1]
            ny = line_start[0] - line_end[0]
            nz = line_start[1] * line_end[0] - line_start[0] * line_end[1]

            dist = abs(nx * point[0] + ny * point[1] + nz) / math.sqrt(nx * nx + ny * ny)
            return dist

        def rdp(points_list, epsilon):
            """Recursive implementation of Ramer-Douglas-Peucker algorithm"""
            # Find the point with the maximum distance from the line
            dmax = 0
            index = 0
            end = len(points_list) - 1

            for i in range(1, end):
                d = perpendicular_distance(points_list[i], points_list[0], points_list[end])
                if d > dmax:
                    index = i
                    dmax = d

            # If max distance is greater than epsilon, recursively simplify
            if dmax > epsilon:
                # Recursive call
                rec_results1 = rdp(points_list[:index + 1], epsilon)
                rec_results2 = rdp(points_list[index:], epsilon)

                # Build the result list
                result_list = rec_results1[:-1] + rec_results2
                return result_list
            else:
                return [points_list[0], points_list[end]]

        # Close the polygon if it's not already closed
        closed = points[0] == points[-1]
        if not closed:
            points = points + [points[0]]

        # Apply the algorithm
        simplified = rdp(points, tolerance)

        # Ensure the polygon remains closed
        if closed and simplified[0] != simplified[-1]:
            simplified.append(simplified[0])
        elif not closed and len(simplified) > 1 and simplified[0] == simplified[-1]:
            simplified.pop()

        original_count = len(points)
        simplified_count = len(simplified)
        if original_count > simplified_count:
            logger.info(
                f"Simplified polygon: {original_count} points → {simplified_count} points (tolerance: {tolerance})")

        return simplified
    except Exception as e:
        logger.error(f"Error in simplify_polygon: {e}", exc_info=True)
        return points.copy()  # Return original points on error


def get_angle_between_points(p1, p2, p3):
    """
    Calculate the angle between three points (angle at p2)

    Args:
        p1 (tuple): First point (x, y)
        p2 (tuple): Middle point (x, y) where the angle is calculated
        p3 (tuple): Third point (x, y)

    Returns:
        float: Angle in degrees
    """
    if not p1 or not p2 or not p3:
        logger.warning("Invalid points in get_angle_between_points")
        return 0.0

    try:
        # Vectors from p2 to p1 and p2 to p3
        v1x = p1[0] - p2[0]
        v1y = p1[1] - p2[1]
        v2x = p3[0] - p2[0]
        v2y = p3[1] - p2[1]

        # Dot product
        dot_product = v1x * v2x + v1y * v2y

        # Magnitudes
        v1_mag = math.sqrt(v1x * v1x + v1y * v1y)
        v2_mag = math.sqrt(v2x * v2x + v2y * v2y)

        # Angle in radians
        if v1_mag == 0 or v2_mag == 0:
            return 0.0

        cos_angle = max(-1.0, min(1.0, dot_product / (v1_mag * v2_mag)))
        angle_rad = math.acos(cos_angle)

        # Convert to degrees
        angle_deg = math.degrees(angle_rad)

        logger.debug(f"Angle between points: {angle_deg:.2f} degrees")
        return angle_deg
    except Exception as e:
        logger.error(f"Error in get_angle_between_points: {e}", exc_info=True)
        return 0.0


def is_convex_polygon(points):
    """
    Check if a polygon is convex

    Args:
        points (list): List of (x, y) tuples representing the polygon vertices

    Returns:
        bool: True if the polygon is convex, False otherwise
    """
    if not points or len(points) < 3:
        logger.warning("Invalid points list in is_convex_polygon")
        return False

    try:
        # For polygons with less than 4 points, it's always convex
        if len(points) < 4:
            return True

        # Check the orientation of each corner
        sign = 0
        n = len(points)

        for i in range(n):
            j = (i + 1) % n
            k = (i + 2) % n

            # Calculate cross product (z component)
            cross_product = (points[j][0] - points[i][0]) * (points[k][1] - points[j][1]) - \
                            (points[j][1] - points[i][1]) * (points[k][0] - points[j][0])

            # Check the sign of the cross product
            if cross_product > 0:
                curr_sign = 1
            elif cross_product < 0:
                curr_sign = -1
            else:
                # Collinear points - skip
                continue

            # If we haven't set a sign yet
            if sign == 0:
                sign = curr_sign
            # If the sign changes, the polygon is not convex
            elif sign != curr_sign:
                return False

        # If we get here, the polygon is convex
        return True
    except Exception as e:
        logger.error(f"Error in is_convex_polygon: {e}", exc_info=True)
        return False


def get_bounding_box(points):
    """
    Get the bounding box for a set of points

    Args:
        points (list): List of (x, y) tuples

    Returns:
        tuple: (min_x, min_y, max_x, max_y) representing the bounding box
    """
    if not points:
        logger.warning("Empty points list in get_bounding_box")
        return (0, 0, 0, 0)

    try:
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)

        logger.debug(f"Bounding box: ({min_x}, {min_y}, {max_x}, {max_y})")
        return (min_x, min_y, max_x, max_y)
    except Exception as e:
        logger.error(f"Error in get_bounding_box: {e}", exc_info=True)
        return (0, 0, 0, 0)