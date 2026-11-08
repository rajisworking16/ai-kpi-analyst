"""Capture README screenshots of the running Streamlit app with headless Chromium.

Start the app first: streamlit run app/streamlit_app.py --server.headless true --server.port 8599
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "img"


def main(run_id: str, month: str, port: int = 8599) -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    url = f"http://localhost:{port}/?run={run_id}&month={month}"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 1000})
        page.goto(url)
        page.get_by_text("3. Agent trace").wait_for(timeout=60000)
        page.get_by_text("Summary.").wait_for(timeout=60000)
        page.wait_for_timeout(3000)
        page.screenshot(path=str(IMG / "app_overview.png"))
        expanders = page.locator("[data-testid='stExpander'] summary")
        if expanders.count():
            expanders.first.click()
            page.wait_for_timeout(1500)
        page.get_by_text("3. Agent trace").scroll_into_view_if_needed()
        page.evaluate("window.scrollBy(0, -20)")
        page.wait_for_timeout(1000)
        main_area = page.locator("[data-testid='stMain']")
        main_area.screenshot(path=str(IMG / "full_page.png"))
        trace = page.get_by_text("3. Agent trace")
        box = trace.bounding_box()
        page.screenshot(path=str(IMG / "agent_trace.png"), full_page=True,
                        clip={"x": 0, "y": box["y"] + page.evaluate("window.scrollY") - 10,
                              "width": 1400, "height": 1100})
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "example_2018-03_revenue",
         sys.argv[2] if len(sys.argv) > 2 else "2018-03")
