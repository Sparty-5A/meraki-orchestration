#!/usr/bin/env python3
"""
Export complete Meraki switch configuration to JSON
Useful for backup, documentation, and comparison
"""

import meraki
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("MERAKI_API_KEY")
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def get_switch_serial(network_id):
    """Find MS switch in network"""
    devices = dashboard.networks.getNetworkDevices(network_id)
    switches = [d for d in devices if d["model"].startswith("MS")]
    return switches[0]["serial"] if switches else None


def export_switch_config(serial, network_name):
    """
    Export complete switch configuration
    """
    print(f"\nExporting configuration for switch: {serial}")

    config = {
        "export_info": {"timestamp": datetime.now().isoformat(), "network": network_name, "switch_serial": serial},
        "device_info": {},
        "ports": [],
        "switch_settings": {},
    }

    # Get device details
    try:
        device = dashboard.devices.getDevice(serial)
        config["device_info"] = {
            "model": device.get("model"),
            "name": device.get("name"),
            "mac": device.get("mac"),
            "lan_ip": device.get("lanIp"),
            "firmware": device.get("firmware"),
            "tags": device.get("tags", []),
        }
        print("  ✓ Device info retrieved")
    except Exception as e:
        print(f"  ⚠ Could not get device info: {e}")

    # Get all port configurations
    try:
        ports = dashboard.switch.getDeviceSwitchPorts(serial)
        config["ports"] = ports
        print(f"  ✓ Retrieved {len(ports)} port configurations")
    except Exception as e:
        print(f"  ✗ Error getting ports: {e}")

    return config


def save_config_json(config, filename):
    """Save configuration to JSON file"""
    with open(filename, "w") as f:
        json.dump(config, f, indent=2)
    print(f"\n✓ Configuration saved to: {filename}")


def display_config_summary(config):
    """Display human-readable summary"""
    print(f"\n{'=' * 70}")
    print("SWITCH CONFIGURATION SUMMARY")
    print(f"{'=' * 70}")

    # Device info
    device = config.get("device_info", {})
    print("\nDevice Information:")
    print(f"  Model: {device.get('model', 'N/A')}")
    print(f"  Name: {device.get('name', 'N/A')}")
    print(f"  Serial: {config['export_info']['switch_serial']}")
    print(f"  Firmware: {device.get('firmware', 'N/A')}")
    print(f"  IP Address: {device.get('lan_ip', 'N/A')}")

    # Port summary
    ports = config.get("ports", [])
    access_ports = [p for p in ports if p.get("type") == "access"]
    trunk_ports = [p for p in ports if p.get("type") == "trunk"]
    poe_ports = [p for p in ports if p.get("poeEnabled")]
    voice_ports = [p for p in ports if p.get("voiceVlan")]

    print("\nPort Statistics:")
    print(f"  Total Ports: {len(ports)}")
    print(f"  Access Ports: {len(access_ports)}")
    print(f"  Trunk Ports: {len(trunk_ports)}")
    print(f"  PoE Enabled: {len(poe_ports)}")
    print(f"  Voice VLAN Configured: {len(voice_ports)}")

    # VLAN usage
    vlans_used = set()
    for port in ports:
        if port.get("vlan"):
            vlans_used.add(port.get("vlan"))
        if port.get("voiceVlan"):
            vlans_used.add(port.get("voiceVlan"))

    print(f"\nVLANs in Use: {sorted(vlans_used)}")

    # Port details table
    print(f"\n{'Port':<6} {'Name':<20} {'Type':<8} {'VLAN':<6} {'Voice':<6} {'PoE':<4} {'Status':<8}")
    print("-" * 70)

    for port in ports[:24]:
        port_id = port.get("portId", "N/A")
        name = port.get("name", "Unconfigured")[:18]
        port_type = port.get("type", "N/A")
        vlan = str(port.get("vlan", "-"))
        voice = str(port.get("voiceVlan", "-"))
        poe = "Yes" if port.get("poeEnabled") else "No"
        enabled = "Enabled" if port.get("enabled") else "Disabled"

        print(f"{port_id:<6} {name:<20} {port_type:<8} {vlan:<6} {voice:<6} {poe:<4} {enabled:<8}")


def main():
    print("=" * 70)
    print("MERAKI SWITCH CONFIGURATION EXPORT")
    print("=" * 70)

    # Get organization
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]["id"]

    # Get networks
    networks = dashboard.organizations.getOrganizationNetworks(org_id)

    # Find branch office
    branch_office = [n for n in networks if "branch office" in n["name"].lower()][0]
    network_id = branch_office["id"]
    network_name = branch_office["name"]

    print(f"\nNetwork: {network_name}")

    # Get switch
    switch_serial = get_switch_serial(network_id)
    if not switch_serial:
        print("\n✗ No switch found in network")
        return

    # Export configuration
    config = export_switch_config(switch_serial, network_name)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"switch_config_{switch_serial}_{timestamp}.json"

    # Save to file
    save_config_json(config, filename)

    # Display summary
    display_config_summary(config)

    print(f"\n{'=' * 70}")
    print("EXPORT COMPLETE")
    print(f"{'=' * 70}")
    print(f"\nConfiguration file: {filename}")
    print("\nYou can:")
    print("  - Use this for backup/restore")
    print("  - Compare configs (diff two JSON files)")
    print("  - Document switch configuration")
    print("  - Import into other tools")


if __name__ == "__main__":
    main()
