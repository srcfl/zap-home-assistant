# Sourceful Zap Integration Tests

Test suite for the Sourceful Zap Home Assistant integration.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared pytest fixtures
├── test_config_flow.py         # Config flow tests
├── test_init.py                # Integration setup/teardown tests
├── test_sensor.py              # Sensor entity tests
├── test_api.py                 # API client tests
├── test_coordinator.py         # Data coordinator tests
├── test_datamodel_v2.py        # Firmware 7.x data model v2 parsing
├── test_dashboard.py           # Cards and dashboard added to the frontend
├── frontend/
│   └── zap-cards.test.mjs      # Logic in frontend/zap-cards.js, run with Node
├── fixtures/                   # Firmware 7.x payloads
└── README.md                   # This file
```

## Running Tests

### Run All Tests
```bash
pytest tests/
node --test tests/frontend/
```

The Node tests need Node 20 or newer and no packages.

### Run Specific Test File
```bash
pytest tests/test_config_flow.py -v
pytest tests/test_sensor.py -v
pytest tests/test_api.py -v
pytest tests/test_coordinator.py -v
pytest tests/test_datamodel_v2.py -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=custom_components/sourceful_zap --cov-report=html
pytest tests/ --cov=custom_components/sourceful_zap --cov-report=term-missing
```

### Run Specific Test
```bash
pytest tests/test_config_flow.py::test_manual_flow_success -v
pytest tests/test_sensor.py::test_power_sensor_state -v
```

### Run with Verbose Output
```bash
pytest tests/ -v -s
```

## What Each File Covers

| File | Covers |
|------|--------|
| `test_config_flow.py` | Menu, manual entry, network scan, zeroconf discovery, options flow and input validation |
| `test_dashboard.py` | Serving the cards, adding and removing the sidebar dashboard, address conflicts, the option, and failures that must not stop the sensors |
| `frontend/zap-cards.test.mjs` | Axis scales and ticks, unit conversion, which data a range reads, bar buckets, and the dashboard the strategy builds for a meter, a hybrid inverter and two Zaps |
| `test_api.py` | API client requests, response formats and error handling |
| `test_coordinator.py` | Data updates, connection status, partial data and value conversion |
| `test_sensor.py` | Sensor creation per DER type, state, availability and device info |
| `test_init.py` | Entry setup, unload and reload |
| `test_datamodel_v2.py` | Firmware 7.x payloads mapped onto the existing sensors, with signs matching firmware 2.3.x |

## Fixtures (conftest.py)

### Available Fixtures

- `hass` - Home Assistant instance (from pytest-homeassistant-custom-component)
- `auto_enable_custom_integrations` - Enables custom integrations for every test
- `mock_config_entry` - Mock config entry with default values
- `mock_zap_api` - Mock API client with successful responses
- `mock_zap_api_battery` - Mock API client with a battery device
- `mock_zap_api_p1_meter` - Mock API client with a P1 meter
- `mock_zap_api_error` - Mock API client that raises errors

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

Coverage measured at v1.1.1:

| Module | Goal | Measured |
|--------|------|----------|
| Config flow | 100% (required for Home Assistant core) | 100% |
| API client | >95% | 100% |
| Integration init | >95% | 97% |
| Data model | >95% | 96% |
| Sensors | >95% | 91% |
| Coordinator | >95% | 89% |
| Overall | >95% | 96% |

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

Tests run on Python 3.13 on:
- Every push to `main` and `develop`
- Every pull request to `main` and `develop`
- Every release tag, before the release is built

See `.github/workflows/test.yml` and `.github/workflows/release.yml` for CI configuration.

## Writing New Tests

### Test Naming Convention
- Test files: `test_<component>.py`
- Test functions: `test_<what_is_being_tested>`
- Use descriptive names: `test_manual_flow_cannot_connect` not `test_error_1`

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
pytest tests/test_config_flow.py::test_manual_flow_success -v -s
```

### Run with PDB Debugger
```bash
pytest tests/test_config_flow.py::test_manual_flow_success --pdb
```

### Print Debug Information
```python
async def test_debug_example(hass, mock_config_entry, mock_zap_api):
    """Test with debug output."""
    import pprint

    # Print fixture data
    pprint.pprint(mock_config_entry.data)

    # Print state
    for state in hass.states.async_all("sensor"):
        print(state.entity_id, state.state, state.attributes)
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
