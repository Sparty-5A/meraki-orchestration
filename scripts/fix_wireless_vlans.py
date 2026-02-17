#!/usr/bin/env python3
"""
Configure wireless SSIDs with PROPER VLAN tagging
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MERAKI_API_KEY")
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def configure_ssids_with_vlans(network_id):
    """
    Configure enterprise SSIDs with VLAN tagging enabled
    """

    ssid_configs = [
        {
            "number": 0,
            "name": "Shure-Corporate",
            "enabled": True,
            "authMode": "psk",
            "encryptionMode": "wpa",
            "psk": "CorporatePassword123!",
            "ipAssignmentMode": "Bridge mode",
            "useVlanTagging": True,  # ← ENABLE VLAN TAGGING
            "defaultVlanId": 10,  # ← MAP TO VLAN 10
            "visible": True,
            "availableOnAllAps": True,
            "bandSelection": "Dual band operation",
            "minBitrate": 12,
        },
        {
            "number": 1,
            "name": "Shure-Guest",
            "enabled": True,
            "authMode": "open",
            "splashPage": "Click-through splash page",
            "ipAssignmentMode": "Bridge mode",
            "useVlanTagging": True,  # ← ENABLE VLAN TAGGING
            "defaultVlanId": 20,  # ← MAP TO VLAN 20
            "visible": True,
            "availableOnAllAps": True,
            "bandSelection": "5 GHz band only",
            "minBitrate": 12,
            "walledGardenEnabled": True,
            "walledGardenRanges": ["*.google.com", "*.cloudflare.com"],
        },
        {
            "number": 2,
            "name": "Shure-IoT",
            "enabled": True,
            "authMode": "psk",
            "encryptionMode": "wpa",
            "psk": "IoTDevices2024!",
            "ipAssignmentMode": "Bridge mode",
            "useVlanTagging": True,  # ← ENABLE VLAN TAGGING
            "defaultVlanId": 30,  # ← MAP TO VLAN 30
            "visible": False,
            "availableOnAllAps": True,
            "bandSelection": "Dual band operation",
            "minBitrate": 11,
        },
        {
            "number": 3,
            "name": "Shure-Voice",
            "enabled": True,
            "authMode": "psk",
            "encryptionMode": "wpa",
            "psk": "VoicePhones2024!",
            "ipAssignmentMode": "Bridge mode",
            "useVlanTagging": True,  # ← ENABLE VLAN TAGGING
            "defaultVlanId": 40,  # ← MAP TO VLAN 40
            "visible": False,
            "availableOnAllAps": True,
            "bandSelection": "5 GHz band only",
            "minBitrate": 12,
            "perClientBandwidthLimitUp": 1024,
            "perClientBandwidthLimitDown": 1024,
        },
    ]

    print("Configuring Wireless SSIDs with VLAN Tagging...")
    print("=" * 70)

    for ssid_config in ssid_configs:
        try:
            response = dashboard.wireless.updateNetworkWirelessSsid(network_id, **ssid_config)

            vlan = ssid_config.get("defaultVlanId", "N/A")
            auth = ssid_config["authMode"]
            visible = "👁️  Visible" if ssid_config.get("visible", True) else "🔒 Hidden"

            print(f"✓ SSID {ssid_config['number']}: {ssid_config['name']}")
            print(f"  VLAN: {vlan} | Auth: {auth} | {visible}")

        except meraki.APIError as e:
            print(f"✗ Error configuring SSID {ssid_config['number']}: {e}")

    return True


def verify_vlan_tagging(network_id):
    """Verify VLAN tagging is enabled"""
    print("\n" + "=" * 70)
    print("Verification - VLAN Tagging Status:")
    print("=" * 70)

    ssids = dashboard.wireless.getNetworkWirelessSsids(network_id)

    for ssid in ssids[:4]:  # First 4 SSIDs
        vlan_tagging = ssid.get("useVlanTagging", False)
        default_vlan = ssid.get("defaultVlanId", "N/A")

        status = "✓" if vlan_tagging else "✗"

        print(f"\n{status} SSID {ssid['number']}: {ssid['name']}")
        print(f"  VLAN Tagging: {vlan_tagging}")
        print(f"  Default VLAN: {default_vlan}")


def main():
    # Get network
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]["id"]
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    branch_network = [n for n in networks if n["name"] == "branch office"][0]
    network_id = branch_network["id"]

    print(f"Network: {branch_network['name']}")
    print(f"Network ID: {network_id}\n")

    # Configure SSIDs with VLAN tagging
    configure_ssids_with_vlans(network_id)

    # Verify
    verify_vlan_tagging(network_id)

    print("\n" + "=" * 70)
    print("✅ Wireless SSIDs now properly mapped to VLANs!")
    print("=" * 70)
    print("\nVLAN Mapping:")
    print("  Corporate WiFi (SSID 0) → VLAN 10")
    print("  Guest WiFi (SSID 1)     → VLAN 20")
    print("  IoT WiFi (SSID 2)       → VLAN 30")
    print("  Voice WiFi (SSID 3)     → VLAN 40")


if __name__ == "__main__":
    main()
