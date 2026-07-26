# Oracle Database Scripts

This repository contains Python scripts for working with Oracle databases, including connection testing and pre-approval data export.

It also contains the **Game Camera Summary** tool — see below.

## Configuration

The script connects to:
- **Hostname**: dcmpgwm04-cl.edc.nam.gm.com
- **Port**: 1521 (default Oracle port)
- **Service Name**: gwmtkpd_srv.edc.nam.gm.com

## Prerequisites

- Python 3.6 or higher
- Oracle Instant Client (optional, depending on your setup)

## Installation

1. Install the required Python package:
```bash
pip install -r requirements.txt
```

Or install directly:
```bash
pip install oracledb
```

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

# Pre-Approvals Export Script

The `export_pre_approvals.py` script exports pre-approval data from the Oracle database to an Excel file with embedded images.

## Features

- Exports pre-approval records from the last 90 days
- Includes all required columns: Pre-Approval ID, Status, Request Date, Trouble Code Text, Correction Text, and Comment Text
- Embeds JPG images associated with each pre-approval
- Filters by specific labor operation codes
- Only includes ACCEPTED or REJECTED statuses

## Usage

### Interactive Mode
```bash
python export_pre_approvals.py
```

### With Command-Line Arguments
```bash
# With username only (prompts for password):
python export_pre_approvals.py -u myusername

# With username and password:
python export_pre_approvals.py -u myusername -p mypassword

# With custom output file:
python export_pre_approvals.py -u myusername -p mypassword -o custom_output.xlsx
```

## Output

The script creates an Excel file (default: `pre_approvals_with_images.xlsx`) containing:
- All pre-approval records matching the criteria
- Embedded JPG images for each pre-approval ID
- Properly formatted columns with appropriate widths
- Auto-sized rows to accommodate images

## Query Details

The script executes a query that:
- Joins `pre_approvals` and `pre_approval_comments` tables
- Filters records from the last 90 days
- Includes only ACCEPTED or REJECTED statuses
- Filters by specific labor operation codes
- Orders by request date (descending) and sequence ID

Images are fetched from the `pre_approval_attachment_data3` table based on the pre-approval ID.

---

# Game Camera Summary

The `game_camera_summary.py` script analyzes a folder of game/trail camera photos and
produces a daily activity summary.

For each photo, it uses Claude vision (Anthropic API) to read the date/time stamp the
camera burns into the image and to count animals present: pigs, turkeys, female doe,
male bucks, and cows. Results are cached locally (`analysis_cache.json` in the input
folder by default) so re-running the script only analyzes new photos.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-api-key-here
```

## Usage

```bash
python game_camera_summary.py --input "C:\Beave\Files\Investments\Real Estate\235 Antler Lane Rocky Hollow Lot 65\Pics\Analyze"
```

Optional arguments:
- `--output` — path for the markdown report (default: `game_camera_summary.md`)
- `--cache` — path for the analysis cache JSON (default: `analysis_cache.json` inside the input folder)
- `--model` — Claude model to use for vision analysis (default: `claude-haiku-4-5-20251001`)
- `--workers` — number of concurrent API requests (default: 4)
- `--api-key` — Anthropic API key (defaults to the `ANTHROPIC_API_KEY` environment variable)

## Report Contents

- **Overall summary**: total pictures and counts of pigs, turkeys, female doe, male
  bucks, and cows across all photos analyzed.
- **Per-day breakdown**, for each day:
  - Total pictures and the same species counts, for that day
  - First time a pig was spotted
  - First time a pig was spotted after 6:00 PM
  - The photo with the most pigs, and the count
