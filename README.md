# Paper Alert

Automatically monitor academic journals and conference proceedings for new papers matching your keywords, and receive notifications via email or WeChat.

## Supported Sources

### Journals

| Journal | Short | Group |
|---------|-------|-------|
| Journal of Finance | JF | top_finance |
| Journal of Financial Economics | JFE | top_finance |
| Review of Financial Studies | RFS | top_finance |
| Journal of Financial and Quantitative Analysis | JFQA | top_finance |
| Management Science | MNSC | top_om |
| Operations Research | OR | top_om |
| Manufacturing and Service Operations Management | MSOM | top_om |
| Information Systems Research | ISR | top_is |
| Marketing Science | MKSC | top_marketing |
| Organization Science | ORSC | top_management |
| Production and Operations Management | POM | om_extended |
| Journal of Operations Management | JOM | om_extended |
| Journal of Accounting and Economics | JAE | top_accounting |
| Journal of Accounting Research | JAR | top_accounting |
| Econometrica | ECTA | econ_core |
| American Economic Review | AER | econ_core |
| Quarterly Journal of Economics | QJE | econ_core |
| Journal of Political Economy | JPE | econ_core |
| Review of Economic Studies | REStud | econ_core |
| NBER Working Papers | NBER | working_papers |

### Conferences (most recent year)

| Conference | Group |
|------------|-------|
| WFA (Western Finance Association) | conferences |
| AFA (American Finance Association) | conferences |

Conference papers are fetched by downloading and parsing the official agenda PDF. See [Conference Papers](#conference-papers) below.

## Quickstart

```bash
git clone https://github.com/Antongnidas/paper-alert.git
cd paper-alert
pip install -r requirements.txt
cp config.example.yaml config.yaml
# edit config.yaml with your settings
python main.py
```

Results are saved to `outputs/papers.md` (and `.csv`, `.json`).

## Configuration

Open `config.yaml` and adjust the following sections:

### Keywords
```yaml
keywords:
  include:
    - healthcare
    - mutual fund
  exclude:
    - editorial
```
Papers must match **at least one** include keyword and **none** of the exclude keywords. Matching is whole-word and case-insensitive by default.

### Time Window
```yaml
lookback_days: 14   # fetch papers from the last 14 days
```

### Source Selection
Select sources by group, category, name, or tags. Leave all lists empty to fetch from all sources.

```yaml
selection:
  groups:
    - top_finance     # JF, JFE, RFS, JFQA
    - top_om          # MNSC, OR, MSOM
    - working_papers  # NBER
    - conferences     # WFA, AFA
```

Available groups:

| group | 包含期刊 |
|-------|----------|
| top_finance | JF, JFE, RFS, JFQA |
| top_om | MNSC, OR, MSOM |
| top_is | ISR |
| top_marketing | Marketing Science |
| top_management | Organization Science |
| top_accounting | JAE, JAR |
| om_extended | POM, JOM |
| econ_core | Econometrica, JPE, REStud *(AER/QJE 无公开 RSS，暂不支持)* |
| working_papers | NBER |
| conferences | WFA, AFA |

## Conference Papers

Conference papers are fetched from the official agenda PDF (WFA/AFA most recent year).

### Auto-discover agenda URL

```bash
python main.py --find-agenda wfa
python main.py --find-agenda afa
```

The program will scrape the official conference website, find the most recent agenda PDF, and ask if you want to update `sources.yaml` automatically.

> **Note:** WFA agenda is available year-round. AFA agenda PDF may not be publicly hosted — paste the URL manually into `sources.yaml` if auto-discovery fails.

### Enable a conference in sources.yaml

```yaml
- name: "WFA 2025"
  type: "conference"
  enabled: true          # set to true to include
  url: "https://..."     # filled automatically by --find-agenda, or paste manually
  download_pdf: false    # set to true to download matched papers as PDFs
  pdf_output_dir: "outputs/pdfs/WFA2025"
```

### Download matched papers as PDFs

Set `download_pdf: true` in `sources.yaml` for the conference. Matched papers will be saved to `pdf_output_dir` after each run.

## Notifications

**Email (Gmail):**
1. Enable 2-Step Verification on your Google account
2. Generate an App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Fill in `config.yaml`:
```yaml
notify:
  email:
    enabled: true
    smtp_host: smtp.gmail.com
    smtp_port: 465
    sender: "you@gmail.com"
    password: "YOUR_APP_PASSWORD"
    recipients:
      - "you@gmail.com"
```

**WeChat (via Server酱):**
1. Get a free SendKey at [sct.ftqq.com](https://sct.ftqq.com/)
2. Fill in `config.yaml`:
```yaml
notify:
  wechat:
    enabled: true
    sckey: "YOUR_SENDKEY"
```

## Requirements

- Python 3.8+
- Dependencies: `pip install -r requirements.txt`
