# ECHO-ADMIN CLI Documentation

A command‑line interface for administering the ECHO application.  
All commands talk to the ECHO admin API using the credentials configured in your environment.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation & Setup](#installation--setup)
3. [Global Options](#global-options)
4. [Command Reference](#command-reference)
   - [User Management](#user-management)
   - [Promo Code Management](#promo-code-management)
   - [Credit Manipulation](#credit-manipulation)
   - [Log Downloads](#log-downloads)
5. [Exit Codes](#exit-codes)

---

## Prerequisites

- Python **3.10+** (uses `X | Y` type hints and `typer` features).
- An ECHO admin account with a valid **Admin ID** and **Admin Key**.
- The ECHO backend API must be running and reachable at the URL defined in `urls.py` (`BASE_URL`).

---

## Installation & Setup

1. **Clone the repository** and enter the project directory.

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Linux / macOS
   .venv\Scripts\activate         # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** – create `.venv/vars.env` with:
   ```env
   ADMIN_ID=your_admin_id
   ADMIN_KEY=your_admin_key
   ```
   The CLI automatically loads this file on startup.

5. **Set the API base URL** – edit `urls.py` and set `BASE_URL` to your backend, e.g.:
   ```python
   BASE_URL = "http://localhost:5000/api/admin"
   ```

6. **Run the CLI**:
   ```bash
   python main.py --help
   ```
   If you package the tool as an entry point, the command is `echo-admin`.

---

## Global Options

| Option          | Short | Description                              |
| --------------- | ----- | ---------------------------------------- |
| `--version`     | `-v`  | Show the CLI version and exit.           |
| `--help`        |       | Show help for any command or subcommand. |

Example:
```bash
echo-admin --version
# echo-admin 0.1.0
```

---

## Command Reference

Commands are grouped into four sub‑applications: `user`, `promo`, `credits`, and `logs`.

---

### User Management

#### `user list`

Fetch and display every registered user. Optionally export the result to a CSV file.

```bash
echo-admin user list [FILENAME]
```

| Argument   | Required | Description                                      |
| ---------- | -------- | ------------------------------------------------ |
| `FILENAME` | No       | Path to save the users table as CSV (must end with `.csv`). |

**Examples:**
```bash
# Print users to stdout
echo-admin user list

# Print and export to users.csv
echo-admin user list users.csv
```

---

#### `user get`

Fetch details of a single user.

```bash
echo-admin user get USER_ID
```

| Argument  | Required | Description                |
| --------- | -------- | -------------------------- |
| `USER_ID` | Yes      | The unique ID of the user. |

**Example:**
```bash
echo-admin user get 42
```

---

#### `user patch`

Update one or more fields on an existing user. Only the options you provide are sent to the API.

```bash
echo-admin user patch USER_ID [OPTIONS]
```

| Option                | Description                                   |
| --------------------- | --------------------------------------------- |
| `--name TEXT`         | Full name.                                    |
| `--email TEXT`        | Email address.                                |
| `--site-url TEXT`     | Associated website URL.                       |
| `--total-credits INT` | Total credits assigned.                       |
| `--left-credits INT`  | Remaining credits.                            |
| `--last-plan TEXT`    | Previous subscription plan.                   |
| `--current-plan TEXT` | Current subscription plan.                    |
| `--renewal-date TEXT` | Renewal date in `YYYY-MM-DD` format.          |

**Example:**
```bash
echo-admin user patch 42 --email new@example.com --current-plan pro
```

---

#### `user delete`

Permanently delete a user and all related records (captions, headlines, barcode sheets, saved items, payments, orders, products).

```bash
echo-admin user delete USER_ID [--yes | -y]
```

| Option        | Description                                    |
| ------------- | ---------------------------------------------- |
| `--yes`, `-y` | Skip the interactive confirmation prompt.      |

**Example:**
```bash
# Interactive confirmation
echo-admin user delete 42

# Non-interactive (e.g. in scripts)
echo-admin user delete 42 --yes
```

---

### Promo Code Management

#### `promo list`

List all promo codes along with aggregate statistics.

```bash
echo-admin promo list
```

---

#### `promo get`

Fetch a single promo code's details.

```bash
echo-admin promo get PROMO_ID
```

| Argument   | Required | Description                     |
| ---------- | -------- | ------------------------------- |
| `PROMO_ID` | Yes      | The unique ID of the promo code. |

**Example:**
```bash
echo-admin promo get 7
```

---

#### `promo create`

Create a new promo code. Required fields must be supplied.

```bash
echo-admin promo create [OPTIONS]
```

| Option                  | Short | Required | Description                                           |
| ----------------------- | ----- | -------- | ----------------------------------------------------- |
| `--code TEXT`           | `-c`  | Yes      | Unique promo code string.                             |
| `--plans TEXT`          | `-p`  | Yes      | Comma‑separated list of plans (e.g. `pro,team`).      |
| `--limit INT`           | `-l`  | Yes      | Maximum number of users that can redeem.              |
| `--expiry TEXT`         | `-e`  | Yes      | Expiration date (`YYYY-MM-DD`).                       |
| `--sponsor TEXT`        | `-s`  | No       | Sponsor name.                                         |
| `--credits INT`         |       | No       | Credits granted to redeemers.                         |
| `--discount FLOAT`      |       | No       | Discount as a decimal (e.g. `0.25` = 25%).            |

**Example:**
```bash
echo-admin promo create \
  --code SUMMER25 \
  --plans pro,team \
  --limit 500 \
  --expiry 2026-01-01 \
  --sponsor "ACME Corp" \
  --credits 100 \
  --discount 0.25
```

---

#### `promo patch`

Update one or more fields on an existing promo code.

```bash
echo-admin promo patch PROMO_ID [OPTIONS]
```

| Option                    | Description                                   |
| ------------------------- | --------------------------------------------- |
| `--credits INT`           | New credits value.                            |
| `--available-plans TEXT`  | Comma‑separated list of applicable plans.     |
| `--limit INT`             | New redemption limit.                         |
| `--expiry TEXT`           | New expiration date (`YYYY-MM-DD`).           |

**Example:**
```bash
echo-admin promo patch 7 --limit 1000 --expiry 2026-06-01
```

---

#### `promo delete`

Delete a promo code.

```bash
echo-admin promo delete PROMO_ID [--yes | -y]
```

| Option        | Description                                    |
| ------------- | ---------------------------------------------- |
| `--yes`, `-y` | Skip the interactive confirmation prompt.      |

**Example:**
```bash
echo-admin promo delete 7 --yes
```

---

### Credit Manipulation

#### `credits manipulate`

Increase or decrease a user's total and remaining credits. The same amount is applied to both fields.

```bash
echo-admin credits manipulate --user-id USER_ID --amount INT
```

| Option                 | Short | Required | Description                                                   |
| ---------------------- | ----- | -------- | ------------------------------------------------------------- |
| `--user-id TEXT`       | `-u`  | Yes      | The unique ID of the user.                                    |
| `--amount INT`         | `-a`  | Yes      | Credits to add (positive) or remove (negative). Must be non‑zero. |

**Examples:**
```bash
# Add 500 credits
echo-admin credits manipulate -u 42 -a 500

# Deduct 100 credits
echo-admin credits manipulate -u 42 -a -100
```

---

### Log Downloads

#### `logs download`

Download a log file from the server.

```bash
echo-admin logs download LOG_TYPE [--output PATH]
```

| Argument   | Required | Description                                           |
| ---------- | -------- | ----------------------------------------------------- |
| `LOG_TYPE` | Yes      | The log file to fetch (e.g. `app`, `error`, `access`). |

| Option          | Short | Description                                                   |
| --------------- | ----- | ------------------------------------------------------------- |
| `--output PATH` | `-o`  | Destination path. Defaults to `./<LOG_TYPE>.log`.             |

**Examples:**
```bash
# Save as ./error.log
echo-admin logs download error

# Save to a specific directory
echo-admin logs download app -o /tmp/echo-app.log
```

---

## Exit Codes

| Code | Meaning                                                      |
| ---- | ------------------------------------------------------------ |
| `0`  | Command completed successfully.                              |
| `1`  | An error occurred (network failure, API error, user abort).  |

Scripts can rely on these codes to detect failures.

---

## Tips

- Use `--help` on any command for a quick reminder:  
  `echo-admin user patch --help`
- All destructive commands (`user delete`, `promo delete`) prompt for confirmation unless `--yes` is passed.
- The CLI reads credentials from `.venv/vars.env`; never commit this file to version control.

---

*Happy administering!*