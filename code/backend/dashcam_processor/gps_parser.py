"""
GPS Parser Module
Handles parsing GPS .git files and converting to data format
"""
import re
from datetime import datetime, timedelta

def parse_lat_lon(value, direction):
    """
    Parse latitude/longitude from GPS format to decimal degrees
    
    Args:
        value (str): GPS coordinate value
        direction (str): Direction indicator (N/S/E/W)
    
    Returns:
        float: Decimal degrees coordinate or None if invalid
    """
    if not value or len(value) < 4:
        return None
    try:
        if direction in ['N', 'S']:
            degrees = int(value[:2])
            minutes = float(value[2:])
        elif direction in ['E', 'W']:
            degrees = int(value[:3])
            minutes = float(value[3:])
        else:
            return None

        decimal = degrees + minutes / 60.0
        if direction in ['S', 'W']:
            decimal = -decimal
        return round(decimal, 6)
    except ValueError:
        return None

def convert_git_to_data(git_path):
    """
    Convert GPS .git file to structured data
    
    Args:
        git_path (str): Path to the .git GPS file
    
    Returns:
        list: List of GPS data dictionaries with date, time, lat, lon, speed, alt
    """
    with open(git_path, 'rb') as f:
        content = f.read()

    # Extract readable strings from binary content
    strings = re.findall(rb"[ -~]{4,}", content)
    decoded = [s.decode("utf-8", errors="ignore") for s in strings]

    # Filter GPS sentences
    gprmc = [s for s in decoded if s.startswith("$GPRMC")]
    gpgga = [s for s in decoded if s.startswith("$GPGGA")]

    gps_data = []
    for rmc, gga in zip(gprmc, gpgga):
        try:
            r = rmc.split(",")
            g = gga.split(",")

            time_raw = r[1]
            date_raw = r[9]

            # Parse date and time
            if len(date_raw) == 6 and len(time_raw) >= 6:
                dt_utc = datetime.strptime(
                    f"20{date_raw[4:6]}-{date_raw[2:4]}-{date_raw[:2]} {time_raw[:2]}:{time_raw[2:4]}:{time_raw[4:6]}",
                    "%Y-%m-%d %H:%M:%S"
                )
                # Convert to IST (UTC + 5:30:44)
                dt_ist = dt_utc + timedelta(hours=5, minutes=30, seconds=44)
                date_str = dt_ist.strftime("%m/%d/%Y")
                time_str = dt_ist.strftime("%I:%M:%S %p")
            else:
                continue

            # Parse coordinates
            lat = parse_lat_lon(r[3], r[4])
            lon = parse_lat_lon(r[5], r[6])
            
            # Parse speed (convert knots to km/h)
            speed = round(float(r[7]) * 1.852, 2) if r[7] else None
            
            # Parse altitude
            alt = float(g[9]) if g[9] else None

            gps_data.append({
                'date': date_str,
                'time': time_str,
                'lat': lat,
                'lon': lon,
                'speed': speed,
                'alt': alt
            })

        except Exception:
            continue

    return gps_data

def find_matching_gps(gps_data, date, time):
    """
    Find GPS entry matching the given date and time
    
    Args:
        gps_data (list): List of GPS data dictionaries
        date (str): Date string in MM/DD/YYYY format
        time (str): Time string in HH:MM:SS AM/PM format
    
    Returns:
        dict: Matching GPS entry or None if not found
    """
    for entry in gps_data:
        if entry['date'] == date and entry['time'] == time:
            return entry
    return None
