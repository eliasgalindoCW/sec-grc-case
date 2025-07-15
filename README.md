# README.md

## Security GRC – Internal Case Study

### Overview
This project demonstrates a solution for automating the verification of GitHub pull request (PR) controls, submitting audit evidence to the Eramba GRC platform, and proposing a future integration path with LLMs via Model Context Protocol (MCP).

---

### 🛠️ Part 1 – Technical Control Verification
**Objective:** Ensure that all merged PRs are approved by someone other than the author.

- Uses GitHub REST API to fetch merged PRs.
- Validates whether at least one approver is different from the author.

**Command:**
```bash
python check_github_control.py
```

> Output: Lists PRs and whether they comply with the required approval policy.

---

### 🔄 Part 2 – Automated Evidence Update
**Objective:** Submit control evidence automatically to Eramba's REST API.

- Sends audit result with timestamp, control ID, and description.
- Uses token-based authentication.

**Command:**
```bash
python submit_eramba_evidence.py
```

> Output: API response from Eramba confirming submission.

---

### 🤖 Part 3 – LLM + MCP Integration (Future Thinking)
**Goal:** Show how MCP can enable LLMs to analyze context and reason over PR approval patterns.

- Provided a JSON structure compatible with Model Context Protocol.
- Includes author/approver relationships for multiple PRs.
- Enables risk pattern detection and recommendation generation via LLM.

**Example:** See `mcp_llm_example.json`

> Potential future behavior: the LLM analyzes cross-approval patterns, flags repeated behavior, and suggests rotation or dual-review policies.

---

### 🔐 Assumptions
- You have GitHub and Eramba API tokens available.
- The repo being analyzed is accessible by the token.
- Eramba accepts evidence via POST in JSON format.

---

### 📁 File Structure
```
.
├── check_github_control.py       # GitHub PR policy verification
├── submit_eramba_evidence.py     # Evidence submission to Eramba
├── mcp_llm_example.json          # MCP-compatible input sample
└── README.md                     # Project documentation
```

---

### 📌 Notes
- In production, improve error handling and logging.
- GitHub API requests should be paginated for full coverage.
- Rate-limiting and retry logic should be added if used at scale.
- Approvers' timestamps could enhance future LLM analysis.

---

### 👨‍💻 Author
Prepared by candidate for the internal Security Engineer position at CloudWalk.

Feel free to adapt and extend this implementation.
# sec-grc-case
