"""Content extraction and cleaning module with improved handling for modern web design."""

import logging
import re
from typing import Optional, Dict, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class Extractor:
    """Extracts and cleans content from HTML with support for modern web design patterns."""

    # Elements to remove - expanded for modern sites
    REMOVE_SELECTORS = [
        "script",
        "style",
        "nav",
        "header",
        "footer",
        "aside",
        ".sidebar",
        ".navigation",
        ".menu",
        ".advertisement",
        ".ads",
        ".social-share",
        ".comments",
        "noscript",
        # Modern web patterns
        "[role='navigation']",
        "[role='banner']",
        "[role='complementary']",
        "[role='contentinfo']",
        ".cookie-banner",
        ".cookie-popup",
        ".modal",
        ".popup",
        ".overlay",
        ".skip-link",
        ".breadcrumb",
        # Common flex/grid layout containers that are navigation
        ".navbar",
        ".nav-bar",
        ".topbar",
        ".header-bar",
        ".footer-bar",
        ".site-header",
        ".site-footer",
        ".main-nav",
        ".primary-nav",
        ".secondary-nav",
    ]

    # Selectors that typically indicate main content
    CONTENT_SELECTORS = [
        "main",
        "article",
        "[role='main']",
        "[role='article']",
        ".content",
        ".main-content",
        ".post-content",
        ".article-content",
        ".entry-content",
        ".page-content",
        ".body-content",
        ".main-body",
        # Modern patterns
        ".container",
        ".wrapper",
        "[data-testid*='content']",
        "[data-testid*='article']",
        "[data-testid*='main']",
    ]

    def extract(self, html_content: str, url: str) -> Dict[str, Optional[str]]:
        """
        Extract title, body text, images, and table content from HTML.

        Args:
            html_content: HTML content to parse
            url: URL of the page (for fallback title and resolving relative URLs)

        Returns:
            Dictionary with 'title', 'body_text', 'images', and 'table_content' keys
        """
        try:
            soup = BeautifulSoup(html_content, "lxml")

            # Extract title
            title = self._extract_title(soup, url)

            # Extract main content
            body_text = self._extract_body_text(soup, url)

            # Extract images
            images = self._extract_images(soup, url)

            # Extract table content
            table_content = self._extract_table_content(soup)

            return {
                "title": title,
                "body_text": body_text,
                "images": images,
                "table_content": table_content,
            }

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return {"title": None, "body_text": None, "images": [], "table_content": None}

    def _extract_title(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """
        Extract page title with multiple fallback strategies.

        Args:
            soup: BeautifulSoup object
            url: URL for fallback

        Returns:
            Page title or None
        """
        # Try <title> tag
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            if title and len(title) > 0:
                return title

        # Try <h1> tag (often the main heading)
        h1_tag = soup.find("h1")
        if h1_tag:
            title = h1_tag.get_text(strip=True)
            if title and len(title) > 0:
                return title

        # Try og:title meta tag
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]

        # Try twitter:title
        twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
        if twitter_title and twitter_title.get("content"):
            return twitter_title["content"]

        # Try data attributes (common in modern SPAs)
        title_elem = soup.find(attrs={"data-title": True})
        if title_elem:
            title = title_elem.get("data-title", "").strip()
            if title:
                return title

        # Fallback to URL
        logger.warning(f"Could not extract title from {url}, using URL as fallback")
        return url

    def _extract_body_text(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """
        Extract main body text, removing boilerplate.
        Improved for modern web design patterns including flex layouts.

        Args:
            soup: BeautifulSoup object

        Returns:
            Cleaned body text or None
        """
        # Create a copy to avoid modifying original
        soup_copy = BeautifulSoup(str(soup), "lxml")

        # Remove unwanted elements
        for selector in self.REMOVE_SELECTORS:
            try:
                for element in soup_copy.select(selector):
                    element.decompose()
            except Exception as e:
                logger.debug(f"Error removing selector {selector}: {e}")

        # Try to find main content container using multiple strategies
        main_content = None

        # Strategy 1: Semantic HTML5 elements
        main_content = soup_copy.find("main")
        if not main_content:
            main_content = soup_copy.find("article")
        
        # Strategy 2: Role attributes
        if not main_content:
            main_content = soup_copy.find(attrs={"role": "main"})
        if not main_content:
            main_content = soup_copy.find(attrs={"role": "article"})

        # Strategy 3: Common content class names
        if not main_content:
            for selector in self.CONTENT_SELECTORS:
                try:
                    found = soup_copy.select_one(selector)
                    if found:
                        # Check if it has substantial content
                        text_length = len(found.get_text(strip=True))
                        if text_length > 100:  # Minimum content threshold
                            main_content = found
                            break
                except Exception:
                    continue

        # Strategy 4: Find largest text container (heuristic for flex layouts)
        if not main_content:
            main_content = self._find_largest_content_container(soup_copy)

        # Strategy 5: Fallback to body
        if not main_content:
            main_content = soup_copy.find("body")
            if not main_content:
                main_content = soup_copy

        # Extract text including table content
        if main_content:
            # First, extract and format table content
            tables = main_content.find_all("table")
            table_texts = []
            for table in tables:
                table_text = self._extract_table_text(table)
                if table_text:
                    table_texts.append(table_text)
            
            # Get regular text
            text = main_content.get_text(separator=" ", strip=True)
            
            # Append table content if found
            if table_texts:
                text += " " + " ".join(table_texts)
            
            cleaned_text = self._clean_text(text)
            
            # Validate we got meaningful content
            if len(cleaned_text) < 10:
                logger.warning("Extracted content is too short, may be incomplete")
            
            return cleaned_text

        return None

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract all image URLs from the page.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative image URLs

        Returns:
            List of absolute image URLs
        """
        images = []
        
        # Find all img tags
        img_tags = soup.find_all("img")
        
        for img in img_tags:
            # Try src attribute first
            src = img.get("src")
            if src:
                absolute_url = urljoin(base_url, src)
                # Filter out data URIs and very small images/icons
                if not absolute_url.startswith("data:") and not absolute_url.endswith((".ico", ".svg")):
                    images.append(absolute_url)
            
            # Try srcset attribute (for responsive images)
            srcset = img.get("srcset")
            if srcset:
                # Parse srcset (format: "url1 size1, url2 size2")
                for srcset_item in srcset.split(","):
                    parts = srcset_item.strip().split()
                    if parts:
                        img_url = parts[0]
                        if not img_url.startswith("data:"):
                            absolute_url = urljoin(base_url, img_url)
                            if absolute_url not in images:
                                images.append(absolute_url)
            
            # Try data-src (lazy loading)
            data_src = img.get("data-src")
            if data_src:
                absolute_url = urljoin(base_url, data_src)
                if absolute_url not in images and not absolute_url.startswith("data:"):
                    images.append(absolute_url)
            
            # Try data-lazy-src (another lazy loading pattern)
            data_lazy_src = img.get("data-lazy-src")
            if data_lazy_src:
                absolute_url = urljoin(base_url, data_lazy_src)
                if absolute_url not in images and not absolute_url.startswith("data:"):
                    images.append(absolute_url)

        # Also check for background images in style attributes
        elements_with_bg = soup.find_all(attrs={"style": re.compile(r"background.*image", re.I)})
        for elem in elements_with_bg:
            style = elem.get("style", "")
            # Extract url(...) from style
            url_matches = re.findall(r"url\(['\"]?([^'\"]+)['\"]?\)", style)
            for img_url in url_matches:
                absolute_url = urljoin(base_url, img_url.strip())
                if absolute_url not in images and not absolute_url.startswith("data:"):
                    images.append(absolute_url)

        # Remove duplicates while preserving order
        seen = set()
        unique_images = []
        for img_url in images:
            if img_url not in seen:
                seen.add(img_url)
                unique_images.append(img_url)

        return unique_images

    def _extract_table_content(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract all table content from the page.

        Args:
            soup: BeautifulSoup object

        Returns:
            Formatted table content as text or None
        """
        tables = soup.find_all("table")
        if not tables:
            return None

        table_texts = []
        for table in tables:
            table_text = self._extract_table_text(table)
            if table_text:
                table_texts.append(table_text)

        return " ".join(table_texts) if table_texts else None

    def _extract_table_text(self, table: Tag) -> Optional[str]:
        """
        Extract text content from a table, preserving structure.

        Args:
            table: BeautifulSoup table Tag

        Returns:
            Formatted table text or None
        """
        rows = []
        
        # Handle thead
        thead = table.find("thead")
        if thead:
            header_rows = thead.find_all("tr")
            for tr in header_rows:
                cells = []
                for th in tr.find_all(["th", "td"]):
                    cell_text = th.get_text(separator=" ", strip=True)
                    if cell_text:
                        cells.append(cell_text)
                if cells:
                    rows.append(" | ".join(cells))

        # Handle tbody or direct tr elements
        tbody = table.find("tbody")
        body_rows = (tbody.find_all("tr") if tbody else table.find_all("tr"))
        
        for tr in body_rows:
            # Skip if already processed in thead
            if thead and tr in thead.find_all("tr"):
                continue
                
            cells = []
            for td in tr.find_all(["td", "th"]):
                cell_text = td.get_text(separator=" ", strip=True)
                # Clean up cell text
                cell_text = re.sub(r"\s+", " ", cell_text)
                if cell_text:
                    cells.append(cell_text)
            if cells:
                rows.append(" | ".join(cells))

        if rows:
            return "\n".join(rows)
        return None

    def _find_largest_content_container(self, soup: BeautifulSoup) -> Optional[Tag]:
        """
        Find the largest content container by text length.
        Useful for sites with complex flex/grid layouts.

        Args:
            soup: BeautifulSoup object

        Returns:
            Largest content container or None
        """
        body = soup.find("body")
        if not body:
            return None

        # Find all divs and sections
        containers = body.find_all(["div", "section"], recursive=True)
        
        # Filter out likely navigation/header/footer containers
        filtered_containers = []
        for container in containers:
            # Skip if has navigation-like classes or IDs
            classes = container.get("class", [])
            container_id = container.get("id", "")
            
            skip_keywords = ["nav", "header", "footer", "sidebar", "menu", "bar"]
            if any(keyword in str(classes).lower() or keyword in container_id.lower() 
                   for keyword in skip_keywords):
                continue
            
            # Skip if has role attributes indicating non-content
            role = container.get("role", "")
            if role in ["navigation", "banner", "complementary", "contentinfo"]:
                continue
            
            filtered_containers.append(container)

        # Find container with most text content
        if not filtered_containers:
            return None

        largest = max(
            filtered_containers,
            key=lambda c: len(c.get_text(strip=True))
        )

        # Only return if it has substantial content
        text_length = len(largest.get_text(strip=True))
        if text_length > 100:
            return largest

        return None

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text with improved normalization.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove invisible Unicode characters that might confuse AI models
        # (common in obfuscated content)
        text = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]", "", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove excessive newlines (more than 2 consecutive)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove leading/trailing whitespace
        text = text.strip()

        # Remove common artifacts from flex layouts
        text = re.sub(r"\s*\|+\s*", " ", text)  # Remove pipe separators
        text = re.sub(r"\s*•+\s*", " ", text)  # Remove bullet separators

        return text
