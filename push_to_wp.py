import os, json, glob
import requests
from dotenv import load_dotenv

load_dotenv()

SITE = os.getenv("SITE")
WP_USER = os.getenv("WP_USER")
WP_APP_PASS = os.getenv("WP_APP_PASS")

if not all([SITE, WP_USER, WP_APP_PASS]):
    raise SystemExit("ERROR: .env の SITE / WP_USER / WP_APP_PASS を設定してください")

session = requests.Session()
session.auth = (WP_USER, WP_APP_PASS)

POSTS_API = f"{SITE}/wp-json/wp/v2/posts"
ACF_API   = f"{SITE}/wp-json/frebull/v1/acf"

def post_draft(title: str, content_html: str) -> int:
    payload = {"title": title, "content": content_html, "status": "draft"}
    r = session.post(POSTS_API, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["id"]

def update_acf(post_id: int, article_description: str):
    payload = {"post_id": post_id, "article_description": article_description}
    r = session.post(ACF_API, json=payload, timeout=60)
    r.raise_for_status()

def main():
    files = sorted(glob.glob("drafts/*.json"))
    if not files:
        print("drafts/*.json がありません。先にテスト記事JSONを作ってください。")
        return

    os.makedirs("logs", exist_ok=True)
    log_path = "logs/push_log.jsonl"

    with open(log_path, "a", encoding="utf-8") as logf:
        for fp in files:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)

            title = data["title"]
            content_html = data["content_html"]
            article_description = data.get("article_description", "").strip()

            post_id = post_draft(title, content_html)
            if article_description:
                update_acf(post_id, article_description)

            out = {"file": fp, "post_id": post_id, "title": title}
            logf.write(json.dumps(out, ensure_ascii=False) + "\n")
            print(f"OK: {title} -> post_id={post_id}")

if __name__ == "__main__":
    main()
