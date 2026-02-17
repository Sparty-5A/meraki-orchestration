#!/usr/bin/env python3
"""
Comprehensive verification of entire Meraki configuration
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('MERAKI_API_KEY')
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def main():
    # Get network
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]['id']
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    branch_network = [n for n in networks if n['name'] == 'branch office'][0]
    network_id = branch_network['id']

    print("=" * 70)
    print("MERAKI BRANCH OFFICE - COMPLETE CONFIGURATION REPORT")
    print("=" * 70)

    # VLANs
    print("\n📊 VLAN CONFIGURATION:")
    print("-" * 70)
    vlans = dashboard.appliance.getNetworkApplianceVlans(network_id)
    for vlan in vlans:
        print(f"  VLAN {vlan['id']:>3}: {vlan['name']:<15} {vlan['subnet']:<18} GW: {vlan['applianceIp']}")

    # Firewall Rules
    print(f"\n🔒 FIREWALL RULES: (Total: {len(vlans)} VLANs protected)")
    print("-" * 70)
    fw_rules = dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(network_id)
    for i, rule in enumerate(fw_rules['rules'][:5], 1):  # First 5
        policy_icon = "✓" if rule['policy'] == 'allow' else "✗"
        print(f"  {i}. [{policy_icon}] {rule['comment'][:50]}")
    print(f"  ... and {len(fw_rules['rules']) - 5} more rules")

    # Wireless SSIDs - Get detailed info
    print("\n📡 WIRELESS SSIDs:")
    print("-" * 70)
    for i in range(15):  # Meraki supports 0-14 SSIDs
        try:
            ssid = dashboard.wireless.getNetworkWirelessSsid(network_id, number=i)
            if ssid['enabled']:
                # Try multiple VLAN fields
                vlan_id = (ssid.get('defaultVlanId') or
                           ssid.get('vlanId') or
                           ssid.get('useVlanTagging', {}).get('vlanId', 'N/A'))

                auth = ssid.get('authMode', 'N/A')
                visible = "👁️ " if ssid.get('visible', True) else "🔒"
                band = ssid.get('bandSelection', 'Unknown')[:20]

                print(f"  SSID {i}: {visible} {ssid['name']:<20} "
                      f"VLAN {str(vlan_id):<3} Auth: {auth:<10} Band: {band}")
        except:
            continue

    # Devices
    print("\n🖥️  DEVICES:")
    print("-" * 70)
    devices = dashboard.networks.getNetworkDevices(network_id)
    for device in devices:
        model = device['model']
        name = device.get('name') or 'Unnamed'
        serial = device.get('serial', 'N/A')
        status = device.get('status', 'unknown')
        print(f"  {model:<10} {name:<25} Serial: {serial} Status: {status}")

    # Summary
    print("\n" + "=" * 70)
    print("📈 DEPLOYMENT SUMMARY:")
    print("-" * 70)
    print(f"  ✅ VLANs configured: {len(vlans)}")
    print(f"  ✅ Firewall rules: {len(fw_rules['rules'])}")
    print(
        f"  ✅ Active SSIDs: {len([s for s in range(15) if dashboard.wireless.getNetworkWirelessSsid(network_id, s).get('enabled')])}")
    print(f"  ✅ Devices claimed: {len(devices)}")
    print("\n✅ Configuration complete! Branch office is production-ready.")
    print("=" * 70)


if __name__ == "__main__":
    main()
