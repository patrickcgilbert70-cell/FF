#!/usr/bin/env python3
"""
Flask web server to view images for PRE_APPROVAL_IDs
Displays BLOB images from Oracle database
"""

import sys
import getpass
import argparse
import base64
from io import BytesIO

try:
    import oracledb
except ImportError:
    print("Error: oracledb module not found.")
    print("Please install it using: pip install oracledb")
    sys.exit(1)

try:
    from flask import Flask, render_template_string, abort
except ImportError:
    print("Error: flask module not found.")
    print("Please install it using: pip install flask")
    sys.exit(1)

# Database configuration (global for Flask routes)
DB_CONFIG = {
    'hostname': "dcmpgwm04-cl.edc.nam.gm.com",
    'port': 1521,
    'service_name': "gwmtkpd_srv.edc.nam.gm.com",
    'username': None,
    'password': None
}

app = Flask(__name__)


def get_db_connection():
    """Create and return a database connection"""
    dsn = oracledb.makedsn(
        DB_CONFIG['hostname'],
        DB_CONFIG['port'],
        service_name=DB_CONFIG['service_name']
    )

    connection = oracledb.connect(
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        dsn=dsn
    )

    return connection


def get_images_for_pre_approval(pre_approval_id):
    """
    Fetch all images for a given PRE_APPROVAL_ID

    Args:
        pre_approval_id: The PRE_APPROVAL_ID to fetch images for

    Returns:
        List of dictionaries containing image data and metadata
    """
    query = """
    SELECT a.PRE_APPROVAL_ID, c.PRE_APPROVAL_ATTACHMENT, b.FILENAME,
           a.status, a.pre_approval_request_date
    FROM PRE_APPROVALS a, PRE_APPROVAL_META b, pre_approval_attachment_data3 c
    WHERE a.PRE_APPROVAL_ID = b.PRE_APPROVAL_ID
    AND b.PRE_APPROVAL_ATTACHMENT_ID = c.PRE_APPROVAL_ATTACHMENT_ID
    AND a.PRE_APPROVAL_REQUEST_DATE > (SYSDATE - 30)
    AND UPPER(b.FILENAME) LIKE '%JPG%'
    AND a.status IN ('ACCEPTED', 'REJECTED')
    AND a.PRE_APPROVAL_ID = :pre_approval_id
    ORDER BY b.FILENAME
    """

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(query, {'pre_approval_id': pre_approval_id})
        results = cursor.fetchall()

        images = []
        for row in results:
            pre_id, blob_data, filename, status, request_date = row

            # Convert BLOB to base64 for HTML display
            if blob_data:
                # Read BLOB data
                blob_bytes = blob_data.read()

                # Convert to base64
                base64_image = base64.b64encode(blob_bytes).decode('utf-8')

                images.append({
                    'pre_approval_id': pre_id,
                    'filename': filename,
                    'status': status,
                    'request_date': request_date,
                    'base64_data': base64_image
                })

        return images

    finally:
        cursor.close()
        connection.close()


