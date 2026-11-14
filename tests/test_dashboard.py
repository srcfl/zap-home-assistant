"""Test the cards and the dashboard the integration adds to the frontend."""

import json
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import json_bytes
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sourceful_zap import dashboard
from custom_components.sourceful_zap.const import (
    CONF_DASHBOARD,
    CONF_POLLING_INTERVAL,
    DOMAIN,
)

COMPONENT = Path(dashboard.__file__).parent
FRONTEND_FILE = COMPONENT / "frontend" / "zap-cards.js"


@pytest.fixture
def frontend_env(hass: HomeAssistant):
    """Give hass an HTTP server, a frontend and dashboards, all mocked."""
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()
    hass.config.components.add("frontend")
    lovelace = SimpleNamespace(dashboards={})
    hass.data["lovelace"] = lovelace
    with patch.object(dashboard, "frontend") as frontend:
        yield SimpleNamespace(frontend=frontend, lovelace=lovelace, http=hass.http)


async def setup_entry(hass, entry, api):
    """Set up a config entry with a mocked Zap."""
    entry.add_to_hass(hass)
    with patch("custom_components.sourceful_zap.ZapApiClient", return_value=api):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()


def second_entry():
    """Return a config entry for a second Zap."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.101", CONF_POLLING_INTERVAL: 10},
        unique_id="zap-gateway-67890",
        title="Sourceful Zap zap-gateway-67890",
    )


async def test_cards_and_dashboard_are_added(
    hass: HomeAssistant, mock_config_entry, mock_zap_api, frontend_env
):
    """Setting up a Zap serves the cards and adds the dashboard to the sidebar."""
    await setup_entry(hass, mock_config_entry, mock_zap_api)

    (paths,) = frontend_env.http.async_register_static_paths.await_args.args
    assert [(path.url_path, path.path) for path in paths] == [
        ("/sourceful_zap/zap-cards.js", str(FRONTEND_FILE))
    ]
    (_hass, url), _kwargs = frontend_env.frontend.add_extra_js_url.call_args
    assert re.fullmatch(r"/sourceful_zap/zap-cards\.js\?v=[0-9a-f]{10}", url)

    panel = frontend_env.frontend.async_register_built_in_panel.call_args
    assert panel.args[1] == "lovelace"
    assert panel.kwargs["frontend_url_path"] == "sourceful-zap"
    assert panel.kwargs["sidebar_title"] == "Sourceful Zap"
    assert panel.kwargs["config"] == {"mode": "yaml"}
    assert panel.kwargs["require_admin"] is False

    board = frontend_env.lovelace.dashboards["sourceful-zap"]
    assert board.mode == "yaml"
    assert board.url_path == "sourceful-zap"
    assert board.config["title"] == "Sourceful Zap"
    assert await board.async_load(False) == {
        "strategy": {"type": "custom:sourceful-zap"}
    }
    assert json.loads(json_bytes(await board.async_json(False))) == {
        "strategy": {"type": "custom:sourceful-zap"}
    }
    assert await board.async_get_info() == {"mode": "yaml", "views": 0}


async def test_setup_without_a_frontend(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """A Home Assistant without a frontend still gets its sensors."""
    await setup_entry(hass, mock_config_entry, mock_zap_api)

    assert mock_config_entry.state == ConfigEntryState.LOADED
    assert dashboard.DATA_FRONTEND_URL not in hass.data
    assert dashboard.DATA_DASHBOARD not in hass.data


async def test_dashboard_uses_second_address_when_first_is_taken(
    hass: HomeAssistant, mock_config_entry, mock_zap_api, frontend_env
):
    """A dashboard the user made at /sourceful-zap is left alone."""
    own = object()
    frontend_env.lovelace.dashboards["sourceful-zap"] = own

    await setup_entry(hass, mock_config_entry, mock_zap_api)

    assert frontend_env.lovelace.dashboards["sourceful-zap"] is own
    assert "sourceful-zap-dashboard" in frontend_env.lovelace.dashboards
    panel = frontend_env.frontend.async_register_built_in_panel.call_args
    assert panel.kwargs["frontend_url_path"] == "sourceful-zap-dashboard"
    assert hass.data[dashboard.DATA_DASHBOARD] == "sourceful-zap-dashboard"


async def test_dashboard_skips_an_address_another_panel_has(
    hass: HomeAssistant, mock_config_entry, mock_zap_api, frontend_env
):
    """A panel at the first address makes the dashboard take the second."""
    frontend_env.frontend.async_register_built_in_panel.side_effect = [
        ValueError("Overwriting panel sourceful-zap"),
        None,
    ]

    await setup_entry(hass, mock_config_entry, mock_zap_api)

    assert list(frontend_env.lovelace.dashboards) == ["sourceful-zap-dashboard"]


async def test_no_dashboard_when_both_addresses_are_taken(
    hass: HomeAssistant, mock_config_entry, mock_zap_api, frontend_env
):
    """With no free address the cards are still there, without a dashboard."""
    frontend_env.lovelace.dashboards.update(
        {"sourceful-zap": object(), "sourceful-zap-dashboard": object()}
    )

    await setup_entry(hass, mock_config_entry, mock_zap_api)

    assert mock_config_entry.state == ConfigEntryState.LOADED
    assert dashboard.DATA_DASHBOARD not in hass.data
    frontend_env.frontend.async_register_built_in_panel.assert_not_called()
    frontend_env.frontend.add_extra_js_url.assert_called_once()


async def test_dashboard_can_be_switched_off(
    hass: HomeAssistant, mock_zap_api, frontend_env
):
    """The option keeps the cards and leaves the sidebar alone."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100"},
        options={CONF_DASHBOARD: False},
        unique_id="zap-gateway-12345",
    )

    await setup_entry(hass, entry, mock_zap_api)

    frontend_env.frontend.add_extra_js_url.assert_called_once()
    frontend_env.frontend.async_register_built_in_panel.assert_not_called()
    assert not frontend_env.lovelace.dashboards


