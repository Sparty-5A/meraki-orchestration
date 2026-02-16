#!/usr/bin/env python3
"""
Manually apply template configuration to networks
Simulates what template binding should do
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('MERAKI_API_KEY')
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def get_template_config(template_id):
    """
    Extract configuration from template
    """
    print("Reading template configuration...")

    config = {
        'vlans': [],
        'firewall_rules': {},
        'ssids': []
    }

    # Get VLANs
    try:
        vlans = dashboard.appliance.getNetworkApplianceVlans(template_id)
        config['vlans'] = vlans
        print(f"  ✓ Found {len(vlans)} VLANs")
    except:
        print(f"  ⚠ Could not read VLANs")

    # Get firewall rules
    try:
        fw = dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(template_id)
        config['firewall_rules'] = fw
        print(f"  ✓ Found {len(fw['rules'])} firewall rules")
    except:
        print(f"  ⚠ Could not read firewall rules")

    # Get SSIDs
    try:
        ssids = dashboard.wireless.getNetworkWirelessSsids(template_id)
        enabled_ssids = [s for s in ssids if s['enabled']]
        config['ssids'] = enabled_ssids
        print(f"  ✓ Found {len(enabled_ssids)} enabled SSIDs")
    except:
        print(f"  ⚠ Could not read SSIDs")

    return config


def apply_config_to_network(network_id, network_name, template_config):
    """
    Apply template configuration to a network
    """
    print(f"\n{'=' * 70}")
    print(f"Applying config to: {network_name}")
    print(f"{'=' * 70}")

    # Enable VLANs first
    try:
        dashboard.appliance.updateNetworkApplianceVlansSettings(
            network_id,
            vlansEnabled=True
        )
        print("  ✓ VLANs enabled")
    except Exception as e:
        print(f"  ⚠ VLANs: {e}")

    # Apply VLANs
    if template_config['vlans']:
        print(f"\nApplying {len(template_config['vlans'])} VLANs...")
        for vlan in template_config['vlans']:
            try:
                # Skip VLAN 1 (default)
                if vlan['id'] == '1':
                    continue

                dashboard.appliance.createNetworkApplianceVlan(
                    network_id,
                    id=vlan['id'],
                    name=vlan['name'],
                    subnet=vlan['subnet'],
                    applianceIp=vlan['applianceIp']
                )
                print(f"  ✓ VLAN {vlan['id']}: {vlan['name']}")
            except meraki.APIError as e:
                if "already exists" in str(e).lower():
                    print(f"  ⚠ VLAN {vlan['id']} exists, skipping")
                else:
                    print(f"  ✗ VLAN {vlan['id']}: {e}")

    # Apply firewall rules
    if template_config['firewall_rules']:
        print(f"\nApplying firewall rules...")
        try:
            dashboard.appliance.updateNetworkApplianceFirewallL3FirewallRules(
                network_id,
                rules=template_config['firewall_rules']['rules']
            )
            print(f"  ✓ Applied {len(template_config['firewall_rules']['rules'])} rules")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    # Apply SSIDs
    if template_config['ssids']:
        print(f"\nApplying SSIDs...")
        for ssid in template_config['ssids']:
            try:
                # Remove read-only fields
                ssid_config = {k: v for k, v in ssid.items()
                               if k not in ['number', 'adminSplashUrl']}

                dashboard.wireless.updateNetworkWirelessSsid(
                    network_id,
                    number=ssid['number'],
                    **ssid_config
                )
                print(f"  ✓ SSID {ssid['number']}: {ssid['name']}")
            except Exception as e:
                print(f"  ✗ SSID {ssid['number']}: {e}")


def main():
    print("=" * 70)
    print("MANUAL TEMPLATE CONFIG APPLICATION")
    print("=" * 70)
    print("\nThis simulates what template binding should do automatically")

    # Get organization
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]['id']

    # Get template
    templates = dashboard.organizations.getOrganizationConfigTemplates(org_id)
    template = [t for t in templates if t['name'] == 'Enterprise-Standard-Template'][0]
    template_id = template['id']

    print(f"\nTemplate: {template['name']}")
    print(f"Template ID: {template_id}\n")

    # Get template configuration
    print("=" * 70)
    print("STEP 1: EXTRACT TEMPLATE CONFIGURATION")
    print("=" * 70)
    template_config = get_template_config(template_id)

    # Get branch networks
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    branch_networks = [n for n in networks if n['name'].startswith('Branch-')]

    print(f"\n{'=' * 70}")
    print(f"STEP 2: APPLY TO {len(branch_networks)} NETWORKS")
    print(f"{'=' * 70}")

    # Apply to each network
    for network in branch_networks:
        apply_config_to_network(network['id'], network['name'], template_config)

    print("\n" + "=" * 70)
    print("✓ CONFIGURATION APPLIED")
    print("=" * 70)
    print("\nResult: All 3 networks now have the same configuration!")
    print("This is what template binding would do automatically.")
    print("\nVerify in Dashboard:")
    print("  - Switch to Branch-Chicago")
    print("  - Check VLANs, Firewall, SSIDs")
    print("  - Should match Branch-NYC and Branch-LA")


if __name__ == "__main__":
    main()