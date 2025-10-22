#!/usr/bin/env python3
"""
Export PRE_APPROVAL_IDs to Excel with hyperlinks to view images
"""

import sys
import getpass
import argparse
from datetime import datetime

try:
    import oracledb
except ImportError:
    print("Error: oracledb module not found.")
    print("Please install it using: pip install oracledb")
    sys.exit(1)

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
except ImportError:
    print("Error: openpyxl module not found.")
    print("Please install it using: pip install openpyxl")
    sys.exit(1)


def export_pre_approvals(username=None, password=None, output_file=None, server_port=5000):
    """
    Export PRE_APPROVAL_IDs to Excel with clickable links

    Args:
        username (str, optional): Database username
        password (str, optional): Database password
        output_file (str, optional): Output Excel file path
        server_port (int): Port where the image viewer server will run
    """
    # Database connection parameters
    hostname = "dcmpgwm04-cl.edc.nam.gm.com"
    port = 1521
    service_name = "gwmtkpd_srv.edc.nam.gm.com"

    # Get credentials
    if username is None:
        username = input("Enter username: ").strip()

    if not username:
        print("Error: Username cannot be empty")
        return

    if password is None:
        password = getpass.getpass("Enter password: ")

    if not password:
        print("Error: Password cannot be empty")
        return

    # Default output file
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"pre_approvals_{timestamp}.xlsx"

    # Construct DSN
    dsn = oracledb.makedsn(hostname, port, service_name=service_name)

    print("\nConnecting to Oracle database...")

    try:
        # Connect to database
        connection = oracledb.connect(
            user=username,
            password=password,
            dsn=dsn
        )

        print("Connected successfully!")

        # Query to get PRE_APPROVAL_IDs
        query = """
        SELECT DISTINCT a.PRE_APPROVAL_ID, a.status, a.pre_approval_request_date
        FROM PRE_APPROVALS a, PRE_APPROVAL_META b
        WHERE a.PRE_APPROVAL_ID = b.PRE_APPROVAL_ID
        AND a.PRE_APPROVAL_REQUEST_DATE > (SYSDATE - 30)
        AND a.status IN ('ACCEPTED', 'REJECTED')
        ORDER BY a.pre_approval_request_date DESC
        """

        cursor = connection.cursor()
        cursor.execute(query)

        # Fetch all results
        results = cursor.fetchall()

        if not results:
            print("No records found.")
            cursor.close()
            connection.close()
            return

        print(f"Found {len(results)} PRE_APPROVAL records")

        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Pre-Approvals"

        # Add headers
        headers = ["PRE_APPROVAL_ID", "Status", "Request Date"]
        ws.append(headers)

        # Style headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')

        # Add data rows with hyperlinks
        for row_idx, row in enumerate(results, start=2):
            pre_approval_id, status, request_date = row

            # Add PRE_APPROVAL_ID as hyperlink
            cell = ws.cell(row=row_idx, column=1)
            cell.value = pre_approval_id
            cell.hyperlink = f"http://localhost:{server_port}/view/{pre_approval_id}"
            cell.font = Font(color="0000FF", underline="single")
            cell.alignment = Alignment(horizontal='left')

            # Add status
            ws.cell(row=row_idx, column=2, value=status)

            # Add request date
            ws.cell(row=row_idx, column=3, value=request_date)

        # Adjust column widths
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 20

        # Save workbook
        wb.save(output_file)

        print(f"\nExcel file created: {output_file}")
        print(f"PRE_APPROVAL_IDs are clickable links that will open the image viewer.")
        print(f"\nIMPORTANT: Make sure to start the image viewer server before clicking links:")
        print(f"  python image_viewer_server.py -u {username} -p <password> -P {server_port}")

        # Close database connection
        cursor.close()
        connection.close()

    except oracledb.Error as error:
        print(f"\nDatabase error: {error}")
        sys.exit(1)

    except Exception as error:
        print(f"\nError: {error}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export PRE_APPROVAL_IDs to Excel with hyperlinks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode:
  python export_pre_approvals.py

  # With username and output file:
  python export_pre_approvals.py -u myusername -o approvals.xlsx

  # Specify server port for links:
  python export_pre_approvals.py -u myusername -P 8080
        """
    )
    parser.add_argument(
        '-u', '--username',
        type=str,
        help='Database username'
    )
    parser.add_argument(
        '-p', '--password',
        type=str,
        help='Database password'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output Excel file path'
    )
    parser.add_argument(
        '-P', '--port',
        type=int,
        default=5000,
        help='Port for image viewer server (default: 5000)'
    )

    args = parser.parse_args()

    export_pre_approvals(
        username=args.username,
        password=args.password,
        output_file=args.output,
        server_port=args.port
    )
