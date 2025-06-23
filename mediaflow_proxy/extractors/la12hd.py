import re
from typing import Dict, Any
from urllib.parse import urlparse

from mediaflow_proxy.extractors.base import BaseExtractor, ExtractorError

class La12hdExtractor(BaseExtractor):
    """La12hd URL extractor."""

    def _get_origin(self, url: str) -> str:
        """Extract origin from URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    async def extract(self, url: str, **kwargs) -> Dict[str, Any]:
        """Extract La12hd URL."""
        url_origin = self._get_origin(url)

        response = await self._make_request(
            url,
            headers={
                'Referer': f'{url_origin}/',
                'Origin': url_origin,
                "user-agent": self.base_headers["user-agent"]
            }
        )

        # Extract and decode URL
        match = re.search(r'var playbackURL = "(.*?)"', response.text)
        if not match:
            raise ExtractorError("Failed to extract URL components")
        
        self.base_headers["referer"] = url
        return {
            "destination_url": match.group(1),
            "request_headers": self.base_headers,
            "mediaflow_endpoint": self.mediaflow_endpoint,
        }