#!/usr/bin/env python3
"""
Check template binding status
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("MERAKI_API_KEY")
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def main():
    print("=" * 70)
    print("TEMPLATE BINDING DIAGNOSTIC")
    print("=" * 70)

    # Get organization
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]["id"]

    # Get all templates
    print("\nConfiguration Templates:")
    print("-" * 70)
    templates = dashboard.organizations.getOrganizationConfigTemplates(org_id)
    for template in templates:
        print(f"  Template: {template['name']}")
        print(f"  ID: {template['id']}")
        print()

    # Get all networks
    print("Networks and Their Template Binding:")
    print("-" * 70)
    networks = dashboard.organizations.getOrganizationNetworks(org_id)

    for network in networks:
        print(f"\nNetwork: {network['name']}")
        print(f"  ID: {network['id']}")
        print(f"  Products: {', '.join(network['productTypes'])}")

        # Check if bound to template
        if "configTemplateId" in network and network["configTemplateId"]:
            print(f"  ✓ Bound to template: {network['configTemplateId']}")

            # Try to get template name
            template_name = "Unknown"
            for t in templates:
                if t["id"] == network["configTemplateId"]:
                    template_name = t["name"]
                    break
            print(f"  ✓ Template name: {template_name}")
        else:
            print("  ✗ NOT bound to any template")

        # Try to check VLANs
        try:
            vlan_settings = dashboard.appliance.getNetworkApplianceVlansSettings(network["id"])
            print(f"  VLANs enabled: {vlan_settings.get('vlansEnabled', False)}")
        except Exception as e:
            print(f"  VLAN settings: {e}")

    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
