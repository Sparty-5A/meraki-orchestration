#!/usr/bin/env python3
"""
Enable VLANs on all branch networks
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('MERAKI_API_KEY')
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def main():
    print("=" * 70)
    print("ENABLE VLANs ON BRANCH NETWORKS")
    print("=" * 70)

    # Get organization
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]['id']

    # Get branch networks
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    branch_networks = [n for n in networks if n['name'].startswith('Branch-')]

    print(f"\nFound {len(branch_networks)} networks:\n")

    for network in branch_networks:
        print(f"Network: {network['name']}")

        # Check current status
        try:
            settings = dashboard.appliance.getNetworkApplianceVlansSettings(network['id'])
            current = settings.get('vlansEnabled', False)
            print(f"  Current: VLANs {'enabled' if current else 'disabled'}")

            if not current:
                # Enable VLANs
                dashboard.appliance.updateNetworkApplianceVlansSettings(
                    network['id'],
                    vlansEnabled=True
                )
                print(f"  ✓ VLANs now ENABLED")
            else:
                print(f"  ✓ Already enabled")

        except Exception as e:
            print(f"  ✗ Error: {e}")

        print()

    print("=" * 70)
    print("✓ VLAN ENABLEMENT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()