async def test_unload_removes_cards_and_dashboard(
    hass: HomeAssistant, mock_config_entry, mock_zap_api, frontend_env
):
    """Unloading the only Zap takes the dashboard and the cards away."""
    await setup_entry(hass, mock_config_entry, mock_zap_api)
    url = hass.data[dashboard.DATA_FRONTEND_URL]

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert not frontend_env.lovelace.dashboards
    frontend_env.frontend.async_remove_panel.assert_called_once_with(
        hass, "sourceful-zap", warn_if_unknown=False
    )
    frontend_env.frontend.remove_extra_js_url.assert_called_once_with(hass, url)
    assert dashboard.DATA_DASHBOARD not in hass.data
    assert dashboard.DATA_FRONTEND_URL not in hass.data


async def test_dashboard_stays_while_another_zap_is_loaded(
    hass: HomeAssistant, mock_config_entry, mock_zap_api, frontend_env
):
    """Two Zaps share one dashboard, which goes with the last of them."""
    other = second_entry()
    await setup_entry(hass, mock_config_entry, mock_zap_api)
    await setup_entry(hass, other, mock_zap_api)

    frontend_env.frontend.async_register_built_in_panel.assert_called_once()
    frontend_env.http.async_register_static_paths.assert_awaited_once()

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert "sourceful-zap" in frontend_env.lovelace.dashboards
    frontend_env.frontend.async_remove_panel.assert_not_called()

    assert await hass.config_entries.async_unload(other.entry_id)
    await hass.async_block_till_done()
    assert not frontend_env.lovelace.dashboards
    frontend_env.frontend.async_remove_panel.assert_called_once()


async def test_setup_again_does_not_register_the_file_twice(
    hass: HomeAssistant, mock_config_entry, mock_zap_api, frontend_env
):
    """A reload adds the dashboard again but serves the file once."""
    await setup_entry(hass, mock_config_entry, mock_zap_api)
    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_reload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    frontend_env.http.async_register_static_paths.assert_awaited_once()
    assert frontend_env.frontend.add_extra_js_url.call_count == 2
    assert "sourceful-zap" in frontend_env.lovelace.dashboards


async def test_frontend_failure_leaves_the_sensors(
    hass: HomeAssistant, mock_config_entry, mock_zap_api, frontend_env, caplog
):
    """A failure to serve the cards is logged and the Zap still loads."""
    frontend_env.http.async_register_static_paths.side_effect = RuntimeError("boom")

    await setup_entry(hass, mock_config_entry, mock_zap_api)

    assert mock_config_entry.state == ConfigEntryState.LOADED
    assert "Could not add the Sourceful Zap cards" in caplog.text
    assert not frontend_env.lovelace.dashboards


async def test_dashboard_failure_leaves_the_sensors(
    hass: HomeAssistant, mock_config_entry, mock_zap_api, frontend_env, caplog
):
    """A failure to add the dashboard is logged and the Zap still loads."""
    frontend_env.frontend.async_register_built_in_panel.side_effect = RuntimeError(
        "boom"
    )

    await setup_entry(hass, mock_config_entry, mock_zap_api)

    assert mock_config_entry.state == ConfigEntryState.LOADED
    assert "Could not update the Sourceful Zap dashboard" in caplog.text
    assert dashboard.DATA_DASHBOARD not in hass.data


async def test_cards_removal_failure_is_ignored(
    hass: HomeAssistant, mock_config_entry, mock_zap_api, frontend_env
):
    """A failure to remove the cards does not stop the unload."""
    await setup_entry(hass, mock_config_entry, mock_zap_api)
    frontend_env.frontend.remove_extra_js_url.side_effect = RuntimeError("boom")

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED


async def test_no_dashboards_to_add_to(
    hass: HomeAssistant, mock_config_entry, mock_zap_api, frontend_env
):
    """Without Home Assistant's dashboards the cards are still served."""
    del hass.data["lovelace"]

    await setup_entry(hass, mock_config_entry, mock_zap_api)

    frontend_env.frontend.add_extra_js_url.assert_called_once()
    frontend_env.frontend.async_register_built_in_panel.assert_not_called()
    assert dashboard.DATA_DASHBOARD not in hass.data


def test_frontend_file_matches_the_release():
    """The shipped file exists and carries the integration's version."""
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    source = FRONTEND_FILE.read_text(encoding="utf-8")

    match = re.search(r'^export const VERSION = "([^"]+)";$', source, re.MULTILINE)
    assert match, "zap-cards.js must export VERSION"
    assert match.group(1) == manifest["version"]
    # The strategy and the cards the dashboard is built from
    for name in (
        "ll-strategy-dashboard-sourceful-zap",
        "zap-stat-card",
        "zap-chart-card",
        "zap-range-picker",
        "zap-heading-card",
    ):
        assert f'"{name}"' in source


def test_translations_match_strings():
    """Custom integrations load translations/en.json; it must equal strings.json."""
    strings = (COMPONENT / "strings.json").read_text(encoding="utf-8")
    english = (COMPONENT / "translations" / "en.json").read_text(encoding="utf-8")
    assert json.loads(strings) == json.loads(english)
