import os


NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")
NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"


def get_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }
