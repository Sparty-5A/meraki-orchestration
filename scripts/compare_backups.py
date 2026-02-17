#!/usr/bin/env python3
"""
Meraki Backup Comparison Tool
Compare two backup files to see what changed
"""

import json
from pathlib import Path
from datetime import datetime

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

            network_name = data["metadata"]["network_name"]
            timestamp = data["metadata"]["timestamp"]
            size = backup_file.stat().st_size / 1024

            dt = datetime.fromisoformat(timestamp)
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")

            print(f"{i:<4} {network_name:<30} {date_str:<20} {size:>6.1f} KB")
        except:
            print(f"{i:<4} {backup_file.name:<30} [Error]")

    return backups


def compare_vlans(backup1, backup2):
    """Compare VLANs between backups"""
    vlans1 = {v["id"]: v for v in backup1.get("appliance", {}).get("vlans", [])}
    vlans2 = {v["id"]: v for v in backup2.get("appliance", {}).get("vlans", [])}

    changes = []

    # Added VLANs
    added = set(vlans2.keys()) - set(vlans1.keys())
    for vlan_id in added:
        vlan = vlans2[vlan_id]
        changes.append(f"  + VLAN {vlan_id} added: {vlan['name']} ({vlan['subnet']})")

    # Removed VLANs
    removed = set(vlans1.keys()) - set(vlans2.keys())
    for vlan_id in removed:
        vlan = vlans1[vlan_id]
        changes.append(f"  - VLAN {vlan_id} removed: {vlan['name']}")

    # Modified VLANs
    common = set(vlans1.keys()) & set(vlans2.keys())
    for vlan_id in common:
        v1 = vlans1[vlan_id]
        v2 = vlans2[vlan_id]

        if v1["name"] != v2["name"]:
            changes.append(f"  Δ VLAN {vlan_id} renamed: '{v1['name']}' → '{v2['name']}'")
        if v1["subnet"] != v2["subnet"]:
            changes.append(f"  Δ VLAN {vlan_id} subnet changed: {v1['subnet']} → {v2['subnet']}")

    return changes


def compare_firewall_rules(backup1, backup2):
    """Compare firewall rules"""
    rules1 = backup1.get("appliance", {}).get("firewall_l3", {}).get("rules", [])
    rules2 = backup2.get("appliance", {}).get("firewall_l3", {}).get("rules", [])

    changes = []

    # Overall count change
    if len(rules1) != len(rules2):
        changes.append(f"  Δ Firewall rule count: {len(rules1)} → {len(rules2)}")

        # Don't compare individual rules if counts are different
        # (rules shifted positions after deletion/addition)
        return changes

    # If counts are same, check for modifications
    for i, (r1, r2) in enumerate(zip(rules1, rules2)):
        if r1.get("comment") != r2.get("comment"):
            old_comment = r1.get("comment", "[No comment]")
            new_comment = r2.get("comment", "[No comment]")
            changes.append(f"  Δ Rule {i + 1}: '{old_comment}' → '{new_comment}'")
        if r1.get("policy") != r2.get("policy"):
            changes.append(f"  Δ Rule {i + 1} policy: {r1.get('policy')} → {r2.get('policy')}")
        if r1.get("destCidr") != r2.get("destCidr"):
            changes.append(f"  Δ Rule {i + 1} destination changed")

    return changes


def compare_ssids(backup1, backup2):
    """Compare wireless SSIDs"""
    ssids1 = {s["number"]: s for s in backup1.get("wireless", {}).get("ssids", [])}
    ssids2 = {s["number"]: s for s in backup2.get("wireless", {}).get("ssids", [])}

    changes = []

    for num in sorted(set(ssids1.keys()) | set(ssids2.keys())):
        s1 = ssids1.get(num)
        s2 = ssids2.get(num)

        if not s1:
            changes.append(f"  + SSID {num} added: {s2['name']}")
        elif not s2:
            changes.append(f"  - SSID {num} removed: {s1['name']}")
        elif s1["name"] != s2["name"]:
            changes.append(f"  Δ SSID {num} renamed: '{s1['name']}' → '{s2['name']}'")
        elif s1.get("enabled") != s2.get("enabled"):
            status = "enabled" if s2.get("enabled") else "disabled"
            changes.append(f"  Δ SSID {num} ({s2['name']}): {status}")

    return changes


