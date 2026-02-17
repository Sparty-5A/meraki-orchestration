#!/usr/bin/env python3
"""
Bind existing networks to template
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("MERAKI_API_KEY")
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def bind_network_to_template(network_id, network_name, template_id):
    """
    Bind an existing network to a template
    """
    print(f"\nBinding {network_name} to template...")

    try:
        # API requires at least one field + configTemplateId
        result = dashboard.networks.updateNetwork(
            network_id, name=network_name, configTemplateId=template_id  # Keep same name, but required
        )
        print("  ✓ Successfully bound to template")
        return True
    except meraki.APIError as e:
        print(f"  ✗ Error: {e}")
        return False


def verify_binding(network_id, network_name):
    """
    Verify network is bound to template
    """
    try:
        network = dashboard.networks.getNetwork(network_id)
        if "configTemplateId" in network and network["configTemplateId"]:
            print(f"  ✓ {network_name} is bound to template")
            return True
        else:
            print(f"  ✗ {network_name} is NOT bound")
            return False
    except meraki.APIError as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    print("=" * 70)
    print("BIND NETWORKS TO TEMPLATE")
    print("=" * 70)

    # Get organization
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]["id"]

    # Get template
    templates = dashboard.organizations.getOrganizationConfigTemplates(org_id)
    template = [t for t in templates if t["name"] == "Enterprise-Standard-Template"][0]
    template_id = template["id"]

    print(f"\nTemplate: {template['name']}")
    print(f"Template ID: {template_id}")

    # Get networks to bind
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    branch_networks = [n for n in networks if n["name"].startswith("Branch-")]

    print(f"\nFound {len(branch_networks)} branch networks:")
    for net in branch_networks:
        print(f"  - {net['name']}")

    # Bind each network
    print("\n" + "=" * 70)
    print("BINDING TO TEMPLATE")
    print("=" * 70)

    for network in branch_networks:
        bind_network_to_template(network["id"], network["name"], template_id)

    # Verify
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    for network in branch_networks:
        verify_binding(network["id"], network["name"])

    print("\n" + "=" * 70)
    print("✓ BINDING COMPLETE")
    print("=" * 70)
    print("\nVerify the binding worked:")
    print("  uv run check_template_binding.py")


if __name__ == "__main__":
    main()
