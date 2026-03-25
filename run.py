import os
import sys

# Ensure the root directory is accessible to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
