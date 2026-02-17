#!/usr/bin/env python3
"""
Enable VLANs and create enterprise network segmentation
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('MERAKI_API_KEY')
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def enable_vlans(network_id):
    """Enable VLANs on the network"""
    print("Enabling VLANs...")

    try:
        # Enable VLANs
        response = dashboard.appliance.updateNetworkApplianceVlansSettings(
            network_id,
            vlansEnabled=True
        )
        print("✓ VLANs enabled successfully!")
        return True
    except meraki.APIError as e:
        print(f"Error enabling VLANs: {e}")
        return False


def create_vlans(network_id):
    """Create enterprise VLANs"""

    vlans_to_create = [
        {
            'id': '10',
            'name': 'Corporate',
            'subnet': '10.10.10.0/24',
            'applianceIp': '10.10.10.1'
        },
        {
            'id': '20',
            'name': 'Guest',
            'subnet': '10.10.20.0/24',
            'applianceIp': '10.10.20.1'
        },
        {
            'id': '30',
            'name': 'IoT',
            'subnet': '10.10.30.0/24',
            'applianceIp': '10.10.30.1'
        },
        {
            'id': '40',
            'name': 'Voice',
            'subnet': '10.10.40.0/24',
            'applianceIp': '10.10.40.1'
        }
    ]

    print("\nCreating VLANs...")
    for vlan in vlans_to_create:
        try:
            response = dashboard.appliance.createNetworkApplianceVlan(
                network_id,
                id=vlan['id'],
                name=vlan['name'],
                subnet=vlan['subnet'],
                applianceIp=vlan['applianceIp']
            )
            print(f"✓ Created VLAN {vlan['id']}: {vlan['name']} ({vlan['subnet']})")
        except meraki.APIError as e:
            print(f"✗ Error creating VLAN {vlan['id']}: {e}")


def main():
    # Get network
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]['id']
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    branch_network = [n for n in networks if n['name'] == 'branch office'][0]
    network_id = branch_network['id']

    print(f"Network: {branch_network['name']}")
    print(f"Network ID: {network_id}")
    print("=" * 60)

    # Enable VLANs
    if enable_vlans(network_id):
        # Create VLANs
        create_vlans(network_id)

        # Verify
        print("\n" + "=" * 60)
        print("Verification:")
        vlans = dashboard.appliance.getNetworkApplianceVlans(network_id)
        print(f"\nTotal VLANs configured: {len(vlans)}")
        for vlan in vlans:
            print(f"  VLAN {vlan['id']}: {vlan['name']} - {vlan['subnet']}")


if __name__ == "__main__":
    main()
