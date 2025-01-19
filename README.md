# vcard3-to-vcard4
VCARD 3.0 to 4.0 Converter

A quick hack to convert Apple Contacts (VCARD 3.0) exports to VCARD 4.0 format for importing into Google Contacts. This script helps migrate contacts from Apple to Google by cleaning up Apple-specific fields and ensuring better compatibility with Google's contact import system.

## Features
- Converts VCARD 3.0 to 4.0 format
- Removes Apple-specific fields
- Handles organization contacts correctly
- Optional removal of photos and formatted names
- Preserves essential contact information

## Usage
1. Export your contacts from Apple Contacts:
   - Open Contacts app on your Mac
   - Select the contacts you want to export
   - Go to File > Export > Export vCard...
   - Save as 'contacts.vcf' in the same folder as this script
2. Run the script
3. Import the converted file (contacts_v4.vcf) into Google Contacts
