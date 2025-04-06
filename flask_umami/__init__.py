"""
Flask Umami
-----------

A Flask extension that injects the Umami analytics tag into the HTML response.

:copyright: 2025 by ImShyMike.
:license: AGPL-3.0, see LICENSE for more details.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List

from bs4 import BeautifulSoup
from flask import Flask, request

__version__ = "0.1.3"
__all__ = ["Umami", "UmamiConfig"]


@dataclass
class UmamiConfig:
    """Class that holds the Umami configuration for a specific route.
    Documentation: https://umami.is/docs/tracker-configuration"""

    host_url: str = ""
    auto_track: bool = True
    domains: List[str] = field(default_factory=list)
    tag: str = ""
    exclude_search: bool = False
    exclude_hash: bool = False
    do_not_track: bool = False

    overwrite_url: str = ""
    overwrite_id: str = ""


class Umami:
    """Flask extension that injects the Umami analytics tag into the HTML response."""

    def __init__(
        self,
        app: Flask | None = None,
        *,
        umami_url: str | None,
        umami_id: str | None,
        enabled: bool = True,
        config: Dict[str, UmamiConfig]
        | None = None,  # Defaults to default config for all routes
        ignore_routes: List[str] | None = None,
        ignore_status_codes: List[int] | None = None,
        create_head_if_not_exists: bool = True,
        use_bs4: bool = True,
    ):
        """Class that handles the injection of the Umami analytics tag into the HTML response.

        Args:
            umami_url (str | None): Umami host URL.
            umami_id (str | None): Umami website ID.
            enabled (bool, optional): Tag injection state. Defaults to True.
            config (Dict[str, UmamiConfig], optional): Umami configuration for different routes (uses regex, compares from top to bottom and only the first match is used). Defaults to None = {".*": UmamiConfig()}.
            ignore_routes (List[str] | None, optional): List of routes to ignore (uses regex). Defaults to None.
            ignore_status_codes (List[int] | None, optional): List of status codes to ignore. Defaults to None.
            use_bs4 (bool, optional): Use BeautifulSoup to parse the HTML response, else use regex (may not work). Defaults to True.
            create_head_if_not_exists (bool, optional): Create a head tag if it does not exist, else just ignore. Defaults to True.
        """
        self.umami_url = umami_url
        self.umami_id = umami_id
        self.enabled = enabled
        self.config = config
        self.ignore_routes = ignore_routes or []
        self.ignore_status_codes = ignore_status_codes or []
        self.use_bs4 = use_bs4
        self.create_head_if_not_exists = create_head_if_not_exists
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.ERROR)

        self._head_regex = re.compile(
            r"(<head.*?>)(.*?)(</head>)", re.IGNORECASE | re.DOTALL
        )
        self._html_tag_regex = re.compile(r"(<html.*?>)", re.IGNORECASE)

        self._current_config = None
        self._default_config = UmamiConfig()

        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize the Umami tag injection for the Flask app."""
        app.umami = self  # type: ignore
        app.after_request(self._inject_umami_tag)

    def toggle(self):
        """Toggle the Umami tag injection."""
        self.enabled = not self.enabled

    def _parse_config(self):
        """Parse the Umami configuration into a properly formatted dict."""
        current_config = {
            v: k
            for v, k in self._current_config.__dict__.items()
            if not k.startswith("overwrite_")
        }

        config_dict = {
            v: k for v, k in current_config if self._default_config.__dict__.get(v) != k
        }  # Get only the changed values

        if not config_dict:  # If no changes, return empty dict
            return {}

        config_dict = {
            f"data-{k.replace('_', '-')}": (
                str(v).lower() if isinstance(v, bool) else v
            )
            for k, v in config_dict.items()
        }  # Convert to data-attributes

        if config_dict.get("data-domains"):
            config_dict["data-domains"] = ",".join(
                config_dict["data-domains"]
            )  # Convert domains to comma-separated string

        return config_dict  # Return the parsed config

    def _inject_umami_tag(self, response):
        """Inject the Umami tag into the HTML response at the end of the head tag (creates a head tag if it does not exist)."""
        if not self.umami_url or not self.umami_id:
            return response  # Skip if no umami_url or umami_id

        if not self.enabled:
            return response  # Skip if not enabled

        if response.status_code in self.ignore_status_codes:
            return response  # Skip if status code is in ignore_status_codes

        for route in self.ignore_routes:
            if re.match(route, request.path):
                return response  # Skip if route matches ignore_routes

        self._current_config = None
        if self.config:
            for pattern, config in self.config.items():
                if re.match(pattern, request.path):
                    self._current_config = config
                    break

        if "text/html" in response.content_type:
            if self.use_bs4:
                soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")

                # Check if there's a head tag
                head = soup.find("head")

                # If there's no head tag, create one
                if not head:
                    if not self.create_head_if_not_exists:
                        return response

                    head = soup.new_tag("head")

                    # Check if there's an html tag
                    html = soup.find("html")

                    # If there's no html tag, insert the head tag at the beginning
                    if html is not None:
                        html.insert(0, head)  # type: ignore
                    else:
                        soup.insert(0, head)

                # Parse the current config
                current_config = {}
                if self._current_config and self.config is not None:
                    current_config = self._parse_config()

                overwrite_url = (
                    self._current_config.overwrite_url if self._current_config else None
                )
                overwrite_id = (
                    self._current_config.overwrite_id if self._current_config else None
                )

                umami_tag = soup.new_tag(
                    "script",
                    src=f"{overwrite_url or self.umami_url}/script.js",
                    attrs={
                        "defer": "",
                        "data-website-id": overwrite_id or self.umami_id,
                    }
                    | current_config,
                )

                # Insert the Umami tag into the head tag
                if head is not None:
                    head.append(umami_tag)  # type: ignore
                    response.set_data(str(soup))
                else:
                    self.logger.error(
                        "Failed to inject Umami tag into the HTML response."
                    )
            else:
                html = response.get_data(as_text=True)

                # Parse the current config
                config_string = ""
                if self._current_config and self.config is not None:
                    current_config = self._parse_config()
                    config_string = (
                        " ".join([f'{k}="{v}"' for k, v in current_config.items()])
                        + " "
                    )

                overwrite_url = (
                    self._current_config.overwrite_url if self._current_config else None
                )
                overwrite_id = (
                    self._current_config.overwrite_id if self._current_config else None
                )

                umami_tag = (
                    f'<script defer {config_string}src="{overwrite_url or self.umami_url}/'
                    f'script.js" data-website-id="{overwrite_id or self.umami_id}"></script>'
                )

                # Check if there's a head tag
                match = self._head_regex.search(html)
                if match:
                    # Insert the script before the closing head tag
                    updated_html = html.replace(
                        match.group(0),
                        f"{match.group(1)}{match.group(2)}{umami_tag}{match.group(3)}",
                    )
                    response.set_data(updated_html)
                else:
                    # No head tag found, try to insert after the opening html tag
                    if not self.create_head_if_not_exists:
                        return response

                    html_match = self._html_tag_regex.search(html)
                    if html_match:
                        updated_html = html.replace(
                            html_match.group(0),
                            f"{html_match.group(0)}<head>{umami_tag}</head>",
                        )
                        response.set_data(updated_html)
                    else:
                        # No html tag, insert at the beginning
                        updated_html = f"<head>{umami_tag}</head>{html}"
                        response.set_data(updated_html)

        return response
