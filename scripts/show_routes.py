#!/usr/bin/env python3
"""
Show that MX100 already has routes to all VLANs
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('MERAKI_API_KEY')
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def main():
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]['id']
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    branch_network = [n for n in networks if n['name'] == 'branch office'][0]
    network_id = branch_network['id']

    print("MX100 VLAN Interfaces (Default Gateways):")
    print("=" * 60)

    # Get VLANs - these are the MX's interfaces
    vlans = dashboard.appliance.getNetworkApplianceVlans(network_id)

    for vlan in vlans:
        print(f"\nVLAN {vlan['id']}: {vlan['name']}")
        print(f"  Subnet: {vlan['subnet']}")
        print(f"  MX IP (Gateway): {vlan['applianceIp']}")
        print("  ↳ MX100 is the router for this VLAN")

    print("\n" + "=" * 60)
    print("Routing Behavior:")
    print("  • MX100 has direct routes to ALL VLANs (connected routes)")
    print("  • Traffic between VLANs is routed automatically")
    print("  • WITHOUT firewall rules, all VLANs can reach each other")
    print("  • Firewall rules are REQUIRED to segment traffic")
    print("\nThis is different from traditional switching!")


if __name__ == "__main__":
    main()
