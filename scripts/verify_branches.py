#!/usr/bin/env python3
"""
Verify all branch networks have template configuration
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("MERAKI_API_KEY")
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def verify_network(network_id, network_name):
    """
    Verify network has template configuration
    """
    print(f"\n{'=' * 70}")
    print(f"NETWORK: {network_name}")
    print(f"{'=' * 70}")

    # Check VLANs
    print("\n📊 VLANs:")
    try:
        vlans = dashboard.appliance.getNetworkApplianceVlans(network_id)
        print(f"  Total: {len(vlans)}")
        for vlan in vlans:
            print(f"    VLAN {vlan['id']:>3}: {vlan['name']:<15} {vlan['subnet']:<18} GW: {vlan['applianceIp']}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Check firewall
    print("\n🔒 Firewall Rules:")
    try:
        fw = dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(network_id)
        print(f"  Total: {len(fw['rules'])}")
        for i, rule in enumerate(fw["rules"][:5], 1):
            policy = "✓" if rule["policy"] == "allow" else "✗"
            print(f"    {i}. [{policy}] {rule['comment'][:50]}")
        if len(fw["rules"]) > 5:
            print(f"    ... and {len(fw['rules']) - 5} more")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Check SSIDs
    print("\n📡 Wireless SSIDs:")
    try:
        ssids = dashboard.wireless.getNetworkWirelessSsids(network_id)
        enabled = [s for s in ssids if s["enabled"]]
        print(f"  Active: {len(enabled)}")
        for ssid in enabled:
            vlan = ssid.get("defaultVlanId", "N/A")
            auth = ssid.get("authMode", "N/A")
            visible = "👁️ " if ssid.get("visible", True) else "🔒"
            print(f"    SSID {ssid['number']}: {visible} {ssid['name']:<20} VLAN {vlan:<3} Auth: {auth}")
    except Exception as e:
        print(f"  ✗ Error: {e}")


def main():
    print("=" * 70)
    print("BRANCH NETWORK VERIFICATION")
    print("=" * 70)

    # Get organization
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]["id"]

    # Get branch networks
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    branch_networks = [n for n in networks if n["name"].startswith("Branch-")]

    print(f"\nVerifying {len(branch_networks)} branch networks:")
    for net in branch_networks:
        print(f"  - {net['name']}")

    # Verify each
    for network in branch_networks:
        verify_network(network["id"], network["name"])

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)
    print("\n✓ All branch networks should now have:")
    print("  - 5 VLANs (1, 10, 20, 30, 40, 50)")
    print("  - 6 firewall rules")
    print("  - 2 SSIDs (Corp-WiFi, Guest-WiFi)")


if __name__ == "__main__":
    main()
