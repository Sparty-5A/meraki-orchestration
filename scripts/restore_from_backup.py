#!/usr/bin/env python3
"""
Meraki Configuration Restore Tool
Restore network configuration from backup (disaster recovery)
"""

import meraki
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('MERAKI_API_KEY')
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True, maximum_retries=3)

BACKUP_DIR = Path("backups")


def list_backups():
    """List all available backups"""
    backups = sorted(BACKUP_DIR.glob("backup_*.json"), reverse=True)

    print(f"\n{'=' * 70}")
    print("AVAILABLE BACKUPS")
    print(f"{'=' * 70}")

    if not backups:
        print("No backups found")
        return []

    print(f"\n{'#':<4} {'Network':<30} {'Date':<20} {'Size':<10}")
    print("-" * 70)

    for i, backup_file in enumerate(backups, 1):
        try:
            with open(backup_file) as f:
                data = json.load(f)

            network_name = data['metadata']['network_name']
            timestamp = data['metadata']['timestamp']
            size = backup_file.stat().st_size / 1024

            dt = datetime.fromisoformat(timestamp)
            date_str = dt.strftime('%Y-%m-%d %H:%M:%S')

            print(f"{i:<4} {network_name:<30} {date_str:<20} {size:>6.1f} KB")
        except:
            print(f"{i:<4} {backup_file.name:<30} [Error]")

    return backups


def restore_vlans(network_id, vlans_backup):
    """Restore VLANs (careful - this is destructive!)"""
    print("\n[1/5] Restoring VLANs...")

    # Get current VLANs
    try:
        current_vlans = dashboard.appliance.getNetworkApplianceVlans(network_id)
        current_vlan_ids = {v['id'] for v in current_vlans}
    except:
        current_vlan_ids = set()

    backup_vlan_ids = {v['id'] for v in vlans_backup}

    # Create/update VLANs from backup
    for vlan in vlans_backup:
        try:
            if vlan['id'] in current_vlan_ids:
                # Update existing
                dashboard.appliance.updateNetworkApplianceVlan(
                    network_id,
                    vlan['id'],
                    name=vlan['name'],
                    subnet=vlan['subnet'],
                    applianceIp=vlan['applianceIp']
                )
                print(f"  ✓ Updated VLAN {vlan['id']}: {vlan['name']}")
            else:
                # Create new
                dashboard.appliance.createNetworkApplianceVlan(
                    network_id,
                    id=str(vlan['id']),
                    name=vlan['name'],
                    subnet=vlan['subnet'],
                    applianceIp=vlan['applianceIp']
                )
                print(f"  ✓ Created VLAN {vlan['id']}: {vlan['name']}")
        except Exception as e:
            print(f"  ⚠ VLAN {vlan['id']}: {e}")


def restore_firewall_rules(network_id, firewall_backup):
    """Restore firewall rules - filter out default allow rules"""
    print("\n[2/5] Restoring firewall rules...")

    try:
        rules = firewall_backup.get('rules', [])

        # Filter out ALL default allow-all rules
        # Keep only rules with specific purposes (deny rules, specific allows)
        explicit_rules = []
        for rule in rules:
            comment = rule.get('comment', '').lower()
            policy = rule.get('policy', '')
            dest = rule.get('destCidr', '')

            # Skip any "default" allow-all rules
            if 'default' in comment and policy == 'allow' and dest in ['Any', 'any']:
                print(f"  ⊘ Skipping default rule: '{rule.get('comment')}'")
                continue

            # Keep everything else (your actual security rules)
            explicit_rules.append(rule)

        print(f"  ℹ Restoring {len(explicit_rules)} explicit security rules")
        print(f"  ℹ Meraki will add its own default allow rule automatically")

        # Replace all rules with filtered set
        dashboard.appliance.updateNetworkApplianceFirewallL3FirewallRules(
            network_id,
            rules=explicit_rules
        )

        print(f"  ✓ Firewall rules restored")

    except Exception as e:
        print(f"  ⚠ Firewall rules: {e}")


def restore_ssids(network_id, ssids_backup):
    """Restore wireless SSIDs"""
    print("\n[3/5] Restoring wireless SSIDs...")

    for ssid in ssids_backup:
        try:
            number = ssid['number']

            # Build update parameters (only include what's in backup)
            params = {
                'name': ssid['name'],
                'enabled': ssid.get('enabled', True)
            }

            # Add optional parameters if present
            if 'authMode' in ssid:
                params['authMode'] = ssid['authMode']
            if 'encryptionMode' in ssid:
                params['encryptionMode'] = ssid['encryptionMode']
            if 'psk' in ssid:
                params['psk'] = ssid['psk']
            if 'defaultVlanId' in ssid:
                params['defaultVlanId'] = ssid['defaultVlanId']
            if 'ipAssignmentMode' in ssid:
                params['ipAssignmentMode'] = ssid['ipAssignmentMode']

            dashboard.wireless.updateNetworkWirelessSsid(
                network_id,
                number,
                **params
            )
            print(f"  ✓ Restored SSID {number}: {ssid['name']}")
        except Exception as e:
            print(f"  ⚠ SSID {number}: {e}")


