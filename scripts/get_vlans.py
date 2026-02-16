#!/usr/bin/env python3
"""
Get current VLAN configuration from MX100
"""

import meraki
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('MERAKI_API_KEY')
dashboard = meraki.DashboardAPI(API_KEY, print_console=True)
# dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def main():
    # Get organization and networks
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]['id']
    networks = dashboard.organizations.getOrganizationNetworks(org_id)

    # Find the branch office network
    branch_network = [n for n in networks if n['name'] == 'branch office'][0]
    network_id = branch_network['id']

    print(f"Network: {branch_network['name']}")
    print(f"Network ID: {network_id}")
    print("\n" + "=" * 60)

    # Get VLAN configuration
    try:
        vlans = dashboard.appliance.getNetworkApplianceVlans(network_id)
        print(f"\nVLANs configured: {len(vlans)}")
        print("\nVLAN Details:")
        print(json.dumps(vlans, indent=2))
    except meraki.APIError as e:
        print(f"\nVLANs not enabled or error: {e}")
        print("\nChecking if single LAN mode...")
        try:
            single_lan = dashboard.appliance.getNetworkApplianceSingleLan(network_id)
            print("Single LAN Configuration:")
            print(json.dumps(single_lan, indent=2))
        except Exception as e2:
            print(f"Error: {e2}")


if __name__ == "__main__":
    main()