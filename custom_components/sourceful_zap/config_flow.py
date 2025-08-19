from __future__ import annotations

import ipaddress
import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_SCAN_INTERVAL
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

# --- defaults ---
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_NAME = "Zap"

# --- validators ---------------------------------------------------------


def _validate_host(value: str) -> str:
    """Validate host is IP or valid hostname."""
    if not isinstance(value, str):
        raise vol.Invalid("host_must_be_string")

    # Try IP validation
    try:
        ipaddress.ip_address(value)
        return value
    except ValueError:
        pass

    # Hostname regex (RFC 1123)
    hostname_regex = re.compile(
        r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
        r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
    )
    if hostname_regex.match(value):
        return value

    raise vol.Invalid("invalid_host_or_ip")


# --- shared config schema ------------------------------------------------

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): vol.All(str, _validate_host),
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=1, max=3600)
        ),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    }
)


# --- Config Flow --------------------------------------------------------


class SourcefulZapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Sourceful Zap config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # validate + apply defaults
                validated = CONFIG_SCHEMA(user_input)
            except vol.Invalid:
                errors[CONF_HOST] = "invalid_host"
            else:
                return self.async_create_entry(
                    title=validated.get(CONF_NAME, DEFAULT_NAME),
                    data=validated,
                )

        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )


__all__ = ["CONFIG_SCHEMA", "SourcefulZapConfigFlow"]
