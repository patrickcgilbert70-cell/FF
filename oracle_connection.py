#!/usr/bin/env python3
"""
Oracle Database Connection Script
Connects to Oracle database and reports connection status
"""

import sys
import getpass

try:
    import oracledb
except ImportError:
    print("Error: oracledb module not found.")
    print("Please install it using: pip install oracledb")
    sys.exit(1)


def connect_to_oracle():
    """
    Connect to Oracle database and report connection status
    """
    # Database connection parameters
    hostname = "dcmpgwm04-cl.edc.nam.gm.com"
    port = 1521  # Default Oracle port
    service_name = "gwmtkpd_srv.edc.nam.gm.com"

    # Prompt for credentials
    print("Oracle Database Connection")
    print(f"Hostname: {hostname}")
    print(f"Service Name: {service_name}")
    print("-" * 50)

    username = input("Enter username: ").strip()
    if not username:
        print("Error: Username cannot be empty")
        return

    password = getpass.getpass("Enter password: ")
    if not password:
        print("Error: Password cannot be empty")
        return

    # Construct DSN (Data Source Name)
    dsn = oracledb.makedsn(hostname, port, service_name=service_name)

    print("\nAttempting to connect to Oracle database...")

    try:
        # Attempt connection
        connection = oracledb.connect(
            user=username,
            password=password,
            dsn=dsn
        )

        # Connection successful
        print("\n✓ Connection SUCCESSFUL!")
        print(f"Connected to Oracle Database: {connection.version}")

        # Close the connection
        connection.close()
        print("Connection closed.")

    except oracledb.Error as error:
        # Connection failed
        print("\n✗ Connection FAILED!")
        print(f"Error: {error}")

        # Provide more detailed error information if available
        error_obj, = error.args
        if hasattr(error_obj, 'code'):
            print(f"Error Code: {error_obj.code}")
        if hasattr(error_obj, 'message'):
            print(f"Error Message: {error_obj.message}")

    except Exception as error:
        print("\n✗ Connection FAILED!")
        print(f"Unexpected error: {error}")


if __name__ == "__main__":
    connect_to_oracle()
