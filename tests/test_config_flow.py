import pytest
from homeassistant.core import HomeAssistant

from custom_components.sourceful_zap.config_flow import SourcefulZapConfigFlow


@pytest.mark.asyncio
async def test_user_flow_valid_host(hass: HomeAssistant):
    flow = SourcefulZapConfigFlow()
    flow.hass = hass
    result = await flow.async_step_user({"host": "127.0.0.1"})
    assert result["type"] == "create_entry"
    assert result["data"]["host"] == "127.0.0.1"


@pytest.mark.asyncio
async def test_user_flow_invalid_host(hass: HomeAssistant):
    flow = SourcefulZapConfigFlow()
    flow.hass = hass
    result = await flow.async_step_user({"host": "invalid_host!"})
    assert result["type"] == "form"
    assert "host" in result["errors"] or "host" in result.get("errors", {})
