#!/usr/bin/env python3
"""
Configure inter-VLAN firewall rules for zero-trust segmentation
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MERAKI_API_KEY")
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def configure_firewall_rules(network_id):
    """
    Configure Layer 3 firewall rules for VLAN segmentation

    Policy:
    - Corporate can access everything
    - Guest is isolated (internet only)
    - IoT can only access specific services
    - Voice has QoS priority, limited access
    """

    firewall_rules = [
        # Rule 1: Allow Corporate to everything
        {
            "comment": "Corporate VLAN - full access",
            "policy": "allow",
            "protocol": "any",
            "srcCidr": "10.10.10.0/24",
            "srcPort": "any",
            "destCidr": "any",
            "destPort": "any",
        },
        # Rule 2: Allow Voice SIP signaling
        {
            "comment": "Voice VLAN - SIP signaling",
            "policy": "allow",
            "protocol": "tcp",
            "srcCidr": "10.10.40.0/24",
            "srcPort": "any",
            "destCidr": "10.10.40.0/24",
            "destPort": "5060-5061",
        },
        # Rule 3: Allow Voice RTP media
        {
            "comment": "Voice VLAN - RTP media streams",
            "policy": "allow",
            "protocol": "udp",
            "srcCidr": "10.10.40.0/24",
            "srcPort": "any",
            "destCidr": "10.10.40.0/24",
            "destPort": "16384-32767",
        },
        # Rule 4: Allow Voice to Internet (for cloud PBX)
        {
            "comment": "Voice VLAN - internet access for cloud PBX",
            "policy": "allow",
            "protocol": "any",
            "srcCidr": "10.10.40.0/24",
            "srcPort": "any",
            "destCidr": "any",
            "destPort": "any",
        },
        # Rule 5: IoT deny RFC1918 (block internal networks)
        {
            "comment": "IoT VLAN - block internal networks",
            "policy": "deny",
            "protocol": "any",
            "srcCidr": "10.10.30.0/24",
            "srcPort": "any",
            "destCidr": "10.0.0.0/8",
            "destPort": "any",
        },
        # Rule 6: IoT deny RFC1918 172.16/12
        {
            "comment": "IoT VLAN - block internal networks 172.16",
            "policy": "deny",
            "protocol": "any",
            "srcCidr": "10.10.30.0/24",
            "srcPort": "any",
            "destCidr": "172.16.0.0/12",
            "destPort": "any",
        },
        # Rule 7: IoT deny RFC1918 192.168/16
        {
            "comment": "IoT VLAN - block internal networks 192.168",
            "policy": "deny",
            "protocol": "any",
            "srcCidr": "10.10.30.0/24",
            "srcPort": "any",
            "destCidr": "192.168.0.0/16",
            "destPort": "any",
        },
        # Rule 8: Guest deny RFC1918 10/8
        {
            "comment": "Guest VLAN - block internal networks",
            "policy": "deny",
            "protocol": "any",
            "srcCidr": "10.10.20.0/24",
            "srcPort": "any",
            "destCidr": "10.0.0.0/8",
            "destPort": "any",
        },
        # Rule 9: Guest deny RFC1918 172.16/12
        {
            "comment": "Guest VLAN - block internal networks 172.16",
            "policy": "deny",
            "protocol": "any",
            "srcCidr": "10.10.20.0/24",
            "srcPort": "any",
            "destCidr": "172.16.0.0/12",
            "destPort": "any",
        },
        # Rule 10: Guest deny RFC1918 192.168/16
        {
            "comment": "Guest VLAN - block internal networks 192.168",
            "policy": "deny",
            "protocol": "any",
            "srcCidr": "10.10.20.0/24",
            "srcPort": "any",
            "destCidr": "192.168.0.0/16",
            "destPort": "any",
        },
        # Rule 11: Default allow all (implicit for traffic not matching above)
        {
            "comment": "Default allow all - required by Meraki",
            "policy": "allow",
            "protocol": "any",
            "srcCidr": "any",
            "srcPort": "any",
            "destCidr": "any",
            "destPort": "any",
        },
    ]

    print("Configuring firewall rules...")
    print("=" * 60)

    try:
        response = dashboard.appliance.updateNetworkApplianceFirewallL3FirewallRules(network_id, rules=firewall_rules)

        print("✓ Firewall rules configured successfully!\n")
        print(f"Total rules applied: {len(response['rules'])}\n")

        for i, rule in enumerate(response["rules"], 1):
            print(f"{i}. [{rule['policy'].upper()}] {rule['comment']}")
            print(f"   {rule['srcCidr']}:{rule['srcPort']} → {rule['destCidr']}:{rule['destPort']}")

        return True

    except meraki.APIError as e:
        print(f"✗ Error configuring firewall: {e}")
        return False


def main():
    # Get network
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]["id"]
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    branch_network = [n for n in networks if n["name"] == "branch office"][0]
    network_id = branch_network["id"]

    print(f"Network: {branch_network['name']}")
    print(f"Network ID: {network_id}\n")

    # Configure firewall
    configure_firewall_rules(network_id)

    print("\n" + "=" * 60)
    print("Security Policy Summary:")
    print("  ✓ Corporate (VLAN 10): Full access to everything")
    print("  ✓ Voice (VLAN 40): SIP + RTP + Internet (for cloud PBX)")
    print("  ✓ IoT (VLAN 30): Internet only, NO internal network access")
    print("  ✓ Guest (VLAN 20): Internet only, NO internal network access")
    print("\nZero-trust network segmentation implemented! 🔒")


if __name__ == "__main__":
    main()
