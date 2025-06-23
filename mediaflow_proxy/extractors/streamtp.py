import re
import ast
import base64
from typing import Dict, Any
from urllib.parse import urlparse

from mediaflow_proxy.extractors.base import BaseExtractor, ExtractorError

class StreamtpExtractor(BaseExtractor):
    """Streamtp URL extractor."""

    async def extract(self, url: str, **kwargs) -> Dict[str, Any]:
        """Extract Streamtp URL."""
        url_referer = urlparse(url).hostname

        response = await self._make_request(
            url,
            headers={
                'Referer': f'https://{url_referer}/',
                'Accept': 'text/response.text,application/xresponse.text+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8,en-US;q=0.7',
                "user-agent": self.base_headers["user-agent"]
            }
        )

        match = re.search(r'var playbackURL = "(.*?)"', response.text)
        if not match:
            raise ExtractorError("Failed to extract URL components")
        
        main_logic_regex = re.search(r'var\s+playbackURL\s*=\s*""\s*,\s*(\w+)\s*=\s*\[\][^;]*;\s*\1\s*=\s*(\[\[[\s\S]*?\]\]);', response.text)
        if not main_logic_regex:
            raise ExtractorError("The data array structure or name could not be found")
        
        array_var_name = main_logic_regex.group(1)
        data_array_string = main_logic_regex.group(2)

        k_functions_match = re.search(r'var\s+k\s*=\s*(\w+)\(\)\s*\+\s*(\w+)\(\);', response.text)
        if not k_functions_match:
            raise ExtractorError("Could not find functions for 'k'")

        k1_func = k_functions_match.group(1)
        k2_func = k_functions_match.group(2)

        k1_match = re.search(rf'function\s+{k1_func}\s*\(\)\s*\{{\s*return\s*(\d+);?\s*\}}', response.text)
        k2_match = re.search(rf'function\s+{k2_func}\s*\(\)\s*\{{\s*return\s*(\d+);?\s*\}}', response.text)

        if not k1_match or not k2_match:
            raise ExtractorError("Return values could not be found for functions k1 or k2")

        k1 = int(k1_match.group(1))
        k2 = int(k2_match.group(1))
        k = k1 + k2

        if k == 0:
            raise ExtractorError(f"Invalid k values: k1={k1}, k2={k2}, total={k}")

        try:
            data_array = ast.literal_eval(data_array_string)
        except Exception as e:
            raise ExtractorError(f"Error parsing array {array_var_name}: {str(e)}")

        data_array.sort(key=lambda x: x[0])
        final_url = ""

        for item in data_array:
            if isinstance(item, list) and len(item) >= 2 and isinstance(item[1], str):
                b64_value = item[1]
                try:
                    decoded = base64.b64decode(b64_value).decode('latin1')
                    digits = re.sub(r'\D', '', decoded)
                    if digits:
                        final_url += chr(int(digits) - k)
                except Exception:
                    continue
        
        self.base_headers["referer"] = url
        return {
            "destination_url": final_url,
            "request_headers": self.base_headers,
            "mediaflow_endpoint": self.mediaflow_endpoint,
        }