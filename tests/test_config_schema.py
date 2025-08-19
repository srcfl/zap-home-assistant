import pytest
import voluptuous as vol

from custom_components.sourceful_zap.config_flow import _validate_host


@pytest.mark.parametrize(
    "host,should_pass",
    [
        ("127.0.0.1", True),
        ("192.168.1.1", True),
        ("localhost", True),
        ("invalid_host!", False),
    ],
)
def test_validate_host(host, should_pass):
    if should_pass:
        assert _validate_host(host) == host
    else:
        with pytest.raises(vol.Invalid):
            _validate_host(host)
