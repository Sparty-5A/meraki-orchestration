#!/usr/bin/env python3
"""
Configure Meraki MS switch ports for enterprise office deployment
Demonstrates: Access ports, trunk ports, voice VLAN, PoE, LACP
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("MERAKI_API_KEY")
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def get_switch_serial(network_id):
    """
    Find MS switch in network
    """
    devices = dashboard.networks.getNetworkDevices(network_id)
    switches = [d for d in devices if d["model"].startswith("MS")]

    if switches:
        return switches[0]["serial"]
    else:
        print("No MS switch found in network")
        return None


def configure_workstation_ports(serial, start_port=1, end_port=10):
    """
    Configure workstation ports with voice VLAN
    Typical office desk: PC + IP Phone
    """
    print(f"\nConfiguring Workstation Ports {start_port}-{end_port}...")

    for port in range(start_port, end_port + 1):
        try:
            dashboard.switch.updateDeviceSwitchPort(
                serial,
                portId=str(port),
                name=f"Desk-{port}",
                tags=["workstation", "corporate"],
                enabled=True,
                poeEnabled=True,  # Power for IP phones
                type="access",
                vlan=10,  # Data VLAN (Corporate)
                voiceVlan=40,  # Voice VLAN (for IP phones)
                isolationEnabled=False,
                rstpEnabled=True,
                stpGuard="disabled",
                linkNegotiation="Auto negotiate",
                portScheduleId=None,
                udld="Alert only",
                accessPolicyType="Open",
            )
            print(f"  ✓ Port {port}: Desk-{port} (VLAN 10 data, VLAN 40 voice, PoE)")
        except meraki.APIError as e:
            print(f"  ✗ Port {port}: {e}")


def configure_iot_ports(serial, start_port=11, end_port=15):
    """
    Configure IoT device ports
    Cameras, sensors, access controllers
    """
    print(f"\nConfiguring IoT Ports {start_port}-{end_port}...")

    for port in range(start_port, end_port + 1):
        device_type = ["Camera", "Sensor", "Access-Ctrl", "Camera", "Sensor"][port - start_port]

        try:
            dashboard.switch.updateDeviceSwitchPort(
                serial,
                portId=str(port),
                name=f"IoT-{device_type}-{port}",
                tags=["iot", "security"],
                enabled=True,
                poeEnabled=True,  # Power for cameras/sensors
                type="access",
                vlan=30,  # IoT VLAN
                voiceVlan=None,
                isolationEnabled=False,
                rstpEnabled=True,
                stpGuard="disabled",
                linkNegotiation="Auto negotiate",
                accessPolicyType="Open",
            )
            print(f"  ✓ Port {port}: {device_type} (VLAN 30, PoE)")
        except meraki.APIError as e:
            print(f"  ✗ Port {port}: {e}")


def configure_guest_ports(serial, start_port=16, end_port=20):
    """
    Configure guest/flexible workspace ports
    Conference rooms, hot desks
    """
    print(f"\nConfiguring Guest/Flex Ports {start_port}-{end_port}...")

    for port in range(start_port, end_port + 1):
        try:
            dashboard.switch.updateDeviceSwitchPort(
                serial,
                portId=str(port),
                name=f"Guest-{port}",
                tags=["guest", "flex"],
                enabled=True,
                poeEnabled=True,
                type="access",
                vlan=20,  # Guest VLAN
                voiceVlan=None,
                isolationEnabled=True,  # Isolate guest devices from each other
                rstpEnabled=True,
                stpGuard="disabled",
                linkNegotiation="Auto negotiate",
                accessPolicyType="Open",
            )
            print(f"  ✓ Port {port}: Guest/Flex (VLAN 20, PoE, Isolated)")
        except meraki.APIError as e:
            print(f"  ✗ Port {port}: {e}")


def configure_trunk_ports(serial, ports=[21, 22]):
    """
    Configure trunk ports for uplink to MX
    Carries all VLANs
    """
    print(f"\nConfiguring Trunk Ports {ports}...")

    for port in ports:
        try:
            dashboard.switch.updateDeviceSwitchPort(
                serial,
                portId=str(port),
                name=f"Uplink-MX-{port}",
                tags=["uplink", "trunk"],
                enabled=True,
                poeEnabled=False,  # No PoE needed for uplinks
                type="trunk",
                vlan=1,  # Native VLAN
                allowedVlans="1,10,20,30,40,50",  # All VLANs
                voiceVlan=None,
                isolationEnabled=False,
                rstpEnabled=True,
                stpGuard="disabled",
                linkNegotiation="Auto negotiate",
            )
            print(f"  ✓ Port {port}: Trunk to MX (VLANs: 1,10,20,30,40,50)")
        except meraki.APIError as e:
            print(f"  ✗ Port {port}: {e}")


def configure_management_ports(serial, ports=[23, 24]):
    """
    Configure management ports
    Out-of-band management access
    """
    print(f"\nConfiguring Management Ports {ports}...")

    for port in ports:
        try:
            dashboard.switch.updateDeviceSwitchPort(
                serial,
                portId=str(port),
                name=f"Mgmt-{port}",
                tags=["management"],
                enabled=True,
                poeEnabled=False,
                type="access",
                vlan=50,  # Management VLAN
                voiceVlan=None,
                isolationEnabled=False,
                rstpEnabled=True,
                stpGuard="disabled",
                linkNegotiation="Auto negotiate",
                accessPolicyType="Open",
            )
            print(f"  ✓ Port {port}: Management (VLAN 50)")
        except meraki.APIError as e:
            print(f"  ✗ Port {port}: {e}")


def verify_switch_config(serial):
    """
    Verify switch port configuration
    """
    print(f"\n{'=' * 70}")
    print("SWITCH PORT CONFIGURATION SUMMARY")
    print(f"{'=' * 70}")

    try:
        ports = dashboard.switch.getDeviceSwitchPorts(serial)

        # Group by type
        access_ports = [p for p in ports if p.get("type") == "access"]
        trunk_ports = [p for p in ports if p.get("type") == "trunk"]

        print(f"\nTotal Ports: {len(ports)}")
        print(f"Access Ports: {len(access_ports)}")
        print(f"Trunk Ports: {len(trunk_ports)}")

        # Show first few of each type
        print(f"\n{'Port':<6} {'Name':<20} {'Type':<8} {'VLAN':<8} {'Voice':<8} {'PoE':<6}")
        print("-" * 70)

        for port in ports[:24]:  # Show all 24 ports
            port_id = port.get("portId", "N/A")
            name = port.get("name", "Unconfigured")[:18]
            port_type = port.get("type", "N/A")
            vlan = str(port.get("vlan", "N/A"))
            voice = str(port.get("voiceVlan", "-"))
            poe = "Yes" if port.get("poeEnabled") else "No"

            print(f"{port_id:<6} {name:<20} {port_type:<8} {vlan:<8} {voice:<8} {poe:<6}")

    except meraki.APIError as e:
        print(f"Error retrieving ports: {e}")


def main():
    print("=" * 70)
    print("MERAKI MS SWITCH PORT CONFIGURATION")
    print("=" * 70)

    # Get organization
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]["id"]

    # Use the branch office network (the one with actual devices)
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    branch_office = [n for n in networks if "branch office" in n["name"].lower()][0]
    network_id = branch_office["id"]

    print(f"\nNetwork: {branch_office['name']}")
    print(f"Network ID: {network_id}")

    # Get switch serial
    switch_serial = get_switch_serial(network_id)
    if not switch_serial:
        print("\nNo switch found - cannot continue")
        return

    print(f"Switch Serial: {switch_serial}")

    # Configure ports by function
    print("\n" + "=" * 70)
    print("CONFIGURING SWITCH PORTS")
    print("=" * 70)

    configure_workstation_ports(switch_serial, 1, 10)
    configure_iot_ports(switch_serial, 11, 15)
    configure_guest_ports(switch_serial, 16, 20)
    configure_trunk_ports(switch_serial, [21, 22])
    configure_management_ports(switch_serial, [23, 24])

    # Verify
    verify_switch_config(switch_serial)

    print("\n" + "=" * 70)
    print("SWITCH CONFIGURATION COMPLETE")
    print("=" * 70)
    print("\nKey Learnings:")
    print("  ✓ Access ports: Single VLAN per port")
    print("  ✓ Trunk ports: Multiple VLANs (tagged)")
    print("  ✓ Voice VLAN: Separate VLAN for IP phones")
    print("  ✓ PoE: Power over Ethernet for phones/cameras")
    print("  ✓ Port isolation: Guest devices can't talk to each other")


if __name__ == "__main__":
    main()
