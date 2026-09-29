"""Copies the Stitch screens into frontend/, injecting recall-connect.js. Re-run after replacing the HTML."""
import pathlib, re, shutil
SRC = pathlib.Path(__file__).parent.parent / "stitch_authentication_flow_wireframes"
OUT = pathlib.Path(__file__).parent / "frontend"
PAGES = {"login": "login_recall", "signup": "sign_up_recall_1", "dashboard": "dashboard_daily_recall_2",
         "review": "recall_review_active_session", "stream": "mem0_recall_stream"}
for name, folder in PAGES.items():
    html = (SRC / folder / "code.html").read_text()
    tag = f'<script src="recall-connect.js" data-page="{name}"></script>'
    html = re.sub(r"</body>", tag + "</body>", html, count=1) if "</body>" in html else html + tag
    (OUT / f"{name}.html").write_text(html)
(OUT / "index.html").write_text('<meta http-equiv="refresh" content="0;url=login.html">')
print("built", ", ".join(PAGES))
