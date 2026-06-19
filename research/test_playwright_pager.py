#!/usr/bin/env python3
import re
import html as h
from playwright.sync_api import sync_playwright


def parse_cards(html: str) -> dict[str, str]:
    cards: dict[str, str] = {}
    pattern = re.compile(
        r'<h3[^>]*class="[^"]*elementor-heading-title[^"]*"[^>]*>(.*?)</h3>(.*?)(?=<h3[^>]*class="[^"]*elementor-heading-title|$)',
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(html):
        title = h.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()
        if any(x in title for x in ("Filtrar", "Enlaces", "Sedes", "Querés")):
            continue
        if re.search(r"google\.com/maps", match.group(2), re.I):
            cards[title.casefold()] = title
    return cards


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://osmedica.com.ar/cartilla/", wait_until="load", timeout=120_000)
        page.wait_for_function(
            "() => typeof FWP !== 'undefined' && FWP.settings?.pager?.total_pages > 0",
            timeout=90_000,
        )
        page.wait_for_timeout(2000)
        info = page.evaluate(
            "() => ({ total: FWP.settings.pager.total_pages, per: FWP.settings.pager.per_page })"
        )
        print("pager", info)
        for paged in (1, 2, 5, 10):
            html = page.evaluate(
                """(paged) => new Promise((resolve) => {
                    let settled = false;
                    const finish = () => {
                        if (settled) return;
                        settled = true;
                        const tpl = document.querySelector('.facetwp-template');
                        resolve(tpl ? tpl.innerHTML : '');
                    };
                    document.addEventListener('facetwp-loaded', finish, { once: true });
                    FWP.paged = paged;
                    FWP.soft_refresh = 1;
                    FWP.refresh();
                    setTimeout(finish, 25000);
                })""",
                paged,
            )
            cards = parse_cards(html)
            print(f"page {paged}: {len(cards)} cards", list(cards.values())[:2])
        browser.close()


if __name__ == "__main__":
    main()
