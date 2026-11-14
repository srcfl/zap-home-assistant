"""The cards and the dashboard the integration brings to the frontend.

The integration serves one JavaScript file, ``frontend/zap-cards.js``, and
loads it in the frontend. The file defines the cards and a dashboard strategy
that builds its views in the browser from the Zap's sensors. This module also
adds a dashboard that uses the strategy to the sidebar.

Everything here is an extra. A failure is logged and leaves the sensors alone.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.json import json_bytes, json_fragment

from .const import CONF_DASHBOARD, DOMAIN

try:
    from homeassistant.components.lovelace.dashboard import LovelaceConfig
except ImportError:  # pragma: no cover - lovelace ships with Home Assistant
    LovelaceConfig = object  # type: ignore[assignment,misc]

_LOGGER = logging.getLogger(__name__)

FRONTEND_FILE = "zap-cards.js"
FRONTEND_URL = f"/{DOMAIN}/{FRONTEND_FILE}"
STRATEGY = "custom:sourceful-zap"

DASHBOARD_TITLE = "Sourceful Zap"
DASHBOARD_ICON = "mdi:lightning-bolt-circle"
# The second address is used when a dashboard of the user's own has the first.
DASHBOARD_URL_PATHS = ("sourceful-zap", "sourceful-zap-dashboard")
DASHBOARD_CONFIG: dict[str, Any] = {"strategy": {"type": STRATEGY}}

DATA_FRONTEND_URL = f"{DOMAIN}_frontend_url"
DATA_STATIC_PATH = f"{DOMAIN}_static_path"
DATA_DASHBOARD = f"{DOMAIN}_dashboard"
LOVELACE = "lovelace"
MODE_YAML = "yaml"


def _digest(path: Path) -> str:
    """Return a short hash of the file, so a new file gets a new address."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


async def async_register_frontend(hass: HomeAssistant) -> bool:
    """Serve the cards and load them in the frontend.

    Returns True when the frontend has the cards. Safe to call more than once.
    """
    if hass.data.get(DATA_FRONTEND_URL):
        return True
    if hass.http is None or "frontend" not in hass.config.components:
        _LOGGER.debug("No frontend to add the Sourceful Zap cards to")
        return False

    path = Path(__file__).parent / "frontend" / FRONTEND_FILE
    try:
        digest = await hass.async_add_executor_job(_digest, path)
        if not hass.data.get(DATA_STATIC_PATH):
            await hass.http.async_register_static_paths(
                [StaticPathConfig(FRONTEND_URL, str(path), True)]
            )
            hass.data[DATA_STATIC_PATH] = True
        url = f"{FRONTEND_URL}?v={digest}"
        frontend.add_extra_js_url(hass, url)
    except Exception:  # pylint: disable=broad-except
        _LOGGER.warning("Could not add the Sourceful Zap cards", exc_info=True)
        return False

    hass.data[DATA_FRONTEND_URL] = url
    return True


@callback
def async_unregister_frontend(hass: HomeAssistant) -> None:
    """Stop loading the cards in the frontend."""
    url = hass.data.pop(DATA_FRONTEND_URL, None)
    if url is None:
        return
    try:
        frontend.remove_extra_js_url(hass, url)
    except Exception:  # pylint: disable=broad-except
        _LOGGER.debug("Could not remove the Sourceful Zap cards", exc_info=True)


class ZapDashboard(LovelaceConfig):
    """A read-only dashboard that the frontend builds from the Zap's sensors."""

    def __init__(self, hass: HomeAssistant, url_path: str) -> None:
        """Describe the dashboard the way a YAML dashboard is described."""
        super().__init__(
            hass,
            url_path,
            {
                "mode": MODE_YAML,
                "title": DASHBOARD_TITLE,
                "icon": DASHBOARD_ICON,
                "show_in_sidebar": True,
                "require_admin": False,
            },
        )

    @property
    def mode(self) -> str:
        """Return the mode: read-only, like a YAML dashboard."""
        return MODE_YAML

    async def async_get_info(self) -> dict[str, Any]:
        """Return what Home Assistant lists about a dashboard."""
        return {"mode": self.mode, "views": 0}

    async def async_load(  # pylint: disable=unused-argument
        self, force: bool
    ) -> dict[str, Any]:
        """Return the dashboard: one strategy that the frontend runs."""
        return DASHBOARD_CONFIG

    async def async_json(  # pylint: disable=unused-argument
        self, force: bool
    ) -> json_fragment:
        """Return the dashboard as JSON."""
        return json_fragment(json_bytes(DASHBOARD_CONFIG))


def _wanted(hass: HomeAssistant) -> bool:
    """Return True when a loaded Zap has the dashboard switched on."""
    for entry_id in hass.data.get(DOMAIN, {}):
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is not None and entry.options.get(CONF_DASHBOARD, True):
            return True
    return False


@callback
def async_update_dashboard(hass: HomeAssistant) -> None:
    """Add or remove the sidebar dashboard to match the loaded Zaps."""
    wanted = bool(hass.data.get(DATA_FRONTEND_URL)) and _wanted(hass)
    current = hass.data.get(DATA_DASHBOARD)
    try:
        if wanted and current is None:
            _add_dashboard(hass)
        elif not wanted and current is not None:
            _remove_dashboard(hass, current)
    except Exception:  # pylint: disable=broad-except
        _LOGGER.warning("Could not update the Sourceful Zap dashboard", exc_info=True)


def _add_dashboard(hass: HomeAssistant) -> None:
    dashboards = getattr(hass.data.get(LOVELACE), "dashboards", None)
    if LovelaceConfig is object or not isinstance(dashboards, dict):
        _LOGGER.debug("No dashboards to add the Sourceful Zap dashboard to")
        return

    for url_path in DASHBOARD_URL_PATHS:
        if url_path in dashboards:
            continue
        try:
            frontend.async_register_built_in_panel(
                hass,
                LOVELACE,
                sidebar_title=DASHBOARD_TITLE,
                sidebar_icon=DASHBOARD_ICON,
                frontend_url_path=url_path,
                config={"mode": MODE_YAML},
                require_admin=False,
            )
        except ValueError:
            # Another panel has this address.
            continue
        dashboards[url_path] = ZapDashboard(hass, url_path)
        hass.data[DATA_DASHBOARD] = url_path
        _LOGGER.debug("Added the Sourceful Zap dashboard at /%s", url_path)
        return

    _LOGGER.info(
        "The Sourceful Zap dashboard was not added: /%s and /%s are both taken. "
        "You can add it yourself from Settings, Dashboards",
        *DASHBOARD_URL_PATHS,
    )


def _remove_dashboard(hass: HomeAssistant, url_path: str) -> None:
    hass.data.pop(DATA_DASHBOARD, None)
    dashboards = getattr(hass.data.get(LOVELACE), "dashboards", None)
    if isinstance(dashboards, dict):
        dashboards.pop(url_path, None)
    frontend.async_remove_panel(hass, url_path, warn_if_unknown=False)
