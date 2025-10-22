# Oracle Database Tools

This repository contains Python scripts for working with Oracle database, including:
1. Database connection testing
2. Pre-approval data export to Excel with hyperlinks
3. Web-based image viewer for pre-approval attachments

## Configuration

The script connects to:
- **Hostname**: dcmpgwm04-cl.edc.nam.gm.com
- **Port**: 1521 (default Oracle port)
- **Service Name**: gwmtkpd_srv.edc.nam.gm.com

## Prerequisites

- Python 3.6 or higher
- Oracle Instant Client (optional, depending on your setup)

## Installation

Install all required Python packages:
```bash
pip install -r requirements.txt
```

This installs:
- `oracledb` - Oracle database connectivity
- `openpyxl` - Excel file generation
- `flask` - Web server for image viewer

## Usage

Run the script:
```bash
python oracle_connection.py
```

The script will:
1. Display the connection parameters
2. Prompt you for your username
3. Securely prompt for your password (input will be hidden)
4. Attempt to connect to the Oracle database
5. Report success or failure with detailed error messages

## Example Output

### Successful Connection
```
Oracle Database Connection
Hostname: dcmpgwm04-cl.edc.nam.gm.com
Service Name: gwmtkpd_srv.edc.nam.gm.com
--------------------------------------------------
Enter username: myuser
Enter password:

Attempting to connect to Oracle database...

✓ Connection SUCCESSFUL!
Connected to Oracle Database: 19.0.0.0.0
Connection closed.
```

### Failed Connection
```
Oracle Database Connection
Hostname: dcmpgwm04-cl.edc.nam.gm.com
Service Name: gwmtkpd_srv.edc.nam.gm.com
--------------------------------------------------
Enter username: myuser
Enter password:

Attempting to connect to Oracle database...

✗ Connection FAILED!
Error: ORA-01017: invalid username/password; logon denied
Error Code: 1017
Error Message: ORA-01017: invalid username/password; logon denied
```

## Features

- Secure password input (hidden from display)
- Clear success/failure reporting
- Detailed error messages for troubleshooting
- Automatic connection cleanup

## Security Notes

- Credentials are not stored in the script
- Password input is hidden using `getpass`
- Connection is properly closed after testing

---

## Pre-Approval Image Viewer System

A complete system for exporting pre-approval data and viewing associated images.

### Overview

This system consists of two components:
1. **Excel Exporter** (`export_pre_approvals.py`) - Exports PRE_APPROVAL_IDs to Excel with clickable hyperlinks
2. **Image Viewer Server** (`image_viewer_server.py`) - Flask web server that displays images for each PRE_APPROVAL_ID

### Quick Start

#### Step 1: Start the Image Viewer Server

First, start the web server that will display images:

```bash
python image_viewer_server.py -u your_username -p your_password
```

The server will start on `http://localhost:5000` by default.

#### Step 2: Export Pre-Approvals to Excel

In a separate terminal, export the data:

```bash
python export_pre_approvals.py -u your_username -p your_password
```

This creates an Excel file with PRE_APPROVAL_IDs as clickable hyperlinks.

#### Step 3: View Images

Open the Excel file and click on any PRE_APPROVAL_ID link. Your browser will open and display all associated JPG images.

### Export Pre-Approvals Script

**Purpose**: Query the database for pre-approvals from the last 30 days and export to Excel with clickable links.

**Usage**:
```bash
# Interactive mode (prompts for credentials)
python export_pre_approvals.py

# With username only
python export_pre_approvals.py -u myusername

# With username and custom output file
python export_pre_approvals.py -u myusername -o my_approvals.xlsx

# Specify custom port for image viewer
python export_pre_approvals.py -u myusername -P 8080
```

**Output**: Excel file with columns:
- PRE_APPROVAL_ID (clickable hyperlink)
- Status (ACCEPTED/REJECTED)
- Request Date

### Image Viewer Server

**Purpose**: Web server that displays all JPG images for a given PRE_APPROVAL_ID.

**Usage**:
```bash
# Interactive mode
python image_viewer_server.py

# With credentials
python image_viewer_server.py -u myusername -p mypassword

# Custom port and host
python image_viewer_server.py -u myusername -p mypassword -P 8080 --host 0.0.0.0
```

**Features**:
- Displays all images in a responsive grid layout
- Shows metadata (status, request date, filename)
- Handles BLOB images from database
- Clean, professional web interface

**Direct Access**:
You can also access images directly via URL:
```
http://localhost:5000/view/YOUR_PRE_APPROVAL_ID
```

### Database Query

The system uses this query to fetch images:
```sql
SELECT a.PRE_APPROVAL_ID, c.PRE_APPROVAL_ATTACHMENT, b.FILENAME,
       a.status, a.pre_approval_request_date
FROM PRE_APPROVALS a, PRE_APPROVAL_META b, pre_approval_attachment_data3 c
WHERE a.PRE_APPROVAL_ID = b.PRE_APPROVAL_ID
AND b.PRE_APPROVAL_ATTACHMENT_ID = c.PRE_APPROVAL_ATTACHMENT_ID
AND a.PRE_APPROVAL_REQUEST_DATE > (SYSDATE - 30)
AND UPPER(b.FILENAME) LIKE '%JPG%'
AND a.status IN ('ACCEPTED', 'REJECTED')
AND a.PRE_APPROVAL_ID = :pre_approval_id
```

**Filters**:
- Last 30 days only
- Status: ACCEPTED or REJECTED
- File type: JPG only

### Workflow Example

```bash
# Terminal 1: Start the image viewer server
$ python image_viewer_server.py -u john_doe -p mypassword
Testing database connection...
Database connection successful!

Starting image viewer server on http://localhost:5000
Server is ready to display images!

# Terminal 2: Export data to Excel
$ python export_pre_approvals.py -u john_doe -p mypassword

Connecting to Oracle database...
Connected successfully!
Found 25 PRE_APPROVAL records

Excel file created: pre_approvals_20250101_120000.xlsx
PRE_APPROVAL_IDs are clickable links that will open the image viewer.

# Now open the Excel file and click any PRE_APPROVAL_ID link
```

### Troubleshooting

**Port already in use:**
```bash
python image_viewer_server.py -u username -p password -P 8080
python export_pre_approvals.py -u username -p password -P 8080
```

**No images displayed:**
- Check that the PRE_APPROVAL_ID has JPG attachments
- Verify the pre-approval is within the last 30 days
- Confirm status is ACCEPTED or REJECTED

**Database connection errors:**
- Verify credentials are correct
- Check network connectivity to database server
- Ensure Oracle client libraries are installed

### Command-Line Arguments

#### export_pre_approvals.py
- `-u, --username`: Database username
- `-p, --password`: Database password
- `-o, --output`: Output Excel file path
- `-P, --port`: Port for image viewer server links (default: 5000)

#### image_viewer_server.py
- `-u, --username`: Database username
- `-p, --password`: Database password
- `-P, --port`: Server port (default: 5000)
- `--host`: Host to bind to (default: localhost)
