# job-app-agent

An automated job hunting assistant built by Eric Ferland. This script searches for relevant job postings online, filters by role and location, and uses GPT-4 to generate custom, no-fluff cover letters for each opportunity.

---

## 🔧 Features
- ✅ Scrapes jobs from Indeed based on keywords
- ✅ Filters for remote opportunities
- ✅ Auto-generates targeted GPT-4 cover letters
- ✅ Outputs results to console for review

---

## 🛠️ Requirements
- Python 3.8+
- `openai`
- `requests`
- `beautifulsoup4`

Install with:
```bash
pip install openai requests beautifulsoup4
```

---

## ⚙️ Configuration
Edit the top of `job_app_agent.py` to update:
- `OPENAI_API_KEY`: your OpenAI key
- `JOB_SEARCH_KEYWORDS`: the roles you're targeting
- `LOCATION_FILTER`: usually "remote"

---

## 🚀 Usage
```bash
python job_app_agent.py
```
The script will:
1. Pull job listings from Indeed
2. Print titles, companies, and job URLs
3. Output a GPT-4-generated cover letter tailored to each job

---

## 📌 Example Output
```text
Title: Systems Administrator
Company: ExampleTech
URL: https://www.indeed.com/viewjob?...  

Generated Cover Letter:
Dear Hiring Manager at ExampleTech,
...
```

---

## 🧠 Next Steps (Planned Enhancements)
- [ ] Save job data + letters to CSV/JSON
- [ ] Add resume tailoring
- [ ] Auto-fill job applications (where possible)
- [ ] Integrate Google Sheets logging

---

## 👨‍💻 Built by Eric Ferland
- GitHub: [@itferland](https://github.com/itferland)
- LinkedIn: [linkedin.com/in/eferland](https://www.linkedin.com/in/eferland)
