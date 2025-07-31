"""
OCR Processor Module
Handles OCR text extraction and datetime parsing from video frames
"""
import re
import easyocr

class OCRProcessor:
    """
    OCR processor for extracting datetime information from video frames
    """
    
    def __init__(self, languages=['en'], gpu=False):
        """
        Initialize OCR reader
        
        Args:
            languages (list): List of languages for OCR
            gpu (bool): Whether to use GPU acceleration
        """
        self.reader = easyocr.Reader(languages, gpu=gpu)
    
    def crop_bottom_10_percent(self, image):
        """
        Crop bottom 10% of image where timestamp usually appears
        
        Args:
            image: Input image (numpy array)
        
        Returns:
            image: Cropped image
        """
        height = image.shape[0]
        start_row = int(height * 0.9)
        return image[start_row:, :]
    
    def extract_datetime_from_ocr_results(self, ocr_results):
        """
        Extract date and time from OCR results
        Handles common OCR mistakes like dots instead of slashes/colons and missing spaces
        
        Args:
            ocr_results: OCR results from easyocr
        
        Returns:
            tuple: (date, time) or None if not found
        """
        texts = [text for (_, text, _) in ocr_results]
        
        for i in range(len(texts)):
            # Look for date pattern MM/DD/YYYY or MM.DD.YYYY
            date_match = re.search(r"\d{2}[/.]?\d{2}[/.]?\d{4}", texts[i])
            if date_match:
                # Normalize date format - replace dots with slashes
                date = date_match.group().replace(".", "/")
                time = ""
                ampm = ""

                # Check next text for time
                if i + 1 < len(texts):
                    # Handle time with possible dots instead of colons and missing space before AM/PM
                    time_text = texts[i + 1]
                    
                    # Look for time pattern with optional AM/PM (with or without space)
                    # Handle mixed delimiters like hh.mm:ss, hh:mm.ss, or hh,mm,ss
                    time_match = re.search(r"(\d{1,2}[:.,']\d{2}[:.,']\d{2})\s*(AM|PM)?", time_text, re.IGNORECASE)
                    if time_match:
                        # Normalize all delimiters to colons
                        time = time_match.group(1).replace(".", ":").replace(",", ":")
                        if time_match.group(2):
                            ampm = time_match.group(2).upper()
                        # If no AM/PM found in current text, check surrounding texts more thoroughly
                        else:
                            # Check next few texts for AM/PM
                            for k in range(i + 2, min(len(texts), i + 5)):
                                ampm_match = re.search(r"\b(AM|PM)\b", texts[k], re.IGNORECASE)
                                if ampm_match:
                                    ampm = ampm_match.group().upper()
                                    break
                            
                            # If still not found, check for AM/PM attached to other text
                            if not ampm:
                                for k in range(i + 2, min(len(texts), i + 5)):
                                    ampm_match = re.search(r"(AM|PM)", texts[k], re.IGNORECASE)
                                    if ampm_match:
                                        ampm = ampm_match.group().upper()
                                        break

                # Check if date and time are in the same text (handle various formats)
                if not time:
                    # More flexible pattern to handle dots, colons, commas, and mixed delimiters
                    dt_match = re.search(r"(\d{2}[/.]?\d{2}[/.]?\d{4})\s+(\d{1,2}[:.,']\d{2}[:.,']\d{2})\s*(AM|PM)?", texts[i], re.IGNORECASE)
                    if dt_match:
                        date = dt_match.group(1).replace(".", "/")
                        # Normalize all time delimiters to colons
                        time = dt_match.group(2).replace(".", ":").replace(",", ":")
                        ampm = dt_match.group(3).upper() if dt_match.group(3) else ""

                # Also check for combined date-time without space separation
                if not time:
                    # Handle cases like "08.23.202411:45:30PM" or mixed delimiters including commas
                    combined_match = re.search(r"(\d{2}[/.]?\d{2}[/.]?\d{4})(\d{1,2}[:.,']\d{2}[:.,']\d{2})(AM|PM)?", texts[i], re.IGNORECASE)
                    if combined_match:
                        date = combined_match.group(1).replace(".", "/")
                        # Normalize all time delimiters to colons
                        time = combined_match.group(2).replace(".", ":").replace(",", ":")
                        ampm = combined_match.group(3).upper() if combined_match.group(3) else ""

                # If we found time but no AM/PM, check surrounding texts for AM/PM
                if time and not ampm:
                    # Check previous and next few texts for AM/PM
                    for j in range(max(0, i-1), min(len(texts), i+4)):
                        if j != i:  # Skip current text as we already checked it
                            ampm_match = re.search(r"\b(AM|PM)\b", texts[j], re.IGNORECASE)
                            if ampm_match:
                                ampm = ampm_match.group().upper()
                                break
                    
                    # Also check for AM/PM that might be attached to other text
                    if not ampm:
                        for j in range(max(0, i-1), min(len(texts), i+4)):
                            if j != i:
                                # Look for AM/PM even if attached to other characters
                                ampm_match = re.search(r"(AM|PM)", texts[j], re.IGNORECASE)
                                if ampm_match:
                                    ampm = ampm_match.group().upper()
                                    break

                # Return the complete datetime if we have all components
                if date and time and ampm:
                    return date, f"{time} {ampm}"
                
                # If we have date and time but no AM/PM, still try to return it
                # (some timestamps might be in 24-hour format)
                elif date and time:
                    # Check if it looks like 24-hour format (hours > 12)
                    hour_match = re.match(r"(\d{1,2}):", time)
                    if hour_match and int(hour_match.group(1)) > 12:
                        return date, time  # Return without AM/PM for 24-hour format
                    elif hour_match and int(hour_match.group(1)) <= 12:
                        # For 12-hour format without AM/PM, we can't be sure, so skip
                        continue
        
        return None
    
    def extract_datetime_from_frame(self, image):
        """
        Extract datetime from video frame using OCR
        
        Args:
            image: Input video frame
        
        Returns:
            tuple: (date, time, ocr_texts) or (None, None, ocr_texts)
        """
        # Crop bottom part of image where timestamp appears
        cropped = self.crop_bottom_10_percent(image)
        
        # Perform OCR
        ocr_results = self.reader.readtext(cropped)
        ocr_texts = [text for (_, text, _) in ocr_results]
        
        # Extract datetime
        datetime_result = self.extract_datetime_from_ocr_results(ocr_results)
        
        if datetime_result:
            date, time = datetime_result
            return date, time, ocr_texts
        else:
            return None, None, ocr_texts