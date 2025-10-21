#!/usr/bin/env python3
"""
Oracle Database Connection Script
Connects to Oracle database, runs query, and saves results to CSV file
"""

import sys
import getpass
import csv
from datetime import datetime
from pathlib import Path

try:
    import oracledb
except ImportError:
    print("Error: oracledb module not found.")
    print("Please install it using: pip install oracledb")
    sys.exit(1)


def connect_to_oracle():
    """
    Connect to Oracle database, run query, and save results to CSV file
    """
    # Database connection parameters
    hostname = "dcmpgwm04-cl.edc.nam.gm.com"
    port = 1521  # Default Oracle port
    service_name = "gwmtkpd_srv.edc.nam.gm.com"

    # SQL Query
    query = """
    select a.pre_approval_id, a.system_id, a.status, a.trouble_cd_text,
           a.correction_text, b.comment_text
    from dbo.pre_approvals a, dbo.pre_approval_comments b
    where a.pre_approval_id = b.pre_approval_id
    and upper(a.correction_text) like '%SEAT%'
    and a.PRE_APPROVAL_REQUEST_DATE > (Sysdate-2)
    order by a.PRE_APPROVAL_REQUEST_DATE desc, b.sequence_id
    """

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

        # Create cursor and execute query
        print("\nExecuting query...")
        cursor = connection.cursor()
        cursor.execute(query)

        # Fetch all results
        rows = cursor.fetchall()

        # Get column names
        column_names = [desc[0] for desc in cursor.description]

        print(f"✓ Query executed successfully! Found {len(rows)} rows.")

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"query_results_{timestamp}.csv"

        # Get the script directory
        script_dir = Path(__file__).parent
        filepath = script_dir / filename

        # Write results to CSV file
        print(f"\nWriting results to: {filepath}")
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write header
            csv_writer.writerow(column_names)

            # Write data rows
            csv_writer.writerows(rows)

        print(f"✓ Results saved successfully to: {filename}")
        print(f"Total rows written: {len(rows)}")

        # Close cursor and connection
        cursor.close()
        connection.close()
        print("\nConnection closed.")

    except oracledb.Error as error:
        # Connection or query failed
        print("\n✗ Operation FAILED!")
        print(f"Error: {error}")

        # Provide more detailed error information if available
        error_obj, = error.args
        if hasattr(error_obj, 'code'):
            print(f"Error Code: {error_obj.code}")
        if hasattr(error_obj, 'message'):
            print(f"Error Message: {error_obj.message}")

    except Exception as error:
        print("\n✗ Operation FAILED!")
        print(f"Unexpected error: {error}")


if __name__ == "__main__":
    connect_to_oracle()