def compare_group_policies(backup1, backup2):
    """Compare group policies"""
    policies1 = {p["groupPolicyId"]: p for p in backup1.get("group_policies", [])}
    policies2 = {p["groupPolicyId"]: p for p in backup2.get("group_policies", [])}

    changes = []

    added = set(policies2.keys()) - set(policies1.keys())
    for pid in added:
        changes.append(f"  + Policy added: {policies2[pid]['name']}")

    removed = set(policies1.keys()) - set(policies2.keys())
    for pid in removed:
        changes.append(f"  - Policy removed: {policies1[pid]['name']}")

    return changes


def compare_switch_ports(backup1, backup2):
    """Compare switch port configurations"""
    changes = []

    switches1 = {s["serial"]: s for s in backup1.get("switch", {}).get("devices", [])}
    switches2 = {s["serial"]: s for s in backup2.get("switch", {}).get("devices", [])}

    for serial in set(switches1.keys()) & set(switches2.keys()):
        sw1_ports = {p["portId"]: p for p in switches1[serial]["ports"]}
        sw2_ports = {p["portId"]: p for p in switches2[serial]["ports"]}

        port_changes = 0
        for port_id in sw1_ports.keys():
            p1 = sw1_ports[port_id]
            p2 = sw2_ports.get(port_id)

            if p2 and (
                p1.get("name") != p2.get("name") or p1.get("type") != p2.get("type") or p1.get("vlan") != p2.get("vlan")
            ):
                port_changes += 1

        if port_changes > 0:
            changes.append(f"  Δ Switch {switches1[serial]['name']}: {port_changes} port(s) changed")

    return changes


def compare_backups(file1, file2):
    """Compare two backup files"""
    print(f"\n{'=' * 70}")
    print("BACKUP COMPARISON")
    print(f"{'=' * 70}")

    with open(file1) as f:
        backup1 = json.load(f)
    with open(file2) as f:
        backup2 = json.load(f)

    meta1 = backup1["metadata"]
    meta2 = backup2["metadata"]

    print(f"\nBackup 1: {meta1['network_name']}")
    print(f"  Date: {meta1['timestamp']}")
    print(f"\nBackup 2: {meta2['network_name']}")
    print(f"  Date: {meta2['timestamp']}")

    # Collect all changes
    all_changes = []

    # VLANs
    vlan_changes = compare_vlans(backup1, backup2)
    if vlan_changes:
        all_changes.append(("VLANs", vlan_changes))

    # Firewall rules
    fw_changes = compare_firewall_rules(backup1, backup2)
    if fw_changes:
        all_changes.append(("Firewall Rules", fw_changes))

    # SSIDs
    ssid_changes = compare_ssids(backup1, backup2)
    if ssid_changes:
        all_changes.append(("Wireless SSIDs", ssid_changes))

    # Group Policies
    policy_changes = compare_group_policies(backup1, backup2)
    if policy_changes:
        all_changes.append(("Group Policies", policy_changes))

    # Switch Ports
    switch_changes = compare_switch_ports(backup1, backup2)
    if switch_changes:
        all_changes.append(("Switch Configuration", switch_changes))

    # Display results
    if all_changes:
        print(f"\n{'=' * 70}")
        print("CHANGES DETECTED")
        print(f"{'=' * 70}")

        for category, changes in all_changes:
            print(f"\n{category}:")
            for change in changes:
                print(change)
    else:
        print(f"\n{'=' * 70}")
        print("✓ NO CHANGES DETECTED")
        print(f"{'=' * 70}")
        print("\nThe two backups are identical")


def main():
    print("=" * 70)
    print("MERAKI BACKUP COMPARISON TOOL")
    print("=" * 70)

    # List backups
    backups = list_backups()

    if len(backups) < 2:
        print("\n⚠ Need at least 2 backups to compare")
        print("Run backup_system.py to create more backups")
        return

    # Get user input
    print("\nSelect backups to compare:")
    try:
        num1 = int(input("First backup (#): "))
        num2 = int(input("Second backup (#): "))

        if num1 < 1 or num1 > len(backups) or num2 < 1 or num2 > len(backups):
            print("Invalid selection")
            return

        file1 = backups[num1 - 1]
        file2 = backups[num2 - 1]

        compare_backups(file1, file2)

    except (ValueError, KeyboardInterrupt):
        print("\nCancelled")


if __name__ == "__main__":
    main()
