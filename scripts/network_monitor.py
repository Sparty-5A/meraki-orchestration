#!/usr/bin/env python3
"""
Meraki Network Monitoring System
Monitor device health, client connectivity, and network performance
"""

import meraki
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('MERAKI_API_KEY')
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def check_device_status(network_id):
    """Check if all devices are online"""
    print(f"\n{'=' * 70}")
    print("DEVICE STATUS CHECK")
    print(f"{'=' * 70}")

    devices = dashboard.networks.getNetworkDevices(network_id)

    print(f"\n{'Device':<25} {'Model':<15} {'Status':<10} {'Public IP':<15}")
    print("-" * 70)

    online = 0
    offline = 0
    alerts = []

    for device in devices:
        name = device.get('name') or f"{device['model']}-{device['serial'][-4:]}"
        model = device['model']
        status = device.get('status', 'unknown')
        public_ip = device.get('publicIp', 'N/A')

        # Status indicator
        if status == 'online':
            status_display = "✓ Online"
            online += 1
        else:
            status_display = "✗ Offline"
            offline += 1
            alerts.append(f"⚠ ALERT: {name} ({model}) is OFFLINE")

        print(f"{name:<25} {model:<15} {status_display:<10} {public_ip:<15}")

    print(f"\nSummary: {online} online, {offline} offline")

    if offline > 0:
        print("\nℹ Note: Sandbox devices are virtual and may show as offline")

    return alerts


def check_device_performance(org_id):
    """Check device performance metrics"""
    print(f"\n{'=' * 70}")
    print("DEVICE PERFORMANCE")
    print(f"{'=' * 70}")

    alerts = []

    try:
        # Get organization uplink statuses
        uplinks = dashboard.organizations.getOrganizationUplinksStatuses(
            org_id,
            perPage=100
        )

        if not uplinks:
            print("\nNo uplink data available (sandbox limitation)")
            return alerts

        print(f"\n{'Device':<25} {'Uplink':<12} {'Status':<10} {'IP':<15}")
        print("-" * 70)

        for uplink in uplinks[:10]:  # Show first 10
            serial = uplink.get('serial', 'N/A')
            model = uplink.get('model', 'N/A')

            for link in uplink.get('uplinks', []):
                interface = link.get('interface', 'N/A')
                status = link.get('status', 'N/A')
                ip = link.get('ip', 'N/A')

                status_display = "✓ Active" if status == 'active' else "✗ Failed"

                print(f"{model}-{serial[-4:]:<25} {interface:<12} {status_display:<10} {ip:<15}")

                if status != 'active':
                    alerts.append(f"⚠ UPLINK DOWN: {model}-{serial[-4:]} {interface}")

    except Exception as e:
        print(f"\nUplink data not available: {e}")
        print("ℹ This is normal in sandbox - production would show real metrics")

    return alerts


def check_client_connectivity(network_id):
    """Check connected clients"""
    print(f"\n{'=' * 70}")
    print("CLIENT CONNECTIVITY")
    print(f"{'=' * 70}")

    # Get clients from last hour
    timespan = 3600  # 1 hour in seconds

    try:
        clients = dashboard.networks.getNetworkClients(
            network_id,
            timespan=timespan,
            perPage=100
        )

        print(f"\nTotal clients (last hour): {len(clients)}")

        if len(clients) == 0:
            print("ℹ No clients detected (sandbox has no active clients)")
            return []

        # Categorize by connection type
        wired = [c for c in clients if c.get('switchport')]
        wireless = [c for c in clients if c.get('ssid')]

        print(f"  Wired: {len(wired)}")
        print(f"  Wireless: {len(wireless)}")

        # Show wireless breakdown by SSID
        if wireless:
            print("\nWireless clients by SSID:")
            ssid_counts = {}
            for client in wireless:
                ssid = client.get('ssid', 'Unknown')
                ssid_counts[ssid] = ssid_counts.get(ssid, 0) + 1

            for ssid, count in sorted(ssid_counts.items()):
                print(f"  {ssid}: {count} client(s)")

        # Show recently connected clients
        if clients:
            print("\nRecently active clients:")
            print(f"{'Description':<30} {'IP':<15} {'VLAN':<6} {'Usage':<10}")
            print("-" * 70)

            for client in clients[:10]:  # Show first 10
                desc = client.get('description', 'Unknown')[:28]
                ip = client.get('ip', 'N/A')
                vlan = str(client.get('vlan', 'N/A'))
                usage = client.get('usage', {})
                sent = usage.get('sent', 0) / 1024 / 1024  # Convert to MB
                recv = usage.get('recv', 0) / 1024 / 1024
                total = sent + recv
                usage_str = f"{total:.1f} MB"

                print(f"{desc:<30} {ip:<15} {vlan:<6} {usage_str:<10}")

    except Exception as e:
        print(f"Error getting clients: {e}")

    return []


