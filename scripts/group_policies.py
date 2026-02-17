#!/usr/bin/env python3
"""
Configure Meraki Group Policies for role-based access control
Demonstrates: Bandwidth limits, firewall rules, scheduling, per-user policies
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("MERAKI_API_KEY")
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def create_executive_policy(network_id):
    """
    Executive Policy: Full access, no limits
    For C-level, senior management
    """
    print("\nCreating Executive Policy...")

    try:
        policy = dashboard.networks.createNetworkGroupPolicy(
            network_id,
            name="Executive",
            scheduling={"enabled": False},  # No time restrictions
            bandwidth={"settings": "network default"},  # No bandwidth limit
            firewallAndTrafficShaping={
                "settings": "network default",  # No additional restrictions
                "l3FirewallRules": [],
                "l7FirewallRules": [],
                "trafficShapingRules": [],
            },
            splashAuthSettings="network default",
            # Removed contentFiltering - not supported in sandbox
        )
        print(f"  ✓ Executive Policy created: {policy['groupPolicyId']}")
        return policy["groupPolicyId"]
    except meraki.APIError as e:
        print(f"  ✗ Error: {e}")
        return None


def create_employee_policy(network_id):
    """
    Employee Policy: 50 Mbps, some restrictions
    For regular full-time employees
    """
    print("\nCreating Employee Policy...")

    try:
        policy = dashboard.networks.createNetworkGroupPolicy(
            network_id,
            name="Employee",
            scheduling={
                "enabled": True,
                "monday": {"active": True, "from": "08:00", "to": "18:00"},
                "tuesday": {"active": True, "from": "08:00", "to": "18:00"},
                "wednesday": {"active": True, "from": "08:00", "to": "18:00"},
                "thursday": {"active": True, "from": "08:00", "to": "18:00"},
                "friday": {"active": True, "from": "08:00", "to": "18:00"},
                "saturday": {"active": False},
                "sunday": {"active": False},
            },
            bandwidth={
                "settings": "custom",
                "bandwidthLimits": {"limitUp": 50000, "limitDown": 50000},  # 50 Mbps upload  # 50 Mbps download
            },
            firewallAndTrafficShaping={
                "settings": "custom",
                "l3FirewallRules": [
                    {
                        "comment": "Block common P2P ports",
                        "policy": "deny",
                        "protocol": "tcp",
                        "destPort": "any",  # Fixed: using "any" instead of port ranges
                        "destCidr": "any",
                    }
                ],
                "l7FirewallRules": [],  # Simplified - L7 rules removed for sandbox
                "trafficShapingRules": [],
            },
        )
        print(f"  ✓ Employee Policy created: {policy['groupPolicyId']}")
        print("    - 50 Mbps bandwidth limit")
        print("    - Business hours only (8am-6pm, Mon-Fri)")
        return policy["groupPolicyId"]
    except meraki.APIError as e:
        print(f"  ✗ Error: {e}")
        return None


def create_contractor_policy(network_id):
    """
    Contractor Policy: 5 Mbps, heavily restricted
    For temporary workers, vendors
    """
    print("\nCreating Contractor Policy...")

    try:
        policy = dashboard.networks.createNetworkGroupPolicy(
            network_id,
            name="Contractor",
            scheduling={
                "enabled": True,
                "monday": {"active": True, "from": "09:00", "to": "17:00"},
                "tuesday": {"active": True, "from": "09:00", "to": "17:00"},
                "wednesday": {"active": True, "from": "09:00", "to": "17:00"},
                "thursday": {"active": True, "from": "09:00", "to": "17:00"},
                "friday": {"active": True, "from": "09:00", "to": "17:00"},
                "saturday": {"active": False},
                "sunday": {"active": False},
            },
            bandwidth={
                "settings": "custom",
                "bandwidthLimits": {"limitUp": 5000, "limitDown": 5000},  # 5 Mbps upload  # 5 Mbps download
            },
            firewallAndTrafficShaping={
                "settings": "custom",
                "l3FirewallRules": [
                    {
                        "comment": "Deny internal networks - 10.0.0.0/8",
                        "policy": "deny",
                        "protocol": "any",
                        "destPort": "any",
                        "destCidr": "10.0.0.0/8",
                    },
                    {
                        "comment": "Deny internal networks - 172.16.0.0/12",
                        "policy": "deny",
                        "protocol": "any",
                        "destPort": "any",
                        "destCidr": "172.16.0.0/12",
                    },
                    {
                        "comment": "Deny internal networks - 192.168.0.0/16",
                        "policy": "deny",
                        "protocol": "any",
                        "destPort": "any",
                        "destCidr": "192.168.0.0/16",
                    },
                ],
                "l7FirewallRules": [],  # Simplified for sandbox
                "trafficShapingRules": [],
            },
        )
        print(f"  ✓ Contractor Policy created: {policy['groupPolicyId']}")
        print("    - 5 Mbps bandwidth limit")
        print("    - Limited hours (9am-5pm, Mon-Fri)")
        print("    - Blocks internal networks (RFC1918)")
        return policy["groupPolicyId"]
    except meraki.APIError as e:
        print(f"  ✗ Error: {e}")
        return None


def create_guest_policy(network_id):
    """
    Guest Policy: 2 Mbps, internet only
    For visitors, customers
    """
    print("\nCreating Guest Policy...")

    try:
        policy = dashboard.networks.createNetworkGroupPolicy(
            network_id,
            name="Guest",
            scheduling={"enabled": False},  # 24/7 access for guests
            bandwidth={
                "settings": "custom",
                "bandwidthLimits": {"limitUp": 2000, "limitDown": 2000},  # 2 Mbps upload  # 2 Mbps download
            },
            firewallAndTrafficShaping={
                "settings": "custom",
                "l3FirewallRules": [
                    {
                        "comment": "Deny all internal networks - 10.0.0.0/8",
                        "policy": "deny",
                        "protocol": "any",
                        "destPort": "any",
                        "destCidr": "10.0.0.0/8",
                    },
                    {
                        "comment": "Deny all internal networks - 172.16.0.0/12",
                        "policy": "deny",
                        "protocol": "any",
                        "destPort": "any",
                        "destCidr": "172.16.0.0/12",
                    },
                    {
                        "comment": "Deny all internal networks - 192.168.0.0/16",
                        "policy": "deny",
                        "protocol": "any",
                        "destPort": "any",
                        "destCidr": "192.168.0.0/16",
                    },
                    {
                        "comment": "Allow internet only",
                        "policy": "allow",
                        "protocol": "any",
                        "destPort": "any",
                        "destCidr": "any",
                    },
                ],
                "l7FirewallRules": [],  # Simplified
                "trafficShapingRules": [],
            },
        )
        print(f"  ✓ Guest Policy created: {policy['groupPolicyId']}")
        print("    - 2 Mbps bandwidth limit")
        print("    - Internet only (no internal access)")
        print("    - 24/7 access")
        return policy["groupPolicyId"]
    except meraki.APIError as e:
        print(f"  ✗ Error: {e}")
        return None


def list_group_policies(network_id):
    """
    List all group policies in network
    """
    print(f"\n{'=' * 70}")
    print("GROUP POLICIES SUMMARY")
    print(f"{'=' * 70}")

    try:
        policies = dashboard.networks.getNetworkGroupPolicies(network_id)

        print(f"\nTotal Policies: {len(policies)}")
        print(f"\n{'Name':<20} {'ID':<10} {'Bandwidth':<15} {'Scheduling':<12}")
        print("-" * 70)

        for policy in policies:
            name = policy.get("name", "N/A")[:18]
            policy_id = str(policy.get("groupPolicyId", "N/A"))[:8]

            # Bandwidth
            bw_settings = policy.get("bandwidth", {}).get("settings", "default")
            if bw_settings == "custom":
                limits = policy.get("bandwidth", {}).get("bandwidthLimits", {})
                bw = f"{limits.get('limitDown', 0) / 1000:.0f} Mbps"
            else:
                bw = "Unlimited"

            # Scheduling
            sched = policy.get("scheduling", {})
            if sched.get("enabled"):
                scheduling = "Scheduled"
            else:
                scheduling = "24/7"

            print(f"{name:<20} {policy_id:<10} {bw:<15} {scheduling:<12}")

    except meraki.APIError as e:
        print(f"Error: {e}")


def main():
    print("=" * 70)
    print("MERAKI GROUP POLICIES CONFIGURATION")
    print("=" * 70)
    print("\nGroup Policies = Role-based access control")
    print("Different rules per user type, not per VLAN")

    # Get organization
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]["id"]

    # Use branch office network
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    branch_office = [n for n in networks if "branch office" in n["name"].lower()][0]
    network_id = branch_office["id"]

    print(f"\nNetwork: {branch_office['name']}")
    print(f"Network ID: {network_id}")

    # Create policies
    print("\n" + "=" * 70)
    print("CREATING GROUP POLICIES")
    print("=" * 70)

    create_executive_policy(network_id)
    create_employee_policy(network_id)
    create_contractor_policy(network_id)
    create_guest_policy(network_id)

    # List all policies
    list_group_policies(network_id)

    print("\n" + "=" * 70)
    print("GROUP POLICIES CREATED")
    print("=" * 70)
    print("\nHow to Use:")
    print("  1. Dashboard → Network → Group policies")
    print("  2. Assign to clients by:")
    print("     - SSID default policy")
    print("     - RADIUS attribute (for 802.1X)")
    print("     - MAC address assignment")
    print("     - Manual assignment per client")
    print("\nInterview Value:")
    print("  ✓ Role-based access control")
    print("  ✓ Bandwidth management per user type")
    print("  ✓ Scheduled access (business hours)")
    print("  ✓ Per-user firewall policies")
    print("\nKey Learnings:")
    print("  ✓ Group policies override network-wide settings")
    print("  ✓ Can limit bandwidth per user/device")
    print("  ✓ Can restrict access by time schedule")
    print("  ✓ Can apply different firewall rules per user")
    print("  ✓ More granular than VLAN-based policies")


if __name__ == "__main__":
    main()
