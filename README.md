<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows-blue?style=for-the-badge&logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/PowerShell-5.1+-5391FE?style=for-the-badge&logo=powershell&logoColor=white" alt="PowerShell">
  <img src="https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Impala-Hadoop-E25A1C?style=for-the-badge&logo=apache&logoColor=white" alt="Impala">
  <img src="https://img.shields.io/badge/Version-8.7-green?style=for-the-badge" alt="Version">
</p>

# 🚀 Hadoop Query Launcher

> **A powerful Windows-based GUI application for executing and managing SQL queries on a remote Impala/Hadoop cluster.**

This tool provides an intuitive interface for uploading SQL files, executing queries, creating tables, downloading results, and running batch monthly-partitioned jobs—all with automated email notifications and robust error handling.

---

## 📑 Table of Contents

<details>
<summary>Click to expand</summary>

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Workflows In-Depth](#-workflows-in-depth)
  - [Create Table Workflow](#1-create-table-workflow)
  - [Query & Download Workflow](#2-query--download-workflow)
  - [Download Existing Table](#3-download-existing-table-workflow)
  - [Monthly Partitioned Job](#4-monthly-partitioned-job-workflow)
- [GUI Reference](#-gui-reference)
- [Configuration Parameters](#-configuration-parameters)
- [Remote Python Scripts API](#-remote-python-scripts-api)
- [SQL Template Examples](#-sql-template-examples)
- [Email Notifications](#-email-notifications)
- [Error Handling & Recovery](#-error-handling--recovery)
- [Best Practices](#-best-practices)
- [Frequently Asked Questions](#-frequently-asked-questions)
- [Troubleshooting Guide](#-troubleshooting-guide)
- [File Structure](#-file-structure)
- [Security Considerations](#-security-considerations)
- [Glossary](#-glossary)
- [Version History](#-version-history)
- [Contributing](#-contributing)

</details>

---

## 🌟 Overview

The **Hadoop Query Launcher** streamlines the process of running SQL queries against a remote Impala cluster from a Windows workstation. Instead of manually SSH-ing into a server, uploading files, and typing complex commands, this tool provides:

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRADITIONAL WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│  1. Open terminal                                               │
│  2. SSH to remote server                                        │
│  3. Authenticate with kinit                                     │
│  4. Navigate to working directory                               │
│  5. Upload SQL file via SCP (separate terminal)                 │
│  6. Manually type impala-shell command with all parameters      │
│  7. Wait and monitor output                                     │
│  8. If error, retry with different queue manually               │
│  9. Export results to CSV manually                              │
│  10. Download results via SCP                                   │
│  11. Send status email manually                                 │
│                                                                 │
│  ⏱️ Time: 15-30 minutes of manual work                          │
│  ❌ Error-prone, tedious, requires expertise                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  HADOOP QUERY LAUNCHER                          │
├─────────────────────────────────────────────────────────────────┤
│  1. Double-click run_query_engine.bat                           │
│  2. Fill in form fields                                         │
│  3. Click "Launch" → Paste command → Done!                      │
│                                                                 │
│  ⏱️ Time: 2 minutes                                             │
│  ✅ Automated, reliable, user-friendly                          │
└─────────────────────────────────────────────────────────────────┘
```

### What This Tool Does For You

| Manual Step | Automated By Launcher |
|-------------|----------------------|
| Write DDL wrapper for SQL | ✅ Auto-generates DROP/CREATE statements |
| Upload SQL file | ✅ SCP transfer with compression |
| Launch SSH terminal | ✅ Opens and positions terminal window |
| Construct bash command | ✅ Copies ready-to-paste command to clipboard |
| Handle queue failures | ✅ Automatic retry across 5 resource pools |
| Send status notifications | ✅ Email at each stage (start, error, success) |
| Export to CSV | ✅ Optional automatic export with gzip |
| Download results | ✅ One-click download button |

---

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🖥️ Native Windows GUI
- Clean, intuitive Windows Forms interface
- Input validation with helpful error messages
- Real-time status logging
- Smart UI state management

### 📤 Automatic File Transfer
- SCP-based upload with compression
- Automatic temp file cleanup
- Session-based folder organization

### 🔄 Intelligent Retry System
- Cycles through 5 Impala resource pools
- Classifies errors as fatal vs. retriable
- 30-second cooldown between retry cycles
- Unlimited retries for transient errors

</td>
<td width="50%">

### 📧 Comprehensive Notifications
- Email on job start, progress, and completion
- Detailed error traces in failure emails
- Support for multiple recipients
- Customizable subject lines

### 📅 Monthly Batch Processing
- Date range queries processed month-by-month
- Automatic temp table creation and cleanup
- Final UNION ALL into consolidated table
- Execution plan sent before processing

### 📥 Result Management
- Compressed CSV export (gzip)
- Session folder organization
- One-click local download
- Automatic path tracking

</td>
</tr>
</table>

---

## 🏗️ Architecture

### System Overview

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                            YOUR WINDOWS MACHINE                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                          │  │
│  │   run_query_engine.bat ──► run_query.ps1 (PowerShell GUI Application)   │  │
│  │                                    │                                     │  │
│  │                    ┌───────────────┼───────────────┐                    │  │
│  │                    │               │               │                    │  │
│  │                    ▼               ▼               ▼                    │  │
│  │              ┌──────────┐   ┌──────────┐   ┌──────────┐                │  │
│  │              │ Validate │   │ Generate │   │  Upload  │                │  │
│  │              │  Inputs  │   │   DDL    │   │   SQL    │                │  │
│  │              └──────────┘   └──────────┘   └────┬─────┘                │  │
│  │                                                 │                       │  │
│  │                    ┌────────────────────────────┘                       │  │
│  │                    ▼                                                    │  │
│  │              ┌───────────────────────────────────────┐                 │  │
│  │              │   Copy Command to Clipboard           │                 │  │
│  │              │   Launch SSH Terminal (Port 2222)     │                 │  │
│  │              │   Position Window on Screen           │                 │  │
│  │              └───────────────────────────────────────┘                 │  │
│  │                                                                          │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ SSH + SCP (Port 2222)
                                        │ Encrypted Connection
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                           HADOOP EDGE NODE SERVER                               │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                          │  │
│  │   SHARED SCRIPTS: /ads_storage/hadoop_query_launcher/scr/               │  │
│  │   ┌────────────────────────────────────────────────────────────────┐    │  │
│  │   │  Query_Impala_Parametrized.py  │  Main table creation engine   │    │  │
│  │   │  download_to_csv.py            │  Direct CSV export utility    │    │  │
│  │   │  monthly_query_processor.py    │  Monthly batch orchestrator   │    │  │
│  │   └────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                          │  │
│  │   USER WORKSPACE: /ads_storage/<username>/                              │  │
│  │   ┌────────────────────────────────────────────────────────────────┐    │  │
│  │   │  uploaded_query.sql           │  Your uploaded SQL files       │    │  │
│  │   │  session_table_20231215/      │  Output session folders        │    │  │
│  │   │  ├── create_process.log       │  Execution logs                │    │  │
│  │   │  ├── tablename.csv.gz         │  Compressed results            │    │  │
│  │   │  └── run.pid                  │  Process ID for monitoring     │    │  │
│  │   └────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                          │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ impala-shell (SSL + Kerberos)
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                           IMPALA CLUSTER                                        │
│                                                                                 │
│   Coordinator: dw.prod.impala.mastercard.int:21000                             │
│                                                                                 │
│   Resource Pools (in failover order):                                          │
│   ┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐      │
│   │ adhoc_fast  │ acs_small   │ adhoc_small │ acs_large   │   adhoc     │      │
│   │ (fastest)   │             │             │             │ (fallback)  │      │
│   └─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘      │
│                                                                                 │
│   Data Storage: HDFS Parquet Tables                                            │
│   Location Pattern: /das/<schema_prefix>/enc/<user>/<table_name>               │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  User   │────►│   GUI   │────►│  Edge   │────►│ Impala  │────►│  HDFS   │
│ Input   │     │  App    │     │  Node   │     │ Cluster │     │ Storage │
└─────────┘     └────┬────┘     └────┬────┘     └────┬────┘     └─────────┘
                     │               │               │
                     │   Upload      │   Execute     │   Store
                     │   SQL File    │   Query       │   Results
                     │               │               │
                     ▼               ▼               ▼
               ┌─────────┐     ┌─────────┐     ┌─────────┐
               │  Email  │◄────│  Python │◄────│ Created │
               │ Server  │     │ Scripts │     │  Table  │
               └─────────┘     └────┬────┘     └─────────┘
                     │               │
                     │               │   Export
                     │               ▼   to CSV
               ┌─────────┐     ┌─────────┐
               │  User   │◄────│  .csv   │
               │ Inbox   │     │  .gz    │
               └─────────┘     └─────────┘
```

---

## 📋 Prerequisites

### Local Machine (Windows)

| Requirement | Version/Details | How to Verify |
|-------------|-----------------|---------------|
| **Windows** | 10 or 11 | `winver` |
| **PowerShell** | 5.1 or later | `$PSVersionTable.PSVersion` |
| **OpenSSH Client** | Built-in or installed | `ssh -V` |
| **Windows Terminal** | Recommended (optional) | Check Start Menu |
| **Network Access** | Port 2222 to remote host | `Test-NetConnection -Port 2222 -ComputerName <host>` |

### Remote Server

| Requirement | Path/Details | Verification Command |
|-------------|--------------|---------------------|
| **Python 3.10** | `/sys_apps_01/python/python310/bin/python3.10` | `python3.10 --version` |
| **impala-shell** | Available in PATH | `which impala-shell` |
| **Kerberos** | Configured and accessible | `klist` |
| **Write Access** | `/ads_storage/<username>/` | `touch /ads_storage/$USER/test && rm /ads_storage/$USER/test` |

### Network Requirements

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Your PC      │   SSH   │   Edge Node     │  Impala │   Cluster       │
│                │◄───────►│                 │◄───────►│                 │
│  Port: Any     │  :2222  │  Port: 2222     │ :21000  │  Port: 21000    │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                    │
                                    │ SMTP
                                    ▼
                           ┌─────────────────┐
                           │   Mail Server   │
                           │ mailhost.mclocal│
                           └─────────────────┘
```

---

## 📦 Installation

### Step 1: Clone or Download

```powershell
# Using Git
git clone https://your-repository-url/hadoop-query-launcher.git
cd hadoop-query-launcher

# Or download and extract ZIP
```

### Step 2: Deploy Remote Scripts (One-Time Setup)

> **Note**: This step only needs to be done once per environment, or when scripts are updated.

```bash
# Connect to the remote server
ssh -p 2222 <username>@<remote-host>

# Create the shared directory (if it doesn't exist)
mkdir -p /ads_storage/hadoop_query_launcher/scr

# Exit back to local machine
exit

# Upload the Python scripts
scp -P 2222 scr/*.py <username>@<remote-host>:/ads_storage/hadoop_query_launcher/scr/
```

### Step 3: Verify Installation

```powershell
# Test SSH connectivity
ssh -p 2222 <username>@<remote-host> "echo 'Connection successful!'"

# Test script accessibility
ssh -p 2222 <username>@<remote-host> "ls -la /ads_storage/hadoop_query_launcher/scr/"
```

### Step 4: Create Your User Directory

```bash
# On the remote server
ssh -p 2222 <username>@<remote-host>
mkdir -p /ads_storage/$USER
exit
```

---

## ⚡ Quick Start

### Your First Query in 5 Steps

```
Step 1                    Step 2                    Step 3
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ Double-click │          │  Fill in the │          │   Click      │
│    .bat      │    ──►   │   GUI form   │    ──►   │  "Launch"    │
│    file      │          │              │          │   button     │
└──────────────┘          └──────────────┘          └──────────────┘

Step 4                    Step 5
┌──────────────┐          ┌──────────────┐
│  In terminal │          │    Click     │
│  kinit, then │    ──►   │  "Download"  │
│  Ctrl+V      │          │   button     │
└──────────────┘          └──────────────┘
```

### Detailed Steps

1. **Launch the Application**
   ```
   Double-click: run_query_engine.bat
   ```

2. **Configure Your Job**
   - Enter your **Remote User** (e.g., `e123456`)
   - Verify the **Remote Host** is correct
   - Enter the **Schema** and **Table Name**
   - Add **Recipient Email(s)** for notifications
   - Select your **SQL Query File** using Browse

3. **Select Options**
   - ✅ **Auto-generate DROP/CREATE** - for creating new tables
   - ✅ **Download result** - to get CSV export

4. **Execute**
   - Click **"1. Launch & Prepare Download"**
   - When SSH terminal opens, run `kinit` to authenticate
   - Paste the command from clipboard (Ctrl+V)
   - Wait for completion (terminal closes automatically)

5. **Download Results**
   - Click **"2. Download Result"** to retrieve your data

---

## 📖 Workflows In-Depth

### 1. Create Table Workflow

**Use Case**: Execute a SELECT query and store results as a new Impala table.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CREATE TABLE WORKFLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Your   │───►│Launcher │───►│ Upload  │───►│Execute  │───►│ Table   │
│  SQL    │    │ Wraps   │    │   to    │    │   on    │    │ Created │
│ SELECT  │    │with DDL │    │ Server  │    │ Impala  │    │   ✓     │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘

Your input:                    Auto-generated wrapper:
┌──────────────────────┐       ┌──────────────────────────────────────────┐
│ SELECT               │       │ DROP TABLE IF EXISTS schema.tablename;   │
│   customer_id,       │  ──►  │                                          │
│   SUM(amount)        │       │ CREATE TABLE schema.tablename            │
│ FROM transactions    │       │ STORED AS PARQUET                        │
│ GROUP BY customer_id │       │ LOCATION '/das/sch/enc/user/tablename'   │
└──────────────────────┘       │ AS                                       │
                               │                                          │
                               │ SELECT                                   │
                               │   customer_id,                           │
                               │   SUM(amount)                            │
                               │ FROM transactions                        │
                               │ GROUP BY customer_id                     │
                               └──────────────────────────────────────────┘
```

**Required Fields**:
- ✅ Remote User & Host
- ✅ Schema & Table Name
- ✅ Email & Subject
- ✅ SQL File
- ✅ "Auto-generate DROP/CREATE" checked

**Optional**:
- ☐ "Download result" - exports created table to CSV

---

### 2. Query & Download Workflow

**Use Case**: Run a query and get results as CSV without creating a permanent table.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       QUERY & DOWNLOAD WORKFLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Your   │───►│ Upload  │───►│Execute  │───►│ Export  │───►│Download │
│  SQL    │    │   to    │    │   on    │    │  CSV    │    │  .csv   │
│ SELECT  │    │ Server  │    │ Impala  │    │ + gzip  │    │  .gz    │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘

No table is created - results go directly to CSV file.
```

**How to Enable**:
1. Select "Create or Query from SQL file" mode
2. ☐ **Uncheck** "Auto-generate DROP/CREATE"
3. ✅ **Check** "Download result to local folder"

**Result**: `query_result_YYYYMMDD_HHMMSS.csv.gz`

---

### 3. Download Existing Table Workflow

**Use Case**: Export an already-existing Impala table to CSV.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DOWNLOAD EXISTING TABLE WORKFLOW                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Table  │───►│Generate │───►│ Export  │───►│Download │
│  Name   │    │SELECT * │    │  CSV    │    │  .csv   │
│ Input   │    │ Query   │    │ + gzip  │    │  .gz    │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

**How to Enable**:
1. Select **"Download Existing Table"** radio button
2. Enter Schema and Table Name
3. Click "Prepare for Download"

---

### 4. Monthly Partitioned Job Workflow

**Use Case**: Process a query for each month in a date range, then consolidate.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MONTHLY PARTITIONED JOB WORKFLOW                          │
└─────────────────────────────────────────────────────────────────────────────┘

Input: Date Range 01/01/2023 - 03/31/2023

          Phase 1: Create Monthly Tables
          ─────────────────────────────────────────────────────
          │
          ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  January 2023   │    │ February 2023   │    │   March 2023    │
│ ─────────────── │    │ ─────────────── │    │ ─────────────── │
│ schema.table_   │    │ schema.table_   │    │ schema.table_   │
│ temp_202301     │    │ temp_202302     │    │ temp_202303     │
│                 │    │                 │    │                 │
│ date_inicio:    │    │ date_inicio:    │    │ date_inicio:    │
│ 2023-01-01      │    │ 2023-02-01      │    │ 2023-03-01      │
│ date_fim:       │    │ date_fim:       │    │ date_fim:       │
│ 2023-01-31      │    │ 2023-02-28      │    │ 2023-03-31      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
          Phase 2: UNION ALL   ▼
          ─────────────────────────────────────────────────────
                               │
                    ┌──────────────────────┐
                    │  schema.table_       │
                    │  fulljoin            │
                    │                      │
                    │  SELECT * FROM       │
                    │    temp_202301       │
                    │  UNION ALL           │
                    │  SELECT * FROM       │
                    │    temp_202302       │
                    │  UNION ALL           │
                    │  SELECT * FROM       │
                    │    temp_202303       │
                    └──────────────────────┘
                               │
          Phase 3: Cleanup     ▼
          ─────────────────────────────────────────────────────
                               │
            DROP temp_202301, temp_202302, temp_202303
                               │
                               ▼
                         ┌──────────┐
                         │   Done   │
                         │    ✓     │
                         └──────────┘
```

**SQL Template Requirements**:

Your SQL must include these placeholders:
- `{date_inicio}` - replaced with first day of month (YYYY-MM-DD)
- `{date_fim}` - replaced with last day of month (YYYY-MM-DD)

---

## 🖼️ GUI Reference

### Main Window Layout

```
┌────────────────────────────────────────────────────────────────┐
│  Impala Process Launcher v3.2                            [─][□][×]
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─ 1. Select Operation Mode ─────────────────────────────┐   │
│  │  ○ Create or Query from SQL file  ○ Download Existing  │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─ 2. Configure Parameters ──────────────────────────────┐   │
│  │  Remote User:        [eXXXXXX                        ] │   │
│  │  Remote Host:        [hde2stl020003.mastercard.int   ] │   │
│  │  Schema:             [your_schema                    ] │   │
│  │  Table Name:         [user_test_table                ] │   │
│  │  Recipient Email(s): [name.surname@mastercard.com    ] │   │
│  │  Email Subject:      [Data Process Result            ] │   │
│  │  SQL Query File:     [query.sql          ] [Browse...] │   │
│  │                                                         │   │
│  │  ☑ Auto-generate DROP/CREATE statement (Create Table)  │   │
│  │  ☑ Download result to local folder                     │   │
│  │                                                         │   │
│  │  ☐ Process as monthly-partitioned job                  │   │
│  │     Start Date: [01/01/2023]  End Date: [12/31/2023]   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─ 3. Execute and Monitor ───────────────────────────────┐   │
│  │  [1. Launch & Prepare] [2. Download] [Reset] [Open Log]│   │
│  │                                                         │   │
│  │  Status Log:                                            │   │
│  │  ┌───────────────────────────────────────────────────┐ │   │
│  │  │ 2023-12-15 10:30:45 [INFO] Log session started.   │ │   │
│  │  │ 2023-12-15 10:30:45 [INFO] --- Run Parameters --- │ │   │
│  │  │ 2023-12-15 10:30:46 [INFO] Step 1: Uploading SQL  │ │   │
│  │  │ 2023-12-15 10:30:48 [INFO] Step 2: Launching SSH  │ │   │
│  │  │                                                   │ │   │
│  │  └───────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Button States

| State | Launch Button | Download Button | Reset | Log |
|-------|--------------|-----------------|-------|-----|
| **Initial** | ✅ Enabled | ❌ Disabled | ❌ Disabled | ❌ Disabled |
| **Processing** | ❌ Disabled | ❌ Disabled | ✅ Enabled | ✅ Enabled |
| **Ready for Download** | ❌ Disabled | ✅ Enabled | ✅ Enabled | ✅ Enabled |

---

## ⚙️ Configuration Parameters

### GUI Input Fields

| Field | Description | Default | Validation |
|-------|-------------|---------|------------|
| **Remote User** | Your enterprise ID | `eXXXXXX` | Required, non-empty |
| **Remote Host** | Hadoop edge node hostname | `hde2stl020003.mastercard.int` | Required, non-empty |
| **Schema** | Target Impala schema | `your_schema` | Required for Create/Download modes |
| **Table Name** | Table name (without schema) | `user_test_table` | Required for Create/Download modes |
| **Recipient Email(s)** | Notification recipients | `name.surname@mastercard.com` | Required for Create mode; semicolon-separated |
| **Email Subject** | Subject line prefix | `Data Process Result` | Required for Create mode |
| **SQL Query File** | Local path to .sql file | `query.sql` | Must exist for Create/Query modes |
| **Start Date** | Monthly job start | `01/01/2023` | MM/DD/YYYY format |
| **End Date** | Monthly job end | `12/31/2023` | MM/DD/YYYY format |

### Internal/Hidden Settings

| Setting | Value | Location in Code |
|---------|-------|------------------|
| SSH Port | `2222` | `run_query.ps1:240` |
| Python Executable | `/sys_apps_01/python/python310/bin/python3.10` | `run_query.ps1:265` |
| Shared Script Path | `/ads_storage/hadoop_query_launcher/scr/` | `run_query.ps1:244` |
| User Directory Pattern | `/ads_storage/<user>/` | `run_query.ps1:244` |
| Impala Host | `dw.prod.impala.mastercard.int:21000` | Python scripts |
| SMTP Server | `mailhost.mclocal.int` | `Query_Impala_Parametrized.py:193` |

---

## 🐍 Remote Python Scripts API

### Query_Impala_Parametrized.py

**Purpose**: Main orchestration script for table creation with full observability.

```bash
python Query_Impala_Parametrized.py \
  --sql-file <filename>        # SQL file in user directory (required)
  --table-name <schema.table>  # Full table name (required)
  --to-email <email>           # Notification recipient (required)
  --subject <text>             # Email subject prefix (required)
  --user <eid>                 # Remote user ID (required)
  --session-folder <path>      # Output directory (required)
  --download                   # Optional: export to CSV after creation
```

**Features**:
- Multi-queue retry with priority order
- Error classification (15+ error types)
- Email notifications at every stage
- Optional CSV export with compression
- Session-based output organization

---

### download_to_csv.py

**Purpose**: Export Impala data directly to CSV with retry logic.

```bash
# Mode 1: Export entire table
python download_to_csv.py \
  --table-name <schema.table>  # Table to export
  --output-file <path.csv>     # Output file path

# Mode 2: Execute query from file
python download_to_csv.py \
  --query-file <filename.sql>  # SQL file to execute
  --output-file <path.csv>     # Output file path
```

**Features**:
- Memory limit set to 1000GB for large exports
- Comma-delimited output with headers
- Automatic queue failover
- Error classification and logging

---

### monthly_query_processor.py

**Purpose**: Orchestrate month-by-month query execution with consolidation.

```bash
python monthly_query_processor.py \
  --sql-file <template.sql>    # SQL template with placeholders (required)
  --schema <schema>            # Target schema (required)
  --table-name <base_name>     # Base table name (required)
  --start-date <MM/DD/YYYY>    # Start of date range (required)
  --end-date <MM/DD/YYYY>      # End of date range (required)
  --user <eid>                 # Remote user ID (required)
  --to-email <email>           # Notification recipient (required)
  --subject <text>             # Email subject prefix (required)
```

**Process Flow**:
1. Parse date range into individual months
2. For each month: create temp table with date-filtered data
3. UNION ALL temp tables into `<table_name>_fulljoin`
4. Drop all temp tables
5. Send completion notification

---

## 📝 SQL Template Examples

### Basic SELECT Query

```sql
-- query.sql
-- This will be wrapped with DROP/CREATE automatically

SELECT 
    customer_id,
    customer_name,
    SUM(transaction_amount) as total_spend,
    COUNT(*) as transaction_count
FROM 
    raw_data.transactions
WHERE 
    transaction_date >= '2023-01-01'
    AND transaction_date < '2024-01-01'
GROUP BY 
    customer_id, 
    customer_name
HAVING 
    SUM(transaction_amount) > 1000
```

### Monthly Template with Placeholders

```sql
-- monthly_template.sql
-- Use with "Process as monthly-partitioned job" option

SELECT 
    account_id,
    merchant_category,
    SUM(amount) as monthly_spend,
    COUNT(*) as transaction_count,
    '{date_inicio}' as period_start,
    '{date_fim}' as period_end
FROM 
    transactions.card_transactions
WHERE 
    transaction_date >= '{date_inicio}'
    AND transaction_date <= '{date_fim}'
    AND status = 'APPROVED'
GROUP BY 
    account_id,
    merchant_category
```

### Complex Analytical Query

```sql
-- analytics_query.sql
-- Creates a customer segmentation table

WITH customer_metrics AS (
    SELECT 
        cust.customer_id,
        cust.segment,
        cust.region,
        SUM(txn.amount) as total_spend,
        COUNT(DISTINCT txn.merchant_id) as unique_merchants,
        COUNT(*) as transaction_count,
        MAX(txn.transaction_date) as last_transaction
    FROM 
        customers.master cust
    LEFT JOIN 
        transactions.approved txn 
        ON cust.customer_id = txn.customer_id
    WHERE 
        txn.transaction_date >= DATE_SUB(CURRENT_DATE(), 365)
    GROUP BY 
        cust.customer_id, 
        cust.segment, 
        cust.region
),
ranked_customers AS (
    SELECT 
        *,
        NTILE(10) OVER (ORDER BY total_spend DESC) as spend_decile,
        NTILE(10) OVER (ORDER BY transaction_count DESC) as frequency_decile
    FROM 
        customer_metrics
)
SELECT 
    *,
    CASE 
        WHEN spend_decile <= 2 AND frequency_decile <= 2 THEN 'PLATINUM'
        WHEN spend_decile <= 4 AND frequency_decile <= 4 THEN 'GOLD'
        WHEN spend_decile <= 6 AND frequency_decile <= 6 THEN 'SILVER'
        ELSE 'BRONZE'
    END as customer_tier
FROM 
    ranked_customers
```

---

## 📧 Email Notifications

### Notification Types

| Stage | Subject Pattern | When Sent |
|-------|-----------------|-----------|
| **Start** | `{subject} - PROCESSO INICIADO` | Job begins execution |
| **Queue Retry** | `{subject} - (Attempt N) All Queues Full` | All 5 queues failed, waiting to retry |
| **Retriable Error** | `{subject} - RETRIABLE ERROR (TYPE)` | Transient error, trying next queue |
| **Fatal Error** | `{subject} - ERRO (TYPE)` | Unrecoverable error, job stopped |
| **Success** | `{subject} - PROCESSO FINALIZADO` | Table created successfully |
| **Export Start** | `{subject} - CSV EXPORT STARTED` | CSV export beginning |
| **Export Complete** | `{subject} - CSV EXPORT FINISHED` | Export successful |
| **Export Failed** | `{subject} - CSV EXPORT FAILED` | Export error |
| **Monthly Plan** | `{subject} - Job Started (Execution Plan)` | Monthly job with table list |
| **Monthly Done** | `{subject} - Job Finished` | All monthly processing complete |

### Email Content Examples

**Success Email**:
```
User: e123456
Process: Table Creation
Status: SUCCESS
Table Created: analytics.customer_segments
Succeeded on Queue: adhoc_fast

The SQL query was executed successfully.
```

**Error Email**:
```
User: e123456
Process: Table Creation
Status: FATAL ERROR
Table: analytics.customer_segments
Failed on Queue: adhoc_small
Error Type: SYNTAX_ERROR

A fatal error occurred, and the process will not be retried. 
Please review the details below.

------------------- ERROR TRACE -------------------
AnalysisException: Syntax error in line 15:
  SELCT customer_id
  ^
Expected: SELECT, INSERT, UPDATE, ...
---------------------------------------------------
```

---

## ⚠️ Error Handling & Recovery

### Error Classification Matrix

| Error Type | Category | Retry? | User Action |
|------------|----------|--------|-------------|
| `MEMORY_EXCEEDED` | Resource | ✅ Yes | Wait; retries on larger pool |
| `QUEUE_FULL` | Resource | ✅ Yes | Wait; retries alternate pool |
| `TIMEOUT` | Resource | ✅ Yes | Wait; retries with fresh connection |
| `CONNECTION_ERROR` | Network | ✅ Yes | Check VPN; will auto-retry |
| `BACKPRESSURE` | Resource | ✅ Yes | Cluster busy; auto-retry |
| `SYNTAX_ERROR` | SQL | ❌ No | Fix SQL and re-run |
| `TABLE_NOT_FOUND` | SQL | ❌ No | Check table/schema names |
| `DUPLICATE_COLUMN` | SQL | ❌ No | Alias duplicate columns |
| `AUTH_ERROR` | Auth | ❌ No | Run `kinit` and re-run |
| `GENERIC_ERROR` | Unknown | ❌ No | Review logs for details |

### Queue Failover Order

```
Attempt 1: adhoc_fast    (fastest, lowest memory)
    │
    ▼ (if failed)
Attempt 2: acs_small     (alternative workload pool)
    │
    ▼ (if failed)
Attempt 3: adhoc_small   (ad-hoc, medium resources)
    │
    ▼ (if failed)
Attempt 4: acs_large     (large workload pool)
    │
    ▼ (if failed)
Attempt 5: adhoc         (general purpose, fallback)
    │
    ▼ (if all failed)
Wait 30 seconds ──► Restart from Attempt 1
```

### Recovery Procedures

**For Transient Errors (auto-handled)**:
The system automatically retries. No action needed.

**For Fatal Errors**:
1. Check the error email for details
2. Review the error trace
3. Fix the issue (SQL, permissions, etc.)
4. Click "Reset" in the GUI
5. Re-run the job

**For Stuck Jobs**:
1. SSH to the remote server
2. Find the process: `ps aux | grep python`
3. Kill if needed: `kill <PID>`
4. Clean up temp files in `/ads_storage/<user>/`

---

## 💡 Best Practices

### SQL Query Tips

```
✅ DO                                    ❌ DON'T
─────────────────────────────────────   ─────────────────────────────────────
Use explicit column aliases             Use SELECT * in production
Alias all computed columns              Leave ambiguous column names
Filter early with WHERE clauses         Filter late with HAVING on large sets
Use LIMIT during development            Run unlimited queries while testing
Test with small date ranges first       Run year-long queries immediately
Use proper date formats (YYYY-MM-DD)    Use locale-specific date formats
```

### Performance Optimization

1. **Partition Pruning**: Always filter on partition columns first
   ```sql
   WHERE partition_date BETWEEN '2023-01-01' AND '2023-01-31'
   ```

2. **Column Pruning**: Select only needed columns
   ```sql
   SELECT col1, col2  -- Not SELECT *
   ```

3. **Memory Management**: For large results, use Monthly Job mode to process in chunks

4. **Queue Selection**: Start with `adhoc_fast`, it auto-escalates if needed

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Table Name | `snake_case`, descriptive | `customer_monthly_spend_2023` |
| SQL Files | `snake_case.sql` | `monthly_aggregation_query.sql` |
| Email Subject | Short, identifiable | `Q4 Customer Analysis` |

---

## ❓ Frequently Asked Questions

<details>
<summary><b>Q: How long does a typical job take?</b></summary>

It depends on:
- Query complexity: Simple aggregations: 1-5 minutes; Complex joins: 5-30 minutes
- Data volume: Millions of rows: minutes; Billions of rows: hours
- Cluster load: Peak times may require more queue retries

The terminal stays open until completion, so you can monitor progress.
</details>

<details>
<summary><b>Q: Can I run multiple jobs simultaneously?</b></summary>

Yes! Each job:
- Creates a unique session folder with timestamp
- Uses separate log files
- Tracks its own remote paths

Just launch multiple instances of the GUI.
</details>

<details>
<summary><b>Q: What happens if my computer goes to sleep?</b></summary>

The remote job continues running via `nohup`. However:
- The SSH terminal will disconnect
- You won't see real-time output
- Email notifications still work
- You can download results when you reconnect
</details>

<details>
<summary><b>Q: How do I cancel a running job?</b></summary>

1. Close the SSH terminal (kills local connection)
2. SSH to server: `ssh -p 2222 <user>@<host>`
3. Find the job: `ps aux | grep python | grep <table_name>`
4. Kill it: `kill <PID>`
</details>

<details>
<summary><b>Q: Why did I get "All Queues Full" but the job succeeded?</b></summary>

This is normal! It means:
1. All 5 queues were busy on the first cycle
2. The system waited 30 seconds
3. On retry, a queue became available
4. Job completed successfully

You receive both the warning email AND the success email.
</details>

<details>
<summary><b>Q: Can I modify the Python scripts?</b></summary>

The scripts in `/ads_storage/hadoop_query_launcher/scr/` are shared. To test changes:
1. Copy to your user directory
2. Modify the copy
3. Test with a manual command
4. Once verified, update the shared version
</details>

<details>
<summary><b>Q: How do I export to a different format (Parquet, ORC)?</b></summary>

The current scripts export to CSV only. For other formats:
1. Create the table (which stores as Parquet in HDFS)
2. Use Impala/Hive to convert: `INSERT OVERWRITE ... SELECT * FROM table`
3. Download from HDFS directly: `hdfs dfs -get /path/to/file`
</details>

<details>
<summary><b>Q: What's the maximum file size I can download?</b></summary>

There's no hard limit, but consider:
- Network bandwidth and stability
- Local disk space
- Compression ratio (gzip typically achieves 10:1)

For very large exports (>10GB compressed), consider:
- Splitting the query by date range
- Downloading on the server and transferring in parts
- Using HDFS directly
</details>

---

## 🔧 Troubleshooting Guide

### Issue: "SSH command failed"

**Symptoms**: Terminal doesn't open or closes immediately

**Diagnosis**:
```powershell
# Test basic connectivity
Test-NetConnection -ComputerName <host> -Port 2222

# Test SSH manually
ssh -p 2222 -v <user>@<host>
```

**Solutions**:
- ✅ Verify VPN is connected
- ✅ Check firewall settings
- ✅ Confirm host is correct (not a typo)
- ✅ Try `ping <host>` to check basic connectivity

---

### Issue: "Failed to upload SQL file"

**Symptoms**: Error in status log about SCP failure

**Diagnosis**:
```powershell
# Test SCP manually
scp -P 2222 <local_file> <user>@<host>:/ads_storage/<user>/
```

**Solutions**:
- ✅ Verify local file exists and is readable
- ✅ Check remote directory permissions
- ✅ Ensure no special characters in filename
- ✅ Try with absolute path to SQL file

---

### Issue: "kinit: Client not found in Kerberos database"

**Symptoms**: Error after running kinit in terminal

**Solutions**:
- ✅ Use correct principal: `kinit <user>@DOMAIN.COM`
- ✅ Check password hasn't expired
- ✅ Verify Kerberos realm is correct
- ✅ Contact IT if account locked

---

### Issue: "Table not found" in error email

**Symptoms**: Query fails with AnalysisException

**Diagnosis**:
```sql
-- In impala-shell, check if table exists
SHOW TABLES IN <schema> LIKE '<pattern>';
DESCRIBE <schema>.<table>;
```

**Solutions**:
- ✅ Verify exact schema and table name spelling
- ✅ Check if you have SELECT permission
- ✅ Confirm table wasn't dropped/renamed
- ✅ Try fully qualified name: `database.schema.table`

---

### Issue: "Memory limit exceeded" persists

**Symptoms**: All 5 queues fail with memory errors

**Solutions**:
- ✅ Simplify the query (fewer JOINs, aggregations)
- ✅ Add stricter WHERE filters to reduce data
- ✅ Use Monthly Job mode to process smaller chunks
- ✅ Create intermediate tables for complex transformations
- ✅ Contact cluster admin for memory limit increase

---

### Issue: Download button doesn't download anything

**Symptoms**: Click Download but no file appears

**Diagnosis**:
Check the status log for the remote path, then:
```bash
ssh -p 2222 <user>@<host>
ls -la /ads_storage/<user>/session_*/
```

**Solutions**:
- ✅ Ensure the SSH job completed (terminal closed cleanly)
- ✅ Check if file exists on remote server
- ✅ Verify you waited for gzip compression to finish
- ✅ Try manual download: `scp -P 2222 <user>@<host>:<path> .`

---

## 📁 File Structure

```
hadoop-query-launcher/
│
├── 📄 README.md                        # This documentation
├── 📄 run_query_engine.bat             # Entry point (double-click to start)
├── 📄 run_query.ps1                    # PowerShell GUI application
│
├── 📁 scr/                             # Remote Python scripts
│   ├── 📄 Query_Impala_Parametrized.py # Table creation orchestrator
│   ├── 📄 download_to_csv.py           # CSV export utility
│   └── 📄 monthly_query_processor.py   # Monthly batch processor
│
└── 📁 (generated at runtime)           
    ├── 📄 launcher_log_*.log           # Session log files
    ├── 📄 _temp_query_*.sql            # Temporary wrapped SQL
    ├── 📁 session_*_timestamp/         # Downloaded session folders
    └── 📄 *.csv.gz                      # Downloaded compressed CSVs
```

### Remote Directory Structure

```
/ads_storage/
│
├── 📁 hadoop_query_launcher/           # Shared installation
│   └── 📁 scr/
│       ├── 📄 Query_Impala_Parametrized.py
│       ├── 📄 download_to_csv.py
│       └── 📄 monthly_query_processor.py
│
└── 📁 <username>/                      # Per-user workspace
    ├── 📄 uploaded_query.sql           # Uploaded SQL files
    ├── 📄 download_job_*.log           # Job logs
    ├── 📄 download_job_*.pid           # Process IDs
    │
    └── 📁 session_table_timestamp/     # Session outputs
        ├── 📄 create_process.log       # Execution log
        ├── 📄 run.pid                  # Process ID
        └── 📄 tablename.csv.gz         # Compressed results
```

---

## 🔐 Security Considerations

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION LAYERS                         │
└─────────────────────────────────────────────────────────────────┘

Layer 1: Network
┌─────────────┐     ┌─────────────┐
│   VPN       │────►│   Firewall  │     Must be on corporate network
└─────────────┘     └─────────────┘

Layer 2: SSH
┌─────────────┐     ┌─────────────┐
│   SSH Key   │────►│   Password  │     SSH authentication to edge node
│   or Pass   │     │   Prompt    │
└─────────────┘     └─────────────┘

Layer 3: Kerberos
┌─────────────┐     ┌─────────────┐
│   kinit     │────►│   TGT       │     Kerberos ticket for Impala
│   Command   │     │   Obtained  │
└─────────────┘     └─────────────┘

Layer 4: Impala
┌─────────────┐     ┌─────────────┐
│   SSL       │────►│   Kerberos  │     Encrypted + authenticated
│   Enabled   │     │   Principal │
└─────────────┘     └─────────────┘
```

### Data Protection

| Aspect | Protection Mechanism |
|--------|---------------------|
| **Data in Transit** | SSH encryption (SCP), SSL (Impala) |
| **Data at Rest** | HDFS encryption zones |
| **Credentials** | Never stored; entered at runtime |
| **Access Control** | Kerberos principals, HDFS ACLs |
| **Audit Trail** | Email notifications, log files |

### User Isolation

- Each user has a dedicated directory: `/ads_storage/<username>/`
- Tables are created in user-specific HDFS locations
- Python scripts run with user's credentials
- No cross-user access to results

---

## 📚 Glossary

| Term | Definition |
|------|------------|
| **DDL** | Data Definition Language (DROP, CREATE, ALTER statements) |
| **Edge Node** | Gateway server providing access to Hadoop cluster |
| **HDFS** | Hadoop Distributed File System for storing table data |
| **Impala** | MPP SQL query engine for Hadoop |
| **Kerberos** | Network authentication protocol used by Impala |
| **kinit** | Command to obtain Kerberos ticket |
| **nohup** | Command to run process immune to hangups |
| **Parquet** | Columnar storage format for efficient analytics |
| **Resource Pool** | Impala queue managing concurrent query resources |
| **SCP** | Secure Copy Protocol for file transfer over SSH |
| **Session Folder** | Timestamped directory for job artifacts |
| **SSH** | Secure Shell for encrypted remote access |

---

## 📜 Version History

| Version | Date | Changes |
|---------|------|---------|
| **8.7** | 2024-12 | Fixed UI: Schema/Table/Email remain enabled for monthly jobs |
| **8.6** | 2024-12 | Refined UI state management |
| **8.5** | 2024-11 | Added terminal window positioning |
| **8.0** | 2024-10 | Introduced Monthly Partitioned Job workflow |
| **7.0** | 2024-09 | Added Query & Download workflow |
| **6.0** | 2024-08 | Enhanced error classification (15+ types) |
| **5.0** | 2024-07 | Multi-queue retry mechanism |
| **4.0** | 2024-06 | Initial GUI implementation |
| **3.0** | 2024-05 | Python script modularization |
| **2.0** | 2024-04 | Email notification system |
| **1.0** | 2024-03 | Initial command-line version |

---

## 🤝 Contributing

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/my-feature`
3. **Test** locally with the full workflow
4. **Document** changes in README if applicable
5. **Submit** a pull request with detailed description

### Code Style

- **PowerShell**: Follow PSScriptAnalyzer recommendations
- **Python**: Follow PEP 8, use type hints where applicable
- **Documentation**: Use clear examples, keep formatting consistent

### Testing Checklist

Before submitting changes, verify:
- [ ] GUI launches without errors
- [ ] All 4 workflows complete successfully
- [ ] Email notifications are sent correctly
- [ ] Error scenarios are handled gracefully
- [ ] Log files capture relevant information

---

## 📞 Support

| Channel | Contact |
|---------|---------|
| **Issues** | Open a GitHub issue |
| **Questions** | Analytics team Slack channel |
| **Urgent** | Email the development team |

---

<p align="center">
  <b>Hadoop Query Launcher</b> - Simplifying Big Data Access
  <br>
  <sub>Internal use only. Mastercard proprietary software.</sub>
</p>
