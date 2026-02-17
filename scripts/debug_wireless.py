#!/usr/bin/env python3
"""
Debug wireless SSID configuration
"""

import meraki
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('MERAKI_API_KEY')
dashboard = meraki.DashboardAPI(API_KEY, print_console=True)  # Enable logging


def main():
    # Get network
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]['id']
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    branch_network = [n for n in networks if n['name'] == 'branch office'][0]
    network_id = branch_network['id']

    print("=" * 70)
    print("WIRELESS SSID DEBUG")
    print("=" * 70)

    # Try getting all SSIDs at once
    print("\nMethod 1: Get all SSIDs")
    try:
        ssids = dashboard.wireless.getNetworkWirelessSsids(network_id)
        print(f"Success! Found {len(ssids)} SSIDs")
        print(json.dumps(ssids, indent=2))
    except Exception as e:
        print(f"Error: {e}")

    # Try getting individual SSIDs
    print("\n" + "=" * 70)
    print("Method 2: Get individual SSIDs (0-4)")
    for i in range(5):
        print(f"\nSSID {i}:")
        try:
            ssid = dashboard.wireless.getNetworkWirelessSsid(network_id, number=i)
            print(f"  Name: {ssid.get('name')}")
            print(f"  Enabled: {ssid.get('enabled')}")
            print(f"  VLAN: {ssid.get('defaultVlanId', 'N/A')}")
            print(f"  Auth: {ssid.get('authMode')}")
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    main()
