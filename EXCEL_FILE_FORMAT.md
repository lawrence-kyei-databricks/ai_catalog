# Excel File Format Requirements

The CarMax Data Classification Platform requires 2 Excel files with specific column names.

## File 1: Data Elements (e.g., Data_Element_Descriptions.xlsx)

This file contains your 172 CarMax data elements.

### Required Columns:

1. **Data Element Name** (STRING, Required)
   - The name of the data element
   - Example: "Social Security Number", "Email Address", "Phone Number"

2. **Data Category** (STRING, Required)
   - The category this element belongs to
   - Example: "Personal Identifiers", "Contact Information"

3. **Sensitive_Flag** (STRING, Required)
   - Must be exactly "Yes" or "No"
   - Indicates if this is sensitive data

### Optional Columns:

4. **Description** (STRING, Optional)
   - Description of the data element
   - Example: "A unique 9-digit identifier for US citizens"

5. **Data Classification** (STRING, Optional)
   - Classification level
   - Example: "PII", "Confidential", "Public"

### Example Data Elements File:

| Data Element Name | Data Category | Sensitive_Flag | Description | Data Classification |
|------------------|---------------|----------------|-------------|-------------------|
| Social Security Number | Personal Identifiers | Yes | A unique 9-digit identifier | PII |
| Email Address | Contact Information | No | Primary email contact | Internal |
| Phone Number | Contact Information | No | Primary phone contact | Internal |
| Date of Birth | Personal Identifiers | Yes | Customer's birth date | PII |

---

## File 2: Subject Types (e.g., Personal_Data_subject_types.xlsx)

This file contains your 3 data subject types.

### Required Columns:

1. **Data Subject Type Id** (STRING, Required)
   - UUID or unique identifier
   - Example: "aa2dfd55-ffa1-4bc6-b9e6-335564e3d89c"

2. **Data Subject Type Name** (STRING, Required)
   - The name of the subject type
   - Example: "Associate", "B2B", "Consumer"

3. **Description** (STRING, Required)
   - Description of this subject type
   - Example: "Individual customers who interact with CarMax for personal or household purposes"

### Example Subject Types File:

| Data Subject Type Id | Data Subject Type Name | Description |
|---------------------|----------------------|-------------|
| aa2dfd55-ffa1-4bc6-b9e6-335564e3d89c | Associate | Internal personnel (e.g., employees, contractors) |
| 2374b463-0605-4e51-96c1-332addd22e84 | B2B | External business contacts (e.g., vendors, partners) |
| 1fdbd718-31f4-4613-a7ca-6564226a0dbf | Consumer | Individual customers who interact with CarMax for personal or household purposes |

---

## Common Issues

### Issue: "'Data Element Name' not found"
**Cause:** Your Excel column is named differently
**Solution:** Rename the column header to exactly "Data Element Name" (case-sensitive)

### Issue: "'Sensitive_Flag' not found"
**Cause:** Column name doesn't match exactly
**Solution:** Ensure it's named "Sensitive_Flag" with underscore (not "Sensitive Flag" with space)

### Issue: "KeyError: 'Description'"
**Cause:** The Subjects file is missing the Description column
**Solution:** Add a "Description" column to your subjects file

---

## Validation

After you try to upload, the error message will now show:
- What columns were found in your file
- What columns are required
- What columns are missing

This helps you fix your Excel files quickly.

---

## Testing Your Files

Before uploading, you can verify your files have the correct format:

1. Open your Excel file
2. Check the first row (header row) has the exact column names listed above
3. Ensure there are no extra spaces before/after column names
4. Save the file as .xlsx format

---

## Need Help?

If you're still having issues, check the app logs after upload - they will show exactly what columns were found in your files.
