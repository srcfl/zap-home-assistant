#!/usr/bin/env python3
"""Simple script to test Zap API connection."""

import asyncio
import sys
import aiohttp


async def test_zap_connection(host: str, api_path: str = "/api"):
    """Test connection to Zap device.

    Args:
        host: IP address or hostname
        api_path: API base path (default: /api)
    """
    # Clean up host input
    host = host.strip().replace("http://", "").replace("https://", "").rstrip("/")
    api_path = api_path.rstrip("/")
    base_url = f"http://{host}{api_path}"

    print(f"Testing connection to Zap device...")
    print(f"Host: {host}")
    print(f"API Path: {api_path}")
    print(f"Base URL: {base_url}")
    print()

    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Check /api/system for "zap" property
            print("Step 1: Checking /system endpoint for Zap identification...")
            print(f"URL: {base_url}/system")
            async with session.get(
                f"{base_url}/system",
                timeout=timeout
            ) as response:
                print(f"Response status: {response.status}")

                if response.status == 200:
                    system_data = await response.json()
                    print(f"System data: {system_data}")

                    if "zap" in system_data:
                        print(f"[SUCCESS] Zap device identified: {system_data.get('zap')}")
                    else:
                        print(f"[WARNING] Response does not contain 'zap' property")
                        print(f"Available keys: {list(system_data.keys())}")
                        print()
                        print("This may not be a Zap device.")
                        return
                else:
                    text = await response.text()
                    print(f"[ERROR] HTTP {response.status}")
                    print(f"Response: {text[:200]}")
                    return

            print()
            # Step 2: Check /api/devices
            print("Step 2: Fetching device list from /devices endpoint...")
            print(f"URL: {base_url}/devices")
            async with session.get(
                f"{base_url}/devices",
                timeout=timeout
            ) as response:
                print(f"Response status: {response.status}")
                print(f"Response headers: {dict(response.headers)}")
                print()

                if response.status == 200:
                    data = await response.json()
                    print(f"[SUCCESS] Response received")
                    print(f"   Type: {type(data)}")
                    print()

                    # Parse devices like the integration does
                    device_list = []
                    if isinstance(data, dict) and "devices" in data:
                        device_list = data["devices"]
                        print(f"   Response format: dict with 'devices' key")
                        print(f"   Device count: {data.get('count', len(device_list))}")
                    elif isinstance(data, list):
                        device_list = data
                        print(f"   Response format: direct list")
                        print(f"   Device count: {len(device_list)}")

                    if not device_list:
                        print(f"   [WARNING] No devices found in response")
                        return

                    print()
                    print(f"Found {len(device_list)} device(s):")
                    print()
                    for i, device in enumerate(device_list):
                        serial = device.get("sn") or device.get("serial_number")
                        device_type = device.get("type", "unknown")
                        profile = device.get("profile", "")
                        connected = device.get("connected", False)
                        ders = device.get("ders", [])

                        print(f"Device {i+1}:")
                        print(f"  Serial Number: {serial}")
                        print(f"  Type: {device_type}")
                        if profile:
                            print(f"  Profile: {profile}")
                        print(f"  Connected: {connected}")
                        print(f"  DERs: {len(ders)}")
                        for der in ders:
                            der_type = der.get("type", "unknown")
                            enabled = der.get("enabled", False)
                            print(f"    - {der_type} (enabled: {enabled})")
                        print()
                else:
                    text = await response.text()
                    print(f"[ERROR] HTTP {response.status}")
                    print(f"   Response: {text[:200]}")

    except aiohttp.ClientConnectorError as err:
        print(f"[ERROR] Connection refused: {err}")
        print(f"   Type: {type(err).__name__}")
        print()
        print("Troubleshooting:")
        print("  - Verify the IP address is correct")
        print("  - Check if device is powered on")
        print("  - Ensure device is on the same network")
        print(f"  - Try accessing http://{host}/api/devices in a web browser")
        print("  - Check for firewall rules blocking port 80")
    except aiohttp.ClientError as err:
        print(f"[ERROR] Connection error: {err}")
        print(f"   Type: {type(err).__name__}")
    except asyncio.TimeoutError:
        print(f"[ERROR] Connection timeout after 10 seconds")
        print("   Device may be unreachable or slow to respond")
    except Exception as err:
        print(f"[ERROR] Unexpected error: {err}")
        print(f"   Type: {type(err).__name__}")


