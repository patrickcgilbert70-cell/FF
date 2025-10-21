# Oracle Database Connection Script

This repository contains a Python script for connecting to an Oracle database and verifying the connection status.

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
