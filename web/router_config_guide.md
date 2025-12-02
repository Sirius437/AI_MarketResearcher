# Router Configuration Guide for MarketResearcher Remote Access

## 🌐 Router Port Forwarding Configuration

Based on your router's interface, here are the specific settings needed:

### **HTTPS Access (Primary - Required)**
```
Route Name: MarketResearch
IP Type: IPv4
Address IP of Destination: YOUR_LOCAL_IP
Top Net Mask IP: 255.255.255.255 (or /32)
Utilize IP Gateway Address: N
External Port: 443
Internal Port: 443
Protocol: TCP
```

### **HTTP Redirect (Optional - for automatic HTTPS redirect)**
```
Route Name: MarketResearcher-HTTP
IP Type: IPv4
Address IP of Destination: YOUR_LOCAL_IP
Top Net Mask IP: 255.255.255.255 (or /32)
Utilize IP Gateway Address: N
External Port: 80
Internal Port: 80
Protocol: TCP
```

## 📋 Step-by-Step Router Configuration

### 1. **Access Router Admin Panel**
- Open browser and go to: `YOUR_ROUTER_IP` (or your router's IP)
- Login with admin credentials

### 2. **Navigate to Port Forwarding**
Look for one of these menu items:
- "Port Forwarding"
- "Virtual Server"
- "NAT Forwarding"
- "Applications & Gaming"

### 3. **Add HTTPS Rule (Port 443)**
```
Service Name/Route Name: MarketResearcher-HTTPS
External Port Start: 443
External Port End: 443
Internal IP Address: YOUR_LOCAL_IP
Internal Port Start: 443
Internal Port End: 443
Protocol: TCP
IP Type: IPv4
Subnet Mask: 255.255.255.255
Use Gateway: No/Disabled
Status: Enabled
```

### 4. **Add HTTP Rule (Port 80) - Optional**
```
Service Name/Route Name: MarketResearcher-HTTP
External Port Start: 80
External Port End: 80
Internal IP Address: YOUR_LOCAL_IP
Internal Port Start: 80
Internal Port End: 80
Protocol: TCP
IP Type: IPv4
Subnet Mask: 255.255.255.255
Use Gateway: No/Disabled
Status: Enabled
```

## 🔍 Network Information You'll Need

### **Current Network Setup**
- **Local Server IP**: YOUR_LOCAL_IP
- **HTTPS Port**: 443
- **HTTP Port**: 80 (redirects to HTTPS)
- **Network Range**: YOUR_LOCAL_NETWORK/24

### **Find Your Public IP**
```bash
curl ifconfig.me
```

## 🧪 Testing Remote Access

### **After Router Configuration:**

1. **From External Network** (mobile data, different WiFi):
   ```
   https://YOUR_PUBLIC_IP
   ```

2. **Test Commands** (from external network):
   ```bash
   # Test HTTPS connectivity
   curl -k -I https://YOUR_PUBLIC_IP
   
   # Test HTTP redirect
   curl -I http://YOUR_PUBLIC_IP
   ```

### **Expected Results:**
- HTTPS should show MarketResearcher login page
- HTTP should redirect to HTTPS (301/302 response)

## 🔒 Security Considerations

### **Current Protection:**
✅ **Firewall**: UFW active with restrictive rules  
✅ **SSL/HTTPS**: Self-signed certificate  
✅ **Rate Limiting**: 5 login attempts/min  
✅ **fail2ban**: Brute force protection  
✅ **Security Headers**: XSS, CSRF protection  

### **Additional Security (Optional):**

1. **Change Default Ports** (if desired):
   ```
   External Port: 8443 → Internal Port: 443
   External Port: 8080 → Internal Port: 80
   ```

2. **IP Whitelist** (if you have static IPs):
   - Configure router to only allow specific external IPs

3. **VPN Access** (most secure):
   - Set up VPN server on router
   - Access MarketResearcher through VPN tunnel

## 🚨 Troubleshooting

### **Common Issues:**

1. **Connection Timeout**:
   - Check router port forwarding rules
   - Verify firewall allows ports 80/443
   - Ensure MarketResearcher services are running

2. **SSL Certificate Warnings**:
   - Expected with self-signed certificates
   - Click "Advanced" → "Proceed to site"

3. **Can't Access from External Network**:
   - Verify public IP is correct
   - Check ISP doesn't block ports 80/443
   - Test from mobile data network

### **Verification Commands:**
```bash
# Check if ports are open externally
nmap -p 80,443 YOUR_PUBLIC_IP

# Check local services
sudo netstat -tlnp | grep -E ":80|:443|:8000|:8501"

# Check nginx status
sudo systemctl status nginx
```

## 📞 Router Brand Specific Notes

### **Common Router Interfaces:**
- **TP-Link**: Advanced → NAT Forwarding → Virtual Servers
- **Netgear**: Dynamic DNS → Port Forwarding
- **Linksys**: Smart Wi-Fi Tools → Port Forwarding
- **ASUS**: Adaptive QoS → Traditional QoS → Port Forwarding
- **D-Link**: Advanced → Port Forwarding

### **Alternative Names for Port Forwarding:**
- Virtual Server
- NAT Forwarding
- Port Mapping
- Application Rules
- Gaming Rules
- Service Rules

## 🎯 Quick Setup Summary

**Minimum Required Configuration:**
```
Rule 1: External 443 → YOUR_LOCAL_IP:443 (TCP)
Rule 2: External 80 → YOUR_LOCAL_IP:80 (TCP) [Optional]
```

**Access URL After Setup:**
```
https://YOUR_PUBLIC_IP
```

**Security Status:**
- ✅ Encrypted HTTPS traffic
- ✅ Rate limited login attempts
- ✅ Firewall protection
- ✅ Intrusion detection (fail2ban)