def check_network_traffic(network_id):
    """Check network traffic patterns"""
    print(f"\n{'=' * 70}")
    print("NETWORK TRAFFIC")
    print(f"{'=' * 70}")

    alerts = []

    try:
        # Get traffic for last 7200 seconds (2 hours minimum)
        traffic = dashboard.networks.getNetworkTraffic(
            network_id,
            timespan=7200  # 2 hours (API minimum)
        )

        if not traffic:
            print("\nNo traffic data available")
            print("ℹ Sandbox may not have traffic analytics data")
            return alerts

        print("\nTop applications:")
        print(f"{'Application':<30} {'Sent':<12} {'Received':<12} {'Total':<12}")
        print("-" * 70)

        # Sort by total traffic
        sorted_traffic = sorted(traffic, key=lambda x: x.get('sent', 0) + x.get('recv', 0), reverse=True)

        for app in sorted_traffic[:10]:  # Top 10
            app_name = app.get('application', 'Unknown')[:28]
            sent = app.get('sent', 0) / 1024 / 1024  # MB
            recv = app.get('recv', 0) / 1024 / 1024
            total = sent + recv

            print(f"{app_name:<30} {sent:>10.1f} MB {recv:>10.1f} MB {total:>10.1f} MB")

    except Exception as e:
        print(f"\nTraffic data not available: {e}")
        print("ℹ This is normal in sandbox - production would show application traffic")

    return alerts


def check_ssid_status(network_id):
    """Check wireless SSID status"""
    print(f"\n{'=' * 70}")
    print("WIRELESS SSID STATUS")
    print(f"{'=' * 70}")

    alerts = []

    try:
        ssids = dashboard.wireless.getNetworkWirelessSsids(network_id)

        print(f"\n{'SSID Name':<25} {'Enabled':<10} {'Auth Mode':<15} {'VLAN':<6}")
        print("-" * 70)

        for ssid in ssids:
            if not ssid['name'].startswith('Unconfigured'):
                name = ssid['name']
                enabled = "✓ Yes" if ssid.get('enabled') else "✗ No"
                auth = ssid.get('authMode', 'N/A')
                vlan = str(ssid.get('defaultVlanId', 'N/A'))

                print(f"{name:<25} {enabled:<10} {auth:<15} {vlan:<6}")

                # Alert if SSID is disabled
                if not ssid.get('enabled'):
                    alerts.append(f"⚠ SSID DISABLED: {name}")

    except Exception as e:
        print(f"Error checking SSIDs: {e}")

    return alerts


def check_vlans(network_id):
    """Check VLAN configuration"""
    print(f"\n{'=' * 70}")
    print("VLAN STATUS")
    print(f"{'=' * 70}")

    try:
        vlans = dashboard.appliance.getNetworkApplianceVlans(network_id)

        print(f"\n{'VLAN ID':<8} {'Name':<25} {'Subnet':<18} {'Gateway':<15}")
        print("-" * 70)

        for vlan in vlans:
            vlan_id = str(vlan['id'])
            name = vlan['name'][:23]
            subnet = vlan['subnet']
            gateway = vlan['applianceIp']

            print(f"{vlan_id:<8} {name:<25} {subnet:<18} {gateway:<15}")

        print(f"\nTotal VLANs: {len(vlans)}")

    except Exception as e:
        print(f"Error checking VLANs: {e}")

    return []