def restore_group_policies(network_id, policies_backup):
    """Restore group policies"""
    print("\n[4/5] Restoring group policies...")

    # Get current policies
    try:
        current_policies = dashboard.networks.getNetworkGroupPolicies(network_id)
        current_names = {p['name'] for p in current_policies}
    except:
        current_names = set()

    for policy in policies_backup:
        try:
            name = policy['name']

            # Skip if already exists (would need to update, not recreate)
            if name in current_names:
                print(f"  ⚠ Policy '{name}' already exists (skipping)")
                continue

            # Build parameters
            params = {'name': name}

            if 'scheduling' in policy:
                params['scheduling'] = policy['scheduling']
            if 'bandwidth' in policy:
                params['bandwidth'] = policy['bandwidth']
            if 'firewallAndTrafficShaping' in policy:
                params['firewallAndTrafficShaping'] = policy['firewallAndTrafficShaping']

            dashboard.networks.createNetworkGroupPolicy(network_id, **params)
            print(f"  ✓ Restored policy: {name}")
        except Exception as e:
            print(f"  ⚠ Policy '{name}': {e}")


def restore_switch_ports(switch_serial, ports_backup):
    """Restore switch port configuration"""
    print(f"\n[5/5] Restoring switch ports for {switch_serial}...")

    restored = 0
    for port in ports_backup:
        try:
            port_id = port['portId']

            # Build parameters
            params = {}
            if 'name' in port:
                params['name'] = port['name']
            if 'enabled' in port:
                params['enabled'] = port['enabled']
            if 'type' in port:
                params['type'] = port['type']
            if 'vlan' in port:
                params['vlan'] = port['vlan']
            if 'voiceVlan' in port:
                params['voiceVlan'] = port['voiceVlan']
            if 'poeEnabled' in port:
                params['poeEnabled'] = port['poeEnabled']

            dashboard.switch.updateDeviceSwitchPort(
                switch_serial,
                port_id,
                **params
            )
            restored += 1
        except Exception as e:
            print(f"  ⚠ Port {port_id}: {e}")

    print(f"  ✓ Restored {restored} port(s)")


def restore_from_backup(backup_file, network_id):
    """Restore network from backup"""
    print(f"\n{'=' * 70}")
    print("RESTORING FROM BACKUP")
    print(f"{'=' * 70}")

    # Load backup
    with open(backup_file) as f:
        backup = json.load(f)

    meta = backup['metadata']
    print(f"\nBackup Details:")
    print(f"  Network: {meta['network_name']}")
    print(f"  Date: {meta['timestamp']}")
    print(f"  Backup Version: {meta['backup_version']}")

    print(f"\n⚠️  WARNING: This will OVERWRITE current configuration!")
    print(f"⚠️  Make sure you have a current backup before proceeding!")

    confirm = input("\nType 'RESTORE' to continue, or anything else to cancel: ")

    if confirm != 'RESTORE':
        print("\n✗ Restore cancelled")
        return

    print(f"\n{'=' * 70}")
    print("STARTING RESTORE")
    print(f"{'=' * 70}")

    # Restore VLANs
    if 'appliance' in backup and 'vlans' in backup['appliance']:
        restore_vlans(network_id, backup['appliance']['vlans'])

    # Restore firewall rules
    if 'appliance' in backup and 'firewall_l3' in backup['appliance']:
        restore_firewall_rules(network_id, backup['appliance']['firewall_l3'])

    # Restore SSIDs
    if 'wireless' in backup and 'ssids' in backup['wireless']:
        restore_ssids(network_id, backup['wireless']['ssids'])

    # Restore group policies
    if 'group_policies' in backup:
        restore_group_policies(network_id, backup['group_policies'])

    # Restore switch ports
    if 'switch' in backup and 'devices' in backup['switch']:
        for switch in backup['switch']['devices']:
            restore_switch_ports(switch['serial'], switch['ports'])

    print(f"\n{'=' * 70}")
    print("RESTORE COMPLETE")
    print(f"{'=' * 70}")
    print("\n✓ Configuration restored from backup")
    print("✓ Verify all settings in Dashboard")
    print("✓ Test connectivity to ensure everything works")


def main():
    print("=" * 70)
    print("MERAKI CONFIGURATION RESTORE TOOL")
    print("=" * 70)
    print("\n⚠️  WARNING: This tool can overwrite your current configuration!")
    print("⚠️  Only use this for disaster recovery scenarios!")

    # List backups
    backups = list_backups()

    if not backups:
        print("\n✗ No backups found")
        return

    # Get user selection
    try:
        num = int(input("\nSelect backup to restore (#): "))

        if num < 1 or num > len(backups):
            print("Invalid selection")
            return

        backup_file = backups[num - 1]

        # Load backup to get network ID
        with open(backup_file) as f:
            backup = json.load(f)

        network_id = backup['metadata']['network_id']

        # Perform restore
        restore_from_backup(backup_file, network_id)

    except (ValueError, KeyboardInterrupt):
        print("\n✗ Cancelled")


if __name__ == "__main__":
    main()