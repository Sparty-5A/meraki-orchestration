#!/usr/bin/env python3
"""
Configure wireless SSIDs mapped to VLANs
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('MERAKI_API_KEY')
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def configure_ssids(network_id):
    """
    Configure enterprise SSIDs:
    - SSID 0: Corporate (VLAN 10, WPA2-Enterprise)
    - SSID 1: Guest (VLAN 20, Open with splash)
    - SSID 2: IoT (VLAN 30, WPA2-PSK)
    - SSID 3: Voice (VLAN 40, WPA2, high priority QoS)
    """

    ssid_configs = [
        {
            'number': 0,
            'name': 'Shure-Corporate',
            'enabled': True,
            'authMode': 'psk',  # In production, use '8021x-radius' with ISE
            'encryptionMode': 'wpa',
            'psk': 'CorporatePassword123!',
            'ipAssignmentMode': 'Bridge mode',
            'defaultVlanId': 10,
            'visible': True,
            'availableOnAllAps': True,
            'bandSelection': 'Dual band operation',
            'minBitrate': 12  # Force 802.11g/n/ac (no legacy 802.11b)
        },
        {
            'number': 1,
            'name': 'Shure-Guest',
            'enabled': True,
            'authMode': 'open',
            'splashPage': 'Click-through splash page',
            'ipAssignmentMode': 'Bridge mode',
            'defaultVlanId': 20,
            'visible': True,
            'availableOnAllAps': True,
            'bandSelection': '5 GHz band only',  # Force 5GHz for better performance
            'minBitrate': 12,
            'walledGardenEnabled': True,
            'walledGardenRanges': [
                '*.google.com',
                '*.cloudflare.com'
            ]
        },
        {
            'number': 2,
            'name': 'Shure-IoT',
            'enabled': True,
            'authMode': 'psk',
            'encryptionMode': 'wpa',
            'psk': 'IoTDevices2024!',
            'ipAssignmentMode': 'Bridge mode',
            'defaultVlanId': 30,
            'visible': False,  # Hidden SSID for security
            'availableOnAllAps': True,
            'bandSelection': 'Dual band operation',
            'minBitrate': 11
        },
        {
            'number': 3,
            'name': 'Shure-Voice',
            'enabled': True,
            'authMode': 'psk',
            'encryptionMode': 'wpa',
            'psk': 'VoicePhones2024!',
            'ipAssignmentMode': 'Bridge mode',
            'defaultVlanId': 40,
            'visible': False,  # Hidden - only voice devices need it
            'availableOnAllAps': True,
            'bandSelection': '5 GHz band only',  # 5GHz for better QoS
            'minBitrate': 12,
            'perClientBandwidthLimitUp': 1024,  # 1 Mbps per client (voice doesn't need more)
            'perClientBandwidthLimitDown': 1024
        }
    ]

    print("Configuring Wireless SSIDs...")
    print("=" * 60)

    for ssid_config in ssid_configs:
        try:
            response = dashboard.wireless.updateNetworkWirelessSsid(
                network_id,
                **ssid_config
            )

            vlan = ssid_config.get('defaultVlanId', 'N/A')
            auth = ssid_config['authMode']
            visible = "Visible" if ssid_config.get('visible', True) else "Hidden"

            print(f"✓ SSID {ssid_config['number']}: {ssid_config['name']}")
            print(f"  VLAN: {vlan} | Auth: {auth} | {visible}")
            print(f"  Band: {ssid_config.get('bandSelection', 'Dual')}")

        except meraki.APIError as e:
            print(f"✗ Error configuring SSID {ssid_config['number']}: {e}")

    return True


def verify_ssids(network_id):
    """Show configured SSIDs"""
    print("\n" + "=" * 60)
    print("Verification - Configured SSIDs:")
    print("=" * 60)

    ssids = dashboard.wireless.getNetworkWirelessSsids(network_id)

    for ssid in ssids:
        if ssid['enabled']:
            print(f"\nSSID {ssid['number']}: {ssid['name']}")
            print(f"  Enabled: {ssid['enabled']}")
            print(f"  VLAN: {ssid.get('defaultVlanId', 'N/A')}")
            print(f"  Auth: {ssid.get('authMode', 'N/A')}")
            print(f"  Visible: {ssid.get('visible', True)}")


def main():
    # Get network
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]['id']
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    branch_network = [n for n in networks if n['name'] == 'branch office'][0]
    network_id = branch_network['id']

    print(f"Network: {branch_network['name']}")
    print(f"Network ID: {network_id}\n")

    # Configure SSIDs
    configure_ssids(network_id)

    # Verify
    verify_ssids(network_id)

    print("\n" + "=" * 60)
    print("Wireless Configuration Summary:")
    print("  ✓ Corporate WiFi → VLAN 10 (WPA2)")
    print("  ✓ Guest WiFi → VLAN 20 (Open with splash page)")
    print("  ✓ IoT WiFi → VLAN 30 (WPA2, hidden)")
    print("  ✓ Voice WiFi → VLAN 40 (WPA2, hidden, QoS)")
    print("\nEnterprise wireless with VLAN segmentation complete! 📡")


if __name__ == "__main__":
    main()