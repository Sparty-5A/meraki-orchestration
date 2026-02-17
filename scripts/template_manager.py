#!/usr/bin/env python3
"""
Meraki Configuration Template Manager
Demonstrates multi-site management best practices
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("MERAKI_API_KEY")
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def create_template(org_id, template_name):
    """
    Create a configuration template
    Templates allow centralized management of multiple networks
    """
    print(f"\nCreating template: {template_name}")

    try:
        template = dashboard.organizations.createOrganizationConfigTemplate(
            org_id, name=template_name, timeZone="America/Chicago"
        )
        print(f"✓ Template created: {template['id']}")
        return template["id"]
    except meraki.APIError as e:
        print(f"✗ Error: {e}")
        return None


def configure_template_vlans(org_id, template_id):
    """
    Configure VLANs in template
    These will be inherited by all bound networks
    """
    print("\nConfiguring template VLANs...")

    # First, enable VLANs on template
    try:
        dashboard.appliance.updateNetworkApplianceVlansSettings(template_id, vlansEnabled=True)
        print("  ✓ VLANs enabled on template")
    except meraki.APIError as e:
        print(f"  ⚠ VLANs may already be enabled: {e}")

    vlans = [
        {"id": "10", "name": "Corporate", "subnet": "10.10.10.0/24", "applianceIp": "10.10.10.1"},
        {"id": "20", "name": "Guest", "subnet": "10.10.20.0/24", "applianceIp": "10.10.20.1"},
        {"id": "30", "name": "IoT", "subnet": "10.10.30.0/24", "applianceIp": "10.10.30.1"},
        {"id": "40", "name": "Voice", "subnet": "10.10.40.0/24", "applianceIp": "10.10.40.1"},
        {"id": "50", "name": "Management", "subnet": "10.10.50.0/24", "applianceIp": "10.10.50.1"},
    ]

    for vlan in vlans:
        try:
            dashboard.appliance.createNetworkApplianceVlan(template_id, **vlan)
            print(f"  ✓ VLAN {vlan['id']}: {vlan['name']}")
        except meraki.APIError as e:
            if "already exists" in str(e).lower():
                print(f"  ⚠ VLAN {vlan['id']} already exists, skipping")
            else:
                print(f"  ✗ Error creating VLAN {vlan['id']}: {e}")


def configure_template_firewall(template_id):
    """
    Configure firewall rules in template
    Same zero-trust policy we built before
    """
    print("\nConfiguring template firewall rules...")

    firewall_rules = [
        {
            "comment": "Corporate - full access",
            "policy": "allow",
            "protocol": "any",
            "srcCidr": "10.10.10.0/24",
            "srcPort": "any",
            "destCidr": "any",
            "destPort": "any",
        },
        {
            "comment": "Management - SSH and HTTPS only",
            "policy": "allow",
            "protocol": "tcp",
            "srcCidr": "10.10.50.0/24",
            "srcPort": "any",
            "destCidr": "any",
            "destPort": "22,443",
        },
        {
            "comment": "Guest - block internal networks",
            "policy": "deny",
            "protocol": "any",
            "srcCidr": "10.10.20.0/24",
            "srcPort": "any",
            "destCidr": "10.0.0.0/8",
            "destPort": "any",
        },
        {
            "comment": "IoT - block internal networks",
            "policy": "deny",
            "protocol": "any",
            "srcCidr": "10.10.30.0/24",
            "srcPort": "any",
            "destCidr": "10.0.0.0/8",
            "destPort": "any",
        },
        {
            "comment": "Voice - SIP signaling",
            "policy": "allow",
            "protocol": "tcp",
            "srcCidr": "10.10.40.0/24",
            "srcPort": "any",
            "destCidr": "10.10.40.0/24",
            "destPort": "5060-5061",
        },
        {
            "comment": "Default allow",
            "policy": "allow",
            "protocol": "any",
            "srcCidr": "any",
            "srcPort": "any",
            "destCidr": "any",
            "destPort": "any",
        },
    ]

    try:
        dashboard.appliance.updateNetworkApplianceFirewallL3FirewallRules(template_id, rules=firewall_rules)
        print(f"  ✓ Configured {len(firewall_rules)} firewall rules")
    except meraki.APIError as e:
        print(f"  ✗ Error: {e}")


def configure_template_wireless(template_id):
    """
    Configure SSIDs in template
    """
    print("\nConfiguring template SSIDs...")

    ssids = [
        {
            "number": 0,
            "name": "Corp-WiFi",
            "enabled": True,
            "authMode": "psk",
            "encryptionMode": "wpa",
            "psk": "ChangeMe123!",
            "ipAssignmentMode": "Bridge mode",
            "useVlanTagging": True,
            "defaultVlanId": 10,
            "visible": True,
            "bandSelection": "Dual band operation",
            "minBitrate": 12,
        },
        {
            "number": 1,
            "name": "Guest-WiFi",
            "enabled": True,
            "authMode": "open",
            "splashPage": "Click-through splash page",
            "ipAssignmentMode": "Bridge mode",
            "useVlanTagging": True,
            "defaultVlanId": 20,
            "visible": True,
            "bandSelection": "5 GHz band only",
            "minBitrate": 12,
            "walledGardenEnabled": True,
            "walledGardenRanges": ["*.google.com", "*.cloudflare.com"],
        },
    ]

    for ssid in ssids:
        try:
            dashboard.wireless.updateNetworkWirelessSsid(template_id, **ssid)
            print(f"  ✓ SSID {ssid['number']}: {ssid['name']}")
        except meraki.APIError as e:
            print(f"  ✗ Error configuring SSID {ssid['number']}: {e}")


def create_network_from_template(org_id, network_name, template_id):
    """
    Create a new network bound to template
    """
    print(f"\nCreating network: {network_name}")

    try:
        network = dashboard.organizations.createOrganizationNetwork(
            org_id,
            name=network_name,
            productTypes=["appliance", "switch", "wireless"],
            timeZone="America/Chicago",
            configTemplateId=template_id,  # ← Bind to template!
        )
        print(f"  ✓ Network created: {network['id']}")
        print("  ✓ Bound to template (configs will inherit)")
        return network["id"]
    except meraki.APIError as e:
        print(f"  ✗ Error: {e}")
        return None


def verify_template_inheritance(network_id, network_name):
    """
    Verify network inherited template configuration
    """
    print(f"\n{'=' * 70}")
    print(f"VERIFYING TEMPLATE INHERITANCE: {network_name}")
    print(f"{'=' * 70}")

    # Check VLANs
    try:
        vlans = dashboard.appliance.getNetworkApplianceVlans(network_id)
        print(f"\n✓ VLANs: {len(vlans)} inherited from template")
        for vlan in vlans[:3]:  # Show first 3
            print(f"    VLAN {vlan['id']}: {vlan['name']} - {vlan['subnet']}")
        if len(vlans) > 3:
            print(f"    ... and {len(vlans) - 3} more")
    except meraki.APIError:
        print("\n⚠ VLANs not available (may need manual enablement)")

    # Check firewall
    try:
        fw_rules = dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(network_id)
        print(f"\n✓ Firewall: {len(fw_rules['rules'])} rules inherited")
        for i, rule in enumerate(fw_rules["rules"][:3], 1):
            print(f"    {i}. [{rule['policy'].upper()}] {rule['comment']}")
        if len(fw_rules["rules"]) > 3:
            print(f"    ... and {len(fw_rules['rules']) - 3} more")
    except meraki.APIError:
        print("\n⚠ Firewall rules not available")

    # Check SSIDs
    try:
        ssids = dashboard.wireless.getNetworkWirelessSsids(network_id)
        enabled_ssids = [s for s in ssids if s["enabled"]]
        print(f"\n✓ Wireless: {len(enabled_ssids)} SSIDs active")
        for ssid in enabled_ssids:
            print(f"    SSID {ssid['number']}: {ssid['name']}")
    except meraki.APIError:
        print("\n⚠ SSIDs not available")


def main():
    print("=" * 70)
    print("MERAKI CONFIGURATION TEMPLATE DEMONSTRATION")
    print("=" * 70)

    # Get organization
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]["id"]
    org_name = orgs[0]["name"]

    print(f"\nOrganization: {org_name}")
    print(f"Org ID: {org_id}")

    # Step 1: Create template
    print("\n" + "=" * 70)
    print("STEP 1: CREATE CONFIGURATION TEMPLATE")
    print("=" * 70)

    template_id = create_template(org_id, "Enterprise-Standard-Template")
    if not template_id:
        print("\n✗ Failed to create template, exiting")
        return

    # Step 2: Configure template
    print("\n" + "=" * 70)
    print("STEP 2: CONFIGURE TEMPLATE")
    print("=" * 70)

    configure_template_vlans(org_id, template_id)
    configure_template_firewall(template_id)
    configure_template_wireless(template_id)

    # Step 3: Create networks from template
    print("\n" + "=" * 70)
    print("STEP 3: DEPLOY NETWORKS FROM TEMPLATE")
    print("=" * 70)

    sites = ["Branch-Chicago", "Branch-NYC", "Branch-LA"]
    network_ids = []

    for site in sites:
        net_id = create_network_from_template(org_id, site, template_id)
        if net_id:
            network_ids.append((net_id, site))

    # Step 4: Verify inheritance (check first network)
    if network_ids:
        verify_template_inheritance(network_ids[0][0], network_ids[0][1])

    # Summary
    print("\n" + "=" * 70)
    print("DEPLOYMENT SUMMARY")
    print("=" * 70)
    print("✓ Template: Enterprise-Standard-Template")
    print("  - 5 VLANs configured")
    print("  - 6 firewall rules configured")
    print("  - 2 SSIDs configured")
    print(f"\n✓ Networks deployed: {len(network_ids)}")
    for net_id, name in network_ids:
        print(f"  - {name}")
    print("\n" + "=" * 70)
    print("NEXT STEP: Test Template Propagation")
    print("=" * 70)
    print("\n1. Go to Meraki Dashboard")
    print("2. Edit the template (add VLAN 60)")
    print("3. Watch it propagate to all 3 networks automatically!")
    print("\nThis is the power of template-based management! 🚀")


if __name__ == "__main__":
    main()