async def test_device_data(host: str, serial_number: str, api_path: str = "/api"):
    """Test fetching device data endpoint.

    Args:
        host: IP address or hostname
        serial_number: Device serial number
        api_path: API base path (default: /api)
    """
    host = host.strip().replace("http://", "").replace("https://", "").rstrip("/")
    api_path = api_path.rstrip("/")
    base_url = f"http://{host}{api_path}"

    print(f"\nTesting device data endpoint...")
    print(f"URL: {base_url}/devices/{serial_number}/data/json")
    print()

    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{base_url}/devices/{serial_number}/data/json",
                timeout=timeout
            ) as response:
                print(f"Response status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    print(f"[SUCCESS] Device data retrieved")
                    print()

                    # Show structure
                    if isinstance(data, dict):
                        for der_type, der_data in data.items():
                            if isinstance(der_data, dict) and "type" in der_data:
                                print(f"DER Type: {der_type}")
                                print(f"  Type field: {der_data.get('type')}")
                                if "W" in der_data:
                                    print(f"  Power: {der_data['W']} W")
                                if "total_generation_Wh" in der_data:
                                    print(f"  Total Generation: {der_data['total_generation_Wh']} Wh")
                                if "SoC_nom_fract" in der_data:
                                    soc_percent = der_data["SoC_nom_fract"] * 100
                                    print(f"  SOC: {soc_percent}%")
                                if "sessionState" in der_data:
                                    print(f"  Session State: {der_data['sessionState']}")
                                if "timestamp" in der_data:
                                    print(f"  Timestamp: {der_data['timestamp']}")
                                print()
                else:
                    text = await response.text()
                    print(f"[ERROR] HTTP {response.status}")
                    print(f"Response: {text[:200]}")

    except aiohttp.ClientConnectorError as err:
        print(f"[ERROR] Connection refused while fetching device data: {err}")
        print(f"   Type: {type(err).__name__}")
        print()
        print("Troubleshooting:")
        print("  - Verify the IP address is correct")
        print("  - Check if device is powered on")
        print("  - Ensure device is on the same network")
        print(f"  - Try accessing http://{host}{api_path}/devices/{serial_number}/data/json in a web browser")
        print("  - Check for firewall rules blocking port 80")
    except aiohttp.ClientError as err:
        print(f"[ERROR] Connection error while fetching device data: {err}")
        print(f"   Type: {type(err).__name__}")
    except asyncio.TimeoutError:
        print(f"[ERROR] Connection timeout after 10 seconds while fetching device data")
        print("   Device may be unreachable or slow to respond")
    except Exception as err:
        print(f"[ERROR] Unexpected error while fetching device data: {err}")
        print(f"   Type: {type(err).__name__}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_connection.py <host> [api_path]")
        print("       python test_connection.py <host> <serial_number> data")
        print()
        print("Examples:")
        print("  python test_connection.py 192.168.1.100")
        print("  python test_connection.py 192.168.1.100 7E16E274 data")
        sys.exit(1)

    host = sys.argv[1]

    # Check if this is a data endpoint test
    if len(sys.argv) >= 4 and sys.argv[3] == "data":
        serial_number = sys.argv[2]
        asyncio.run(test_device_data(host, serial_number))
    else:
        api_path = sys.argv[2] if len(sys.argv) > 2 else "/api"
        asyncio.run(test_zap_connection(host, api_path))
