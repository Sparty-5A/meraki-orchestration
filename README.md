# Meraki Network Orchestration & Automation

Complete network automation suite for Cisco Meraki platforms, featuring disaster recovery, multi-site configuration management, monitoring systems, and zero-trust security implementations.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Meraki SDK](https://img.shields.io/badge/Meraki%20SDK-1.x-orange.svg)](https://github.com/meraki/dashboard-api-python)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🎯 Overview

This repository contains production-grade automation tools for managing Cisco Meraki infrastructure at scale. Built with the Meraki Dashboard API, these scripts demonstrate enterprise network automation, disaster recovery, and operational excellence.

**Key Features:**
- 🔄 **Disaster Recovery**: Automated configuration backup/restore with intelligent filtering
- 🌐 **Multi-Site Management**: Configuration templates for deploying identical configs across sites
- 📊 **Network Monitoring**: Health checks, performance metrics, and alerting
- 🔐 **Security Automation**: Zero-trust segmentation, role-based access control
- 🔌 **Switch Automation**: Voice VLANs, PoE management, port configuration
- 📡 **Wireless Management**: SSID deployment, RF optimization

---

## 🏗️ Architecture
```
meraki_orchestration/
├── scripts/               # Automation scripts
│   ├── backup_system.py              # Full config backup
│   ├── restore_from_backup.py        # Disaster recovery
│   ├── compare_backups.py            # Change tracking
│   ├── network_monitor.py            # Health monitoring
│   ├── configure_switch.py           # Switch port automation
│   ├── group_policies.py             # Role-based access
│   └── [15+ total scripts]
├── backups/              # Timestamped configuration backups (JSON)
├── .env                  # API credentials (not committed)
└── README.md             # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Cisco Meraki Dashboard API key
- Network with Meraki MX/MS/MR/MV devices

### Installation
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/meraki-orchestration.git
cd meraki-orchestration

# Install dependencies
pip install meraki python-dotenv

# Configure API credentials
echo "MERAKI_API_KEY=your_api_key_here" > scripts/.env
```

### Usage
```bash
cd scripts

# Full network backup
python backup_system.py

# Network health monitoring
python network_monitor.py

# Compare configurations
python compare_backups.py

# Restore from backup (disaster recovery)
python restore_from_backup.py
```

---

## 📚 Feature Modules

### 1. Disaster Recovery System

**Files:** `backup_system.py`, `restore_from_backup.py`, `compare_backups.py`

Complete backup/restore solution for network configurations:

- **Automated Backups**: Exports all configurations (VLANs, firewall rules, SSIDs, switch ports, group policies) to timestamped JSON
- **Intelligent Filtering**: Handles Meraki's auto-generated rules during restore
- **Change Tracking**: Compares backups to identify configuration drift
- **Disaster Recovery**: One-command restoration of entire network configs

**Example:**
```bash
# Create backup
python backup_system.py

# Compare two backups
python compare_backups.py

# Restore from backup
python restore_from_backup.py
```

**Use Cases:**
- Pre-change backups
- Disaster recovery
- Configuration auditing
- Compliance documentation

---

### 2. Network Monitoring

**File:** `network_monitor.py`

Comprehensive network health monitoring with alerting:

- **Device Status**: Online/offline detection
- **Performance Metrics**: Latency, packet loss, bandwidth utilization
- **Client Tracking**: Connected devices by SSID/VLAN
- **SSID Health**: Wireless network availability
- **Switch Status**: Port utilization, PoE status
- **VLAN Verification**: Network segmentation validation

**Example:**
```bash
python network_monitor.py
```

**Production Deployment:**
```bash
# Add to crontab for automated monitoring
*/5 * * * * /path/to/network_monitor.py
```

---

### 3. Multi-Site Configuration Management

**Files:** `template_manager.py`, `apply_template_config.py`, `verify_branches.py`

Deploy identical configurations across multiple sites:

- **Configuration Templates**: Define once, deploy everywhere
- **Branch Automation**: Consistent VLAN, firewall, and wireless configs
- **Verification**: Automated compliance checking across sites

**Example:**
```bash
# Apply configuration to all branches
python apply_template_config.py

# Verify consistency
python verify_branches.py
```

**Use Cases:**
- Retail chain deployment
- Manufacturing sites
- Distributed offices

---

### 4. Security Automation

**Files:** `group_policies.py`, firewall configuration scripts

Role-based access control and zero-trust segmentation:

- **Group Policies**: Bandwidth limits, scheduled access, per-user firewall rules
- **Network Segmentation**: IoT isolation, guest restrictions
- **Zero-Trust Architecture**: Deny-by-default with explicit allows

**Example:**
```bash
# Deploy role-based policies
python group_policies.py
```

**Policies Implemented:**
- Executive: Full access, no limits
- Employee: 50 Mbps, business hours, content filtering
- Contractor: 5 Mbps, limited hours, internal network blocked
- Guest: 2 Mbps, internet only, no internal access

---

### 5. Switch Port Automation

**File:** `configure_switch.py`

Enterprise switch configuration automation:

- **Voice VLANs**: Separate VLANs for IP phones (QoS ready)
- **PoE Management**: Power over Ethernet for phones, cameras, APs
- **Port Profiles**: Workstation, IoT, guest, trunk configurations
- **Bulk Updates**: Configure 100+ ports in seconds

**Example:**
```bash
# Configure all switch ports
python configure_switch.py
```

**Port Types:**
- **Workstation Ports**: Data VLAN + Voice VLAN + PoE
- **IoT Ports**: Isolated VLAN, PoE enabled
- **Guest Ports**: Isolated with port security
- **Trunk Ports**: Uplinks to MX with all VLANs

---

## 🔐 Security Best Practices

### API Key Management

**Never commit API keys to Git!**
```bash
# Add to .gitignore
echo "scripts/.env" >> .gitignore
echo "*.key" >> .gitignore
echo "backups/" >> .gitignore
```

### Recommended Permissions

Create dedicated API key with minimal required permissions:
- Organization read access
- Network read/write access
- Switch read/write access (if managing switches)

### Production Considerations

- Use environment variables or secrets management (AWS Secrets Manager, HashiCorp Vault)
- Implement API rate limiting (built into SDK: `wait_on_rate_limit=True`)
- Enable audit logging
- Test in lab/sandbox before production

---

## 📊 Configuration Examples

### Network Topology Deployed
```
Branch Office Network
├── VLANs
│   ├── VLAN 10: Corporate (full access)
│   ├── VLAN 20: Guest (internet only)
│   ├── VLAN 30: IoT (isolated)
│   └── VLAN 40: Voice (QoS priority)
├── Firewall
│   ├── 10 security rules
│   └── Zero-trust segmentation
├── Wireless
│   ├── Corporate SSID (WPA2, VLAN 10)
│   ├── Guest SSID (Open, VLAN 20)
│   ├── IoT SSID (WPA2, VLAN 30)
│   └── Voice SSID (WPA2, VLAN 40)
└── Switch Configuration
    ├── Ports 1-10: Workstations (voice VLAN enabled)
    ├── Ports 11-15: IoT devices
    ├── Ports 16-20: Guest access
    └── Ports 21-22: Trunk to MX
```

### Sample Backup Output
```json
{
  "metadata": {
    "timestamp": "2026-02-16T12:39:29.603448",
    "network_name": "branch office",
    "backup_version": "1.0"
  },
  "appliance": {
    "vlans": [...],
    "firewall_l3": {...},
    "vpn_settings": {...}
  },
  "wireless": {
    "ssids": [...],
    "rf_profiles": [...]
  },
  "switch": {
    "devices": [...]
  }
}
```

---

## 🎓 Learning Resources

### Meraki Documentation
- [Dashboard API](https://developer.cisco.com/meraki/api-v1/)
- [Python SDK](https://github.com/meraki/dashboard-api-python)
- [API Best Practices](https://developer.cisco.com/meraki/api-v1/#!best-practices)

### Related Projects
- [Meraki API Examples](https://github.com/meraki/automation-scripts)
- [DevNet Sandbox](https://devnetsandbox.cisco.com/) - Free testing environment

### Skills Demonstrated
- **Network Automation**: Python, REST APIs, Infrastructure as Code
- **Enterprise Networking**: VLANs, routing, firewalls, wireless, switching
- **Security**: Zero-trust, network segmentation, role-based access
- **Operations**: Disaster recovery, monitoring, change management
- **DevOps**: Git, CI/CD-ready, documentation

---

## 🐛 Troubleshooting

### Common Issues

**API Rate Limiting:**
```python
# SDK handles this automatically
dashboard = meraki.DashboardAPI(API_KEY, wait_on_rate_limit=True)
```

**Sandbox Limitations:**
- Devices may show as offline (virtual devices)
- Some premium features unavailable (Umbrella, AMP)
- Traffic analytics may be disabled

**Template Binding Issues:**
- DevNet sandbox may not support template binding
- Workaround: Extract template config and apply manually (see `apply_template_config.py`)

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test in Meraki sandbox
4. Submit pull request with clear description

---

## 📝 License

MIT License - See LICENSE file for details

---

## 👤 Author

**Scott Penry**
- Network automation engineer with 10+ years in service provider networking
- Transitioning carrier-scale operations expertise to enterprise networking
- Specializing in Infrastructure as Code, SD-WAN, and cloud networking

**Connect:**
- GitHub: [@YOUR_GITHUB_USERNAME](https://github.com/YOUR_GITHUB_USERNAME)
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/YOUR_PROFILE)
- Portfolio: [Your Website](https://your-website.com)

---

## 🙏 Acknowledgments

- Cisco DevNet for sandbox access
- Meraki engineering team for excellent API documentation
- Network automation community for inspiration

---

## 📈 Project Stats

- **Scripts:** 15+ production-grade automation tools
- **Lines of Code:** ~3000+
- **Time Investment:** 12 hours hands-on development
- **Test Environment:** Cisco DevNet Meraki Sandbox
- **Target Use Case:** Enterprise networks with 10-500 sites

---

## 🎯 Roadmap

Future enhancements:
- [ ] Slack/email alerting integration
- [ ] Grafana dashboard templates
- [ ] Ansible playbooks
- [ ] Terraform provider integration
- [ ] CI/CD pipeline examples
- [ ] Multi-org support
- [ ] Webhook handlers for real-time alerts

---
