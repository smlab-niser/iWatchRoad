import csv
import sys
import os

# Set maximum field size to handle large base64 data
try:
    csv.field_size_limit(131072 * 100)  # Set to a large but reasonable size
except OverflowError:
    csv.field_size_limit(131072)

def process_large_csv():
    input_file = 'pothole_gps_merged.csv'
    output_file = 'pothole_data_with_frames.csv'
    
    print(f"Processing {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            
            reader = csv.DictReader(infile)
            fieldnames = ['Frame', 'Date', 'Time', 'Latitude', 'Longitude', 'Pothole_Count', 'Pothole_Grade', 'GPS_Source', 'Distance_from_Previous', 'Frame_Data']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            count = 0
            processed = 0
            
            for row in reader:
                try:
                    # Extract all fields including Frame_Data
                    new_row = {}
                    for field in fieldnames:
                        value = row.get(field, '').strip()
                        # Limit frame data size to prevent issues
                        if field == 'Frame_Data' and len(value) > 1000000:  # 1MB limit
                            value = value[:1000000]  # Truncate if too large
                        new_row[field] = value
                    
                    # Only process rows with valid coordinates
                    if new_row['Latitude'] and new_row['Longitude']:
                        try:
                            lat = float(new_row['Latitude'])
                            lng = float(new_row['Longitude'])
                            if -90 <= lat <= 90 and -180 <= lng <= 180:
                                writer.writerow(new_row)
                                processed += 1
                        except ValueError:
                            continue
                    
                    count += 1
                    if count % 10 == 0:
                        print(f'Read {count} rows, processed {processed} valid rows')
                    
                    # Limit to first 50 rows for testing with frame data
                    if processed >= 50:
                        break
                        
                except Exception as e:
                    print(f"Error processing row {count}: {e}")
                    continue
            
            print(f'Completed! Created CSV with frames - {processed} valid rows from {count} total rows')
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    process_large_csv()
