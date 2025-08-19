from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

# ---- validators --------------------------------------------------------------


def _endpoint(value: str) -> str:
    """Ensure endpoint starts with a slash."""
    if not isinstance(value, str) or not value.startswith("/"):
        raise vol.Invalid("must_start_with_slash")
    return value


# ---- Schema (exported for tests) ---------------------------------------------

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_SCAN_INTERVAL, default=30): vol.All(
            cv.positive_int, vol.Range(min=1, max=3600)
        ),
        vol.Optional("p1_endpoint", default="/api/data/p1/obis"): vol.All(
            str, _endpoint
        ),
        vol.Optional("system_endpoint", default="/api/system"): vol.All(str, _endpoint),
    }
)


# ---- Options Flow ------------------------------------------------------------


class SourcefulZapOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Sourceful Zap options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options form."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Merge current options over data so changed options persist
        current = {**self.config_entry.data, **self.config_entry.options}

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current.get(CONF_SCAN_INTERVAL, 30),
                ): vol.All(cv.positive_int, vol.Range(min=1, max=3600)),
                vol.Optional(
                    "p1_endpoint",
                    default=current.get("p1_endpoint", "/api/data/p1/obis"),
                ): vol.All(str, _endpoint),
                vol.Optional(
                    "system_endpoint",
                    default=current.get("system_endpoint", "/api/system"),
                ): vol.All(str, _endpoint),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow handler."""
        return SourcefulZapOptionsFlowHandler(config_entry)
