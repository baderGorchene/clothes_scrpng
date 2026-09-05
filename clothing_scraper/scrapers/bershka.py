import json
import random
import re
import time
import logging

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


def scrape_bershka_tshirts(
    url: str, output_filename: str = "bershka_tshirts_scraped_data.jsonl"
):
    """Scrape Bershka t-shirts from a category page and save results as JSONL.

    Args:
        url: category page URL to scrape
        output_filename: output .jsonl filename
    Returns:
        Number of products saved (int)
    """
    # Ensure output file exists and is cleared
    with open(output_filename, "w", encoding="utf-8") as f:
        pass

    products_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False  # change to True for headless runs
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        logger.info(f"Navigating to category page: {url}...")
        page.goto(url, wait_until="load")

        # Cookie consent handling
        try:
            cookie_accept_button = page.locator(
                'button:has-text("Accept cookies"), button:has-text("Accepter"), #onetrust-accept-btn-handler'
            )
            if cookie_accept_button.is_visible(timeout=5000):
                logger.info("Cookie consent banner detected. Attempting to accept.")
                cookie_accept_button.click()
                page.wait_for_load_state("networkidle")
                time.sleep(1)
            else:
                logger.debug("No cookie consent banner detected or already dismissed.")
        except Exception as e:
            logger.warning(f"Error handling cookie consent: {e}. Proceeding.")

        clickable_product_selector = "li.grid-item > div > a"

        try:
            page.wait_for_selector(clickable_product_selector, timeout=30000)
            logger.info(
                f"Successfully found at least one product link using '{clickable_product_selector}'."
            )
        except Exception as e:
            logger.error(f"CRITICAL: Initial wait for product links failed: {e}")
            logger.error(
                f"Please manually inspect '{url}' with F12 and confirm the CSS selector for the clickable link on each product card."
            )
            browser.close()
            return 0

        logger.info("Attempting to human-like scroll to load all products on the category page...")
        last_product_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 50

        footer_selector = "div.esi-wrapper:nth-child(7)"

        scroll_increment_min = 200
        scroll_increment_max = 400
        scroll_pause_min = 0.5
        scroll_pause_max = 1.5

        while scroll_attempts < max_scroll_attempts:
            try:
                footer_locator = page.locator(footer_selector)
                if footer_locator.is_visible():
                    footer_bounding_box = footer_locator.bounding_box()
                    if footer_bounding_box and footer_bounding_box["y"] < page.evaluate(
                        "window.innerHeight"
                    ):
                        logger.info("Footer is visible and assumed all products loaded. Breaking scroll loop.")
                        all_clickable_product_elements = page.query_selector_all(
                            clickable_product_selector
                        )
                        current_count = len(all_clickable_product_elements)
                        logger.debug(f"Final count before breaking due to footer visibility: {current_count}")
                        break
            except Exception:
                pass

            scroll_amount = random.randint(scroll_increment_min, scroll_increment_max)
            logger.debug(f"Scrolling down by {scroll_amount} pixels...")
            page.evaluate(f"window.scrollBy(0, {scroll_amount})")

            pause_duration = random.uniform(scroll_pause_min, scroll_pause_max)
            time.sleep(pause_duration)

            all_clickable_product_elements = page.query_selector_all(clickable_product_selector)
            current_count = len(all_clickable_product_elements)

            if current_count > last_product_count:
                logger.debug(
                    f"Scrolled: Found {current_count} products (was {last_product_count}). Scrolling more..."
                )
                last_product_count = current_count
                scroll_attempts = 0
            else:
                logger.debug(f"No new products after scroll. Total products: {current_count}")
                scroll_attempts += 1

            current_scroll_y = page.evaluate("window.scrollY")
            document_height = page.evaluate("document.body.scrollHeight")
            viewport_height = page.evaluate("window.innerHeight")

            if current_scroll_y + viewport_height >= document_height - 500:
                logger.debug("Near end of document. Assuming all products loaded or no more to load.")
                if current_count == last_product_count:
                    break

        logger.info(f"Final count after scrolling: Found {len(all_clickable_product_elements)} total clickable product elements.")

        product_hrefs = []
        for element in page.query_selector_all(clickable_product_selector):
            href = element.get_attribute("href")
            if href:
                if not href.startswith("http"):
                    href = f"https://www.bershka.com{href}"
                product_hrefs.append(href)

        product_hrefs = list(dict.fromkeys(product_hrefs))
        logger.info(f"Prepared to scrape {len(product_hrefs)} unique product detail pages.")

        page.close()

        for i, product_detail_url in enumerate(product_hrefs):
            product_info = {}
            product_page = None
            try:
                product_page = browser.new_page()
                logger.info(f"-> Processing product {i + 1}/{len(product_hrefs)}: Navigating to {product_detail_url}")
                product_page.goto(product_detail_url, wait_until="load")
                product_page.wait_for_load_state("domcontentloaded")
                time.sleep(random.uniform(2, 4))

                name_element = product_page.query_selector(".product-detail-info-layout__title")
                product_info["name"] = name_element.text_content().strip() if name_element else None

                price_element = product_page.query_selector(
                    ".product-detail-info-layout__price > span:nth-child(1)"
                )
                product_info["prices"] = price_element.text_content().strip() if price_element else None

                color_elements = product_page.query_selector_all(
                    'div[data-qa-anchor="color-selector"] img.color-selector__image'
                )
                colors = []
                if not color_elements:
                    color_elements = product_page.query_selector_all("#color-717 > a img, #color-717 > img")
                for c_el in color_elements:
                    alt_text = c_el.get_attribute("alt")
                    if alt_text:
                        colors.append(alt_text.strip())
                product_info["colors"] = [c for c in colors if c] if colors else None

                size_elements = product_page.query_selector_all(".ui--size-dot-list li button span span")
                sizes = [s.text_content().strip() for s in size_elements if s.text_content().strip()]
                product_info["sizes"] = [s for s in sizes if s] if sizes else None

                image_container = product_page.query_selector(".grid-images-layout__content-container")
                image_urls = []
                if image_container:
                    main_image_elements = image_container.query_selector_all(
                        'div.detail-resource-item img, img.media-image__image, img[src^="https://static.bershka.net/4/photos/"]'
                    )
                    for img_el in main_image_elements:
                        src = img_el.get_attribute("src")
                        if src and src not in image_urls:
                            image_urls.append(src)
                product_info["images"] = image_urls if image_urls else None

                description_container = product_page.query_selector("div.product-detail-description__content")
                if description_container:
                    description_parts = [p.text_content().strip() for p in description_container.query_selector_all("p")]
                    product_info["desc"] = re.sub(r"\s+", " ", "\n".join(description_parts)).strip()
                else:
                    product_info["desc"] = None

                product_info["links"] = product_detail_url

                # Save each product_info to the JSONL file
                with open(output_filename, "a", encoding="utf-8") as f:
                    json.dump(product_info, f, ensure_ascii=False)
                    f.write("\n")
                products_count += 1
                logger.info(f"-> Saved product {products_count} to {output_filename}")

                product_page.close()

            except Exception as e:
                logger.exception(f"Error processing product {product_detail_url}: {e}")
                if product_page is not None and not product_page.is_closed():
                    product_page.close()

        browser.close()

    logger.info(f"\n--- Scraping finished. Total {products_count} products saved to {output_filename} ---")
    return products_count


if __name__ == "__main__":
    bershka_url = "https://www.bershka.com/fr/homme/vetements/t-shirts-n3294.html?celement=1010193239"
    output_file = "bershka_tshirts_scraped_data.jsonl"
    total_scraped_products = scrape_bershka_tshirts(bershka_url, output_file)

    if total_scraped_products > 0:
        logger.info(f"Data available in {output_file}")
    else:
        logger.info("No products were scraped or saved.")
