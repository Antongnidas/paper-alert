# Paper Alert

Automatically monitor academic journals for new papers matching your keywords, and receive notifications via email or WeChat.

## Supported Journals

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
| NBER Working Papers | NBER | working_papers |

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

### Journal Selection
Select journals by group, category, name, or tags. Leave all lists empty to fetch from all sources.

```yaml
selection:
  groups:
    - top_finance   # JF, JFE, RFS, JFQA
    - top_om        # MNSC, OR, MSOM
```

Available groups: `top_finance`, `top_om`, `top_is`, `top_marketing`, `top_management`, `top_accounting`, `om_extended`, `econ_core`, `working_papers`

### Notifications

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
