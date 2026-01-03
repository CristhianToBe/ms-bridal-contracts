# notion/client.py
import os
# notion/client.py
import requests
from notion.keys import NOTION_API_KEY, NOTION_VERSION

class NotionError(RuntimeError):
    pass

class NotionClient:
    def __init__(self):
        if not NOTION_API_KEY:
            raise NotionError("NOTION_API_KEY no definido en notion/keys.py")

        self.base_url = "https://api.notion.com/v1"

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def create_page(self, database_id: str, properties: dict) -> dict:
        if not database_id:
            raise NotionError("database_id vacío")

        url = f"{self.base_url}/pages"
        body = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }

        resp = requests.post(url, headers=self.headers, json=body, timeout=30)

        if resp.status_code >= 400:
            raise NotionError(f"Notion error {resp.status_code}: {resp.text}")

        return resp.json()
