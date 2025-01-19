"""
Quick hack to convert Apple Contacts (VCARD 3.0) exports to VCARD 4.0 format
for importing into Google Contacts. This script handles Apple-specific fields
and formatting to ensure better compatibility with Google Contacts import.

Key features:
- Properly converts organization contacts (marked with X-ABShowAs:COMPANY in Apple)
  to use KIND:org in VCARD 4.0, ensuring they appear as companies on mobile devices
- Cleans up Apple-specific fields (X-APPLE-, X-ABADR, X-ABLabel)
- Normalizes address (ADR) and phone (TEL) formatting
"""

import re
import json
import os

def get_user_settings():
    config_file = 'vcard_settings.json'
    
    # Check if settings file exists
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    
    # If not, ask for settings
    print("\nFirst time setup - Please configure your preferences:")
    print("(Press Enter for default values)")
    remove_fn = input("Remove FN (Formatted Name) field? (yes/no) [yes]: ").lower()
    remove_fn = remove_fn in ['', 'yes', 'y']
    
    remove_photos = input("Remove embedded photos? (yes/no) [yes]: ").lower()
    remove_photos = remove_photos in ['', 'yes', 'y']
    
    # Save settings
    settings = {
        'remove_fn': remove_fn,
        'remove_photos': remove_photos
    }
    
    with open(config_file, 'w') as f:
        json.dump(settings, f, indent=4)
    
    return settings

def convert_vcard_3_to_4(input_text, settings):
    # Split into individual vcards more reliably
    vcards = []
    current_vcard = []
    lines = input_text.strip().split('\n')
    
    for line in lines:
        if line.startswith('BEGIN:VCARD'):
            if current_vcard:  # If we have a previous card, save it
                if not current_vcard[-1].startswith('END:VCARD'):
                    current_vcard.append('END:VCARD')
                vcards.append('\n'.join(current_vcard))
            current_vcard = [line]  # Start new card
        elif current_vcard is not None:
            current_vcard.append(line)
    
    # Add the last card if there is one
    if current_vcard:
        if not current_vcard[-1].startswith('END:VCARD'):
            current_vcard.append('END:VCARD')
        vcards.append('\n'.join(current_vcard))
    
    converted_vcards = []
    
    for vcard in vcards:
        if not vcard.strip():
            continue
            
        # Split into lines for processing
        lines = vcard.strip().split('\n')
        new_lines = ['BEGIN:VCARD']  # Always start with BEGIN:VCARD
        kind_added = False
        skip_photo = False
        
        # Check if this is an organization by examining N and X-ABShowAs fields
        is_org = False
        has_x_abshowas_company = any(line.startswith('X-ABShowAs:COMPANY') for line in lines)
        n_field = next((line for line in lines if line.startswith('N:')), '')
        n_parts = n_field.split(':')[1].split(';') if n_field else []
        has_empty_n = all(not part.strip() for part in n_parts)
        
        if has_x_abshowas_company or (has_empty_n and any(line.startswith('ORG:') for line in lines)):
            is_org = True
        
        for line in lines:
            # Skip empty lines and BEGIN:VCARD
            if not line.strip() or line.startswith('BEGIN:VCARD'):
                continue
            
            # Handle multi-line PHOTO field
            if settings['remove_photos']:
                if line.startswith('PHOTO;'):
                    skip_photo = True
                    continue
                if skip_photo:
                    if line.startswith(' ') or re.match(r'^[A-Za-z0-9+/=]', line):
                        continue
                    skip_photo = False
            
            # Skip FN field if configured
            if settings['remove_fn'] and line.startswith('FN:'):
                continue
            
            # Skip Apple PRODID
            if line.startswith('PRODID:-//Apple Inc.//'):
                continue
                
            # Update version
            if line.startswith('VERSION:'):
                new_lines.append('VERSION:4.0')
                continue
                
            # Handle X-ABShowAs:COMPANY
            if line.startswith('X-ABShowAs:COMPANY'):
                continue  # Skip this line, we already determined if it's an org
                
            # Update ADR format
            if 'ADR' in line:
                line = re.sub(r'item\d+\.ADR', 'ADR', line)
                line = re.sub(r'type=([^;]+)', r'TYPE=\1', line, flags=re.IGNORECASE)
                
            # Update TEL format
            if line.startswith('TEL;'):
                line = re.sub(r'type=([^;]+)', r'TYPE=\1', line, flags=re.IGNORECASE)
                # Normalize phone number format (optional)
                # phone_part = line.split(':')[1]
                # phone_clean = re.sub(r'[\s-]', '', phone_part)
                # line = f"{line.split(':')[0]}:{phone_clean}"
                
            # Update EMAIL format
            if line.startswith('EMAIL;'):
                line = re.sub(r'type=([^;]+)', r'TYPE=\1', line, flags=re.IGNORECASE)
                
            # Update URL format
            if line.startswith('item'):
                line = re.sub(r'item\d+\.URL', 'URL', line)
                
            # Clean up N field with empty components
            if line.startswith('N:'):
                parts = line.split(':')[1].split(';')
                # Remove trailing empty components
                while parts and not parts[-1]:
                    parts.pop()
                line = 'N:' + ';'.join(parts + [''] * (5 - len(parts)))
                
            # Remove Apple-specific fields
            if any(x in line for x in ['X-APPLE-', 'X-ABADR:', 'X-ABLabel:']):
                continue
                
            new_lines.append(line)
        
        # Add KIND:org if this is an organization
        if is_org:
            version_index = next(i for i, line in enumerate(new_lines) if line.startswith('VERSION:'))
            new_lines.insert(version_index + 1, 'KIND:org')
        
        # Make sure we end with END:VCARD
        if not new_lines[-1].startswith('END:VCARD'):
            new_lines.append('END:VCARD')
        
        converted_vcards.append('\n'.join(new_lines))
    
    return '\n\n'.join(converted_vcards)

def main():
    # Get or create settings
    settings = get_user_settings()
    
    # Define input/output files
    input_file = 'contacts.vcf'
    output_file = 'contacts_v4.vcf'
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print("\nError: contacts.vcf not found!")
        print("Please place your Apple Contacts export (contacts.vcf) in the same folder as this script.")
        print("\nHow to export contacts from Apple Contacts:")
        print("1. Open Contacts app on your Mac")
        print("2. Select the contacts you want to export")
        print("3. Go to File > Export > Export vCard...")
        print("4. Save as 'contacts.vcf' in the same folder as this script")
        return
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            input_text = f.read()
        
        converted_text = convert_vcard_3_to_4(input_text, settings)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(converted_text)
            
        print(f"\nSuccessfully converted {input_file} to VCARD 4.0 format")
        print(f"Output saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    main()