# HTML template for displaying images
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pre-Approval Images - {{ pre_approval_id }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #333;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .header h1 {
            margin: 0;
        }
        .info {
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .info-row {
            margin: 5px 0;
        }
        .label {
            font-weight: bold;
            display: inline-block;
            width: 150px;
        }
        .images-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .image-card {
            background-color: white;
            border-radius: 5px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .image-card img {
            width: 100%;
            height: auto;
            border-radius: 3px;
            border: 1px solid #ddd;
        }
        .filename {
            margin-top: 10px;
            font-weight: bold;
            color: #333;
            text-align: center;
        }
        .no-images {
            background-color: white;
            padding: 40px;
            text-align: center;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .status-accepted {
            color: green;
            font-weight: bold;
        }
        .status-rejected {
            color: red;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Pre-Approval Images</h1>
    </div>

    {% if images %}
    <div class="info">
        <div class="info-row">
            <span class="label">PRE_APPROVAL_ID:</span>
            <span>{{ images[0].pre_approval_id }}</span>
        </div>
        <div class="info-row">
            <span class="label">Status:</span>
            <span class="status-{{ images[0].status.lower() }}">{{ images[0].status }}</span>
        </div>
        <div class="info-row">
            <span class="label">Request Date:</span>
            <span>{{ images[0].request_date }}</span>
        </div>
        <div class="info-row">
            <span class="label">Total Images:</span>
            <span>{{ images|length }}</span>
        </div>
    </div>

    <div class="images-container">
        {% for image in images %}
        <div class="image-card">
            <img src="data:image/jpeg;base64,{{ image.base64_data }}"
                 alt="{{ image.filename }}">
            <div class="filename">{{ image.filename }}</div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="no-images">
        <h2>No Images Found</h2>
        <p>No images found for PRE_APPROVAL_ID: {{ pre_approval_id }}</p>
        <p>This could mean:</p>
        <ul style="text-align: left; display: inline-block;">
            <li>No JPG images are attached to this pre-approval</li>
            <li>The pre-approval is older than 30 days</li>
            <li>The status is not ACCEPTED or REJECTED</li>
        </ul>
    </div>
    {% endif %}
</body>
</html>
"""


@app.route('/')
def index():
    """Home page"""
    return """
    <html>
    <head>
        <title>Pre-Approval Image Viewer</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 40px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
            }
            code {
                background-color: #f0f0f0;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Pre-Approval Image Viewer</h1>
            <p>This server displays images for PRE_APPROVAL_IDs from the Oracle database.</p>
            <h3>Usage:</h3>
            <p>Click on PRE_APPROVAL_ID links in the Excel file to view images.</p>
            <p>Direct URL format: <code>http://localhost:5000/view/&lt;PRE_APPROVAL_ID&gt;</code></p>
            <h3>Status:</h3>
            <p style="color: green; font-weight: bold;">Server is running ✓</p>
        </div>
    </body>
    </html>
    """


@app.route('/view/<pre_approval_id>')
def view_images(pre_approval_id):
    """Display all images for a given PRE_APPROVAL_ID"""
    try:
        images = get_images_for_pre_approval(pre_approval_id)

        return render_template_string(
            HTML_TEMPLATE,
            pre_approval_id=pre_approval_id,
            images=images
        )

    except oracledb.Error as error:
        return f"""
        <html>
        <body style="font-family: Arial; margin: 40px;">
            <h1>Database Error</h1>
            <p>Error fetching images for PRE_APPROVAL_ID: {pre_approval_id}</p>
            <p>Error details: {error}</p>
        </body>
        </html>
        """, 500

    except Exception as error:
        return f"""
        <html>
        <body style="font-family: Arial; margin: 40px;">
            <h1>Error</h1>
            <p>Unexpected error: {error}</p>
        </body>
        </html>
        """, 500


def main():
    parser = argparse.ArgumentParser(
        description="Flask server to view PRE_APPROVAL images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server (prompts for credentials):
  python image_viewer_server.py

  # Start with username and password:
  python image_viewer_server.py -u myusername -p mypassword

  # Specify port:
  python image_viewer_server.py -u myusername -p mypassword -P 8080

  # Access in browser:
  http://localhost:5000/view/YOUR_PRE_APPROVAL_ID
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
        '-P', '--port',
        type=int,
        default=5000,
        help='Port to run server on (default: 5000)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Host to bind to (default: localhost)'
    )

    args = parser.parse_args()

    # Get credentials
    if args.username is None:
        username = input("Enter database username: ").strip()
    else:
        username = args.username

    if not username:
        print("Error: Username cannot be empty")
        sys.exit(1)

    if args.password is None:
        password = getpass.getpass("Enter database password: ")
    else:
        password = args.password

    if not password:
        print("Error: Password cannot be empty")
        sys.exit(1)

    # Store credentials in global config
    DB_CONFIG['username'] = username
    DB_CONFIG['password'] = password

    # Test database connection
    print("\nTesting database connection...")
    try:
        connection = get_db_connection()
        print("Database connection successful!")
        connection.close()
    except Exception as error:
        print(f"Error: Could not connect to database: {error}")
        sys.exit(1)

    # Start Flask server
    print(f"\nStarting image viewer server on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")
    print("\nServer is ready to display images!")

    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
