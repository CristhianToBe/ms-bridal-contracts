"""
ASGI config for webui project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import sys
from pathlib import Path
from django.core.asgi import get_asgi_application

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # .../dossier-builder-main
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webui.settings')
application = get_asgi_application()
