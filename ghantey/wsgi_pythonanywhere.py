"""
WSGI config for PythonAnywhere deployment.

Point this file in the PythonAnywhere Web dashboard:
  WSGI configuration file → /home/<username>/ghantey/ghantey/wsgi_pythonanywhere.py
"""

import os
import sys
from pathlib import Path

# Ensure the project directory is on the Python path
project_home = os.path.expanduser('~/ghantey')
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ghantey.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
