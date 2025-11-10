thonimport logging
import urllib.parse
from typing import Any, List, Optional, Set, Dict

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .facebook_parser import FacebookPostParser

class ScrollManager:
    """
    Handles browser lifecycle, navigation to Facebook search results and
    infinite scrolling until we collect enough posts or hit scroll limits.
    """

    def __init__(
        self,
        base_search_url: str,
        scroll_pause: float = 2.0,
        max_scroll: int = 100,
        headless: bool = True,
        user_agent: Optional[str] = None,
        locale: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.base_search_url = base_search_url
        self.scroll_pause = scroll_pause
        self.max_scroll = max_scroll
        self.headless = headless
        self.user_agent = user_agent
        self.locale = locale or "en-US"
        self.logger = logger or logging.getLogger(__name__)

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def __aenter__(self) -> "ScrollManager":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        context_kwargs: Dict[str, Any] = {"locale": self.locale}
        if self.user_agent:
            context_kwargs["user_agent"] = self.user_agent
        self._context = await self._browser.new_context(**context_kwargs)
        self._page = await self._context.new_page()
        self._page.set_default_timeout(30_000)
        self.logger.debug("Browser context created (headless=%s)", self.headless)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.logger.debug("Tearing down browser context")
        try:
            if self._context:
                await self._context.close()
        finally:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()

    async def _goto_search(self, query: str) -> Page:
        assert self._page is not None, "Page is not initialized"
        encoded_query = urllib.parse.quote_plus(query)
        url = self.base_search_url.format(query=encoded_query)
        self.logger.info("Navigating to search URL: %s", url)
        await self._page.goto(url, wait_until="networkidle")
        return self._page

    async def scrape_search(
        self,
        query: str,
        parser: FacebookPostParser,
        max_posts: int,
    ) -> List[Dict[str, Any]]:
        """
        Navigate to the Facebook search results and scroll until we collect
        at least max_posts or hit scroll limits.
        """
        page = await self._goto_search(query)
        posts: List[Dict[str, Any]] = []
        seen_post_ids: Set[str] = set()

        scroll_count = 0
        while len(posts) < max_posts and scroll_count < self.max_scroll:
            scroll_count += 1
            self.logger.debug(
                "Scroll iteration %d | collected=%d/%d",
                scroll_count,
                len(posts),
                max_posts,
            )

            # Extract any posts currently visible
            remaining = max_posts - len(posts)
            new_posts = await parser.extract_posts(page, seen_post_ids, max_posts=remaining)
            if new_posts:
                posts.extend(new_posts)
                self.logger.info("Collected %d new posts (total=%d)", len(new_posts), len(posts))

            if len(posts) >= max_posts:
                break

            # Scroll further down to load more results
            await page.mouse.wheel(0, 4000)
            await page.wait_for_timeout(int(self.scroll_pause * 1000))

        if scroll_count >= self.max_scroll:
            self.logger.warning(
                "Reached maximum scroll limit (%d) with %d posts collected.",
                self.max_scroll,
                len(posts),
            )

        return posts[:max_posts]