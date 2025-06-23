import re
from typing import Dict, Any

from mediaflow_proxy.extractors.base import BaseExtractor, ExtractorError

class EnvivoExtractor(BaseExtractor):
    """Envivo1 URL extractor."""

    async def extract(self, url: str, **kwargs) -> Dict[str, Any]:
        """Extract Envivo1 URL."""
        response = await self._make_request(
            url,
            headers={
                'Referer': 'https://librefutboltv.su/',
                'Origin': 'https://librefutboltv.su/',
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