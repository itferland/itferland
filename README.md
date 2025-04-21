# 👋 Eric Ferland

I manage infrastructure like it matters — because it does. I’m a systems administrator with 15+ years of experience building secure, resilient environments across physical, virtual, and cloud platforms.

🛠️ **Focused on:**
- Hardening endpoints and networks (FortiGate, SentinelOne)
- Backup, restore, and disaster recovery (Veeam, Wasabi)
- Identity and access control (Okta, AD, Google Workspace)
- Automating repeatable tasks and audits with PowerShell & Python

🚧 **Currently Building:**  
**Job Application Agent** — A GPT-driven automation tool to scrape jobs, tailor resumes, and apply on your behalf.  
→ _Coming soon to this repo!_

---

## 🔁 Example Code Snippets (Redacted)

```powershell
# Manually start a Veeam backup job
Start-VBRJob -Job "colo-Wasabi-vai-archiveNew_acc"
```
```bash
# Restore Gmail messages using GYB
gyb.exe --email <REDACTED_USER_EMAIL> --action restore --local-folder "<REDACTED_PATH>" --use-admin <REDACTED_ADMIN> --service-account
```
```powershell
# FortiClient registry import batch
FortiClientVPNOnlineInstaller.exe
reg import VpnRegKey.reg
```
```python
# Scrape job listings and call GPT for auto cover letter
import openai, requests

def generate_cover_letter(description):

    return openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
```