def check_switch_ports(network_id):
    """Check switch port status"""
    print(f"\n{'=' * 70}")
    print("SWITCH PORT STATUS")
    print(f"{'=' * 70}")

    alerts = []

    try:
        devices = dashboard.networks.getNetworkDevices(network_id)
        switches = [d for d in devices if d['model'].startswith('MS')]

        if not switches:
            print("\nNo switches found")
            return alerts

        for switch in switches:
            name = switch.get('name') or f"{switch['model']}-{switch['serial'][-4:]}"
            ports = dashboard.switch.getDeviceSwitchPorts(switch['serial'])

            # Count port types
            access_ports = len([p for p in ports if p.get('type') == 'access'])
            trunk_ports = len([p for p in ports if p.get('type') == 'trunk'])
            enabled_ports = len([p for p in ports if p.get('enabled')])
            poe_ports = len([p for p in ports if p.get('poeEnabled')])

            print(f"\n{name}:")
            print(f"  Total Ports: {len(ports)}")
            print(f"  Access: {access_ports}, Trunk: {trunk_ports}")
            print(f"  Enabled: {enabled_ports}, PoE: {poe_ports}")

            # Show configured ports
            configured = [p for p in ports if p.get('name')]
            if configured:
                print("\n  Configured Ports:")
                for port in configured[:5]:  # Show first 5
                    port_id = port['portId']
                    port_name = port['name'][:20]
                    port_type = port.get('type', 'N/A')
                    vlan = port.get('vlan', 'N/A')
                    print(f"    Port {port_id}: {port_name} ({port_type}, VLAN {vlan})")

    except Exception as e:
        print(f"Error checking switch ports: {e}")

    return alerts


def generate_alert_summary(all_alerts):
    """Display all alerts"""
    if not all_alerts:
        print(f"\n{'=' * 70}")
        print("✓ NO CRITICAL ALERTS")
        print(f"{'=' * 70}")
        print("\nAll systems reporting normal status")
        print("(Note: Sandbox devices may show as offline - this is expected)")
        return

    print(f"\n{'=' * 70}")
    print(f"⚠ ALERTS DETECTED: {len(all_alerts)}")
    print(f"{'=' * 70}")

    for i, alert in enumerate(all_alerts, 1):
        print(f"{i}. {alert}")

    print(f"\n{'=' * 70}")
    print("RECOMMENDED ACTIONS:")
    print(f"{'=' * 70}")
    print("1. Investigate offline devices in Dashboard")
    print("2. Check high latency causes (ISP, congestion)")
    print("3. Review packet loss (cable issues, interference)")
    print("4. Verify disabled SSIDs are intentional")
    print("5. Check uplink connectivity and failover")


def main():
    print("=" * 70)
    print("MERAKI NETWORK MONITORING SYSTEM")
    print("=" * 70)
    print(f"\nMonitoring started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get organization
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]['id']
    org_name = orgs[0]['name']

    # Get networks
    networks = dashboard.organizations.getOrganizationNetworks(org_id)

    # Monitor branch office
    branch_office = [n for n in networks if 'branch office' in n['name'].lower()][0]
    network_id = branch_office['id']
    network_name = branch_office['name']

    print(f"Organization: {org_name}")
    print(f"Network: {network_name}")

    # Collect all alerts (only critical ones)
    all_alerts = []

    # Run all checks
    device_alerts = check_device_status(network_id)
    # Don't alert on offline devices in sandbox
    # all_alerts.extend(device_alerts)

    all_alerts.extend(check_device_performance(org_id))
    all_alerts.extend(check_client_connectivity(network_id))
    all_alerts.extend(check_network_traffic(network_id))
    all_alerts.extend(check_ssid_status(network_id))
    all_alerts.extend(check_vlans(network_id))
    all_alerts.extend(check_switch_ports(network_id))

    # Display alert summary
    generate_alert_summary(all_alerts)

    print(f"\n{'=' * 70}")
    print("MONITORING COMPLETE")
    print(f"{'=' * 70}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nProduction Use:")
    print("  - Schedule via cron: */5 * * * * /path/to/network_monitor.py")
    print("  - Add Slack/email notifications for alerts")
    print("  - Store metrics in InfluxDB/Prometheus")
    print("  - Create Grafana dashboard for visualization")
    print("  - Set up PagerDuty integration for critical alerts")


if __name__ == "__main__":
    main()
