# Zap Energy Integration Tests

Comprehensive test suite for the Zap Energy Home Assistant integration with 100% config flow coverage and extensive coverage for all components.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared pytest fixtures
├── test_config_flow.py         # Config flow tests (100% coverage)
├── test_init.py                # Integration setup/teardown tests
├── test_sensor.py              # Sensor entity tests
├── test_api.py                 # API client tests
├── test_coordinator.py         # Data coordinator tests
└── README.md                   # This file
```

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/test_config_flow.py -v
pytest tests/test_sensor.py -v
pytest tests/test_api.py -v
pytest tests/test_coordinator.py -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=custom_components/sourceful_zap --cov-report=html
pytest tests/ --cov=custom_components/sourceful_zap --cov-report=term-missing
```

### Run Specific Test
```bash
pytest tests/test_config_flow.py::test_user_flow_success -v
pytest tests/test_sensor.py::test_power_sensor_state -v
```

### Run with Verbose Output
```bash
pytest tests/ -v -s
```

## Test Coverage

### test_config_flow.py (100% Coverage Required)

**User Flow Tests:**
- `test_user_flow_success` - Successful manual IP entry
- `test_user_flow_cannot_connect` - Connection failure handling
- `test_user_flow_connection_exception` - Connection exception handling
- `test_user_flow_no_devices` - No devices found on gateway
- `test_user_flow_unexpected_exception` - Unexpected error handling
- `test_user_flow_already_configured` - Duplicate device prevention

**Zeroconf Flow Tests:**
- `test_zeroconf_flow_success` - Successful auto-discovery
- `test_zeroconf_flow_cannot_connect` - Discovery connection failure
- `test_zeroconf_flow_already_configured` - Duplicate prevention
- `test_zeroconf_confirm_step` - User confirmation step

**Options Flow Tests:**
- `test_options_flow` - Update polling interval
- `test_options_flow_default_values` - Default values shown
- `test_options_flow_minimum_interval` - Minimum interval validation
- `test_options_flow_with_existing_options` - Existing options preserved

**Validation Tests:**
- `test_validate_input_success` - Input validation success
- `test_validate_input_with_device_name` - Device name handling
- `test_validate_input_without_device_name` - Fallback title generation

### test_api.py

**API Client Tests:**
- `test_init` - Client initialization
- `test_init_strips_trailing_slash` - Host normalization
- `test_get_devices_success` - Device list retrieval
- `test_get_devices_no_serial_number` - Filter invalid devices
- `test_get_devices_not_list` - Invalid response handling
- `test_get_device_data_success` - Real-time data retrieval
- `test_get_device_ders_success` - DER metadata retrieval
- `test_get_system_info_success` - System info retrieval

**Error Handling Tests:**
- `test_request_timeout` - Timeout error handling
- `test_request_client_error` - Client error handling
- `test_request_http_error` - HTTP 404 error handling
- `test_request_500_error` - HTTP 500 error handling
- `test_test_connection_success` - Connection test success
- `test_test_connection_failure` - Connection test failure
- `test_test_connection_timeout` - Connection test timeout

**Edge Cases:**
- `test_request_includes_timeout` - Timeout configuration
- `test_get_devices_empty_list` - Empty device list
- `test_get_device_data_with_special_serial` - Special characters
- `test_api_base_exception` - Base exception
- `test_connection_error_inheritance` - Exception inheritance
- `test_get_devices_with_minimal_device_data` - Minimal data handling

### test_coordinator.py

**Coordinator Tests:**
- `test_coordinator_init` - Coordinator initialization
- `test_coordinator_update_success` - Successful data update
- `test_coordinator_update_with_ders_data` - DER metadata inclusion
- `test_coordinator_update_with_connection_status` - Connection status
- `test_coordinator_update_with_disconnected_status` - Disconnected handling
- `test_coordinator_update_failure` - Update failure handling
- `test_coordinator_partial_data` - Partial data handling

**Data Extraction Tests:**
- `test_coordinator_energy_metrics` - Energy data extraction
- `test_coordinator_battery_metrics` - Battery data extraction
- `test_coordinator_system_metrics` - System data extraction
- `test_coordinator_der_metadata` - DER metadata extraction

**Edge Cases:**
- `test_coordinator_custom_polling_interval` - Custom intervals
- `test_coordinator_multiple_updates` - Multiple update cycles
- `test_coordinator_type_conversion` - String to float conversion
- `test_coordinator_empty_device_data` - Empty data handling
- `test_coordinator_negative_battery_power` - Negative values
- `test_coordinator_zero_values` - Zero value handling
- `test_coordinator_ders_failure_partial_success` - Partial failures

### test_sensor.py

**Sensor Setup Tests:**
- `test_sensor_setup` - Entity creation for all sensor types
- `test_multiple_devices` - Multiple device handling

**Sensor State Tests:**
- `test_power_sensor_state` - Power sensor state and attributes
- `test_energy_import_sensor_state` - Energy import sensor
- `test_energy_export_sensor_state` - Energy export sensor
- `test_battery_soc_sensor_state` - Battery SOC sensor
- `test_battery_power_sensor_state` - Battery power sensor
- `test_temperature_sensor_state` - Temperature sensor
- `test_signal_strength_sensor_state` - Signal strength sensor

**Sensor Behavior Tests:**
- `test_sensor_extra_attributes` - Extra attributes included
- `test_sensor_availability_on_success` - Availability with data
- `test_sensor_unavailable_on_missing_data` - Unavailable without data
- `test_sensor_update` - State updates on refresh
- `test_sensor_device_info` - Device info attached
- `test_sensor_has_entity_name` - Entity naming pattern
- `test_signal_strength_disabled_by_default` - Default disabled entities
- `test_sensor_suggested_display_precision` - Display precision
- `test_sensor_with_session_state_attribute` - Session state attributes
- `test_sensor_none_value_handling` - None value handling

### test_init.py (Existing)

**Integration Tests:**
- `test_setup_entry` - Successful setup
- `test_setup_entry_no_devices` - No devices failure
- `test_setup_entry_connection_error` - Connection error handling
- `test_unload_entry` - Entry unload
- `test_reload_entry` - Entry reload

## Fixtures (conftest.py)

### Available Fixtures

- `hass` - Home Assistant instance (from pytest-homeassistant-custom-component)
- `mock_config_entry` - Mock config entry with default values
- `mock_zap_api` - Mock API client with successful responses
- `mock_zap_api_error` - Mock API client that raises errors
- `mock_device_data` - Mock coordinator device data

### Fixture Usage Example

```python
async def test_example(hass, mock_config_entry, mock_zap_api):
    """Test example using fixtures."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient",
        return_value=mock_zap_api,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Test assertions here
```

## Coverage Goals

- **Config Flow**: 100% (Required for Home Assistant core)
- **API Client**: >95%
- **Coordinator**: >95%
- **Sensors**: >95%
- **Integration Init**: >95%
- **Overall**: >95%

## Coverage Report

Generate HTML coverage report:
```bash
pytest tests/ --cov=custom_components/sourceful_zap --cov-report=html
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

Generate terminal coverage report:
```bash
pytest tests/ --cov=custom_components/sourceful_zap --cov-report=term-missing
```

## Continuous Integration

Tests are automatically run on:
- Every push to main branch
- Every pull request
- Before release tags

See `.github/workflows/test.yml` for CI configuration.

## Writing New Tests

### Test Naming Convention
- Test files: `test_<component>.py`
- Test functions: `test_<what_is_being_tested>`
- Use descriptive names: `test_user_flow_cannot_connect` not `test_error_1`

### Test Structure
```python
async def test_feature_description(hass, mock_config_entry, mock_zap_api):
    """Test docstring describing what is being tested."""
    # Arrange - Set up test data and mocks
    mock_config_entry.add_to_hass(hass)

    # Act - Perform the action being tested
    with patch("custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api):
        result = await hass.config_entries.async_setup(mock_config_entry.entry_id)

    # Assert - Verify expected behavior
    assert result is True
    assert mock_config_entry.state == ConfigEntryState.LOADED
```

### Mocking Best Practices
1. **Patch at the usage point** - Patch where the object is used, not where it's defined
2. **Use AsyncMock for async functions** - `AsyncMock(return_value=...)`
3. **Use MagicMock for sync objects** - `MagicMock()`
4. **Mock at the right level** - Mock API responses, not HTTP calls

### Testing Async Code
```python
async def test_async_function(hass):
    """Test async function."""
    # Always use async def for tests
    result = await some_async_function()
    assert result is not None

    # Wait for all tasks to complete
    await hass.async_block_till_done()
```

## Debugging Tests

### Run Single Test with Output
```bash
pytest tests/test_config_flow.py::test_user_flow_success -v -s
```

### Run with PDB Debugger
```bash
pytest tests/test_config_flow.py::test_user_flow_success --pdb
```

### Print Debug Information
```python
async def test_debug_example(hass, mock_config_entry, mock_zap_api):
    """Test with debug output."""
    import pprint

    # Print fixture data
    pprint.pprint(mock_config_entry.data)

    # Print state
    state = hass.states.get("sensor.zap_zap12345_power")
    print(f"State: {state.state}")
    print(f"Attributes: {state.attributes}")
```

## Common Issues

### Issue: Tests Hanging
**Solution**: Ensure `await hass.async_block_till_done()` is called after async operations

### Issue: Import Errors
**Solution**: Run `pip install -r requirements_test.txt` to install dependencies

### Issue: Mock Not Working
**Solution**: Patch at the correct location where the object is used:
```python
# Correct
with patch("custom_components.sourceful_zap.config_flow.ZapApiClient"):
    ...

# Incorrect
with patch("custom_components.sourceful_zap.api.ZapApiClient"):
    ...
```

### Issue: Fixture Not Found
**Solution**: Ensure `conftest.py` is in the tests directory and fixtures are properly defined

## Additional Resources

- [Home Assistant Test Documentation](https://developers.home-assistant.io/docs/development_testing/)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)
- [Home Assistant Integration Quality Scale](https://www.home-assistant.io/docs/quality_scale/)
