# Credit Approval System - Backend API

## Problem Statement

Build a **Django REST API** for a credit approval system that:
- Manages 300+ customers and 750+ loans from Excel files
- Calculates credit scores based on loan history
- Approves/rejects loans based on eligibility rules
- Provides 5 REST APIs for customer and loan management

---

## Solution: 5 Core APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/register/` | POST | Register new customer (auto-generates customer_id, calculates approved_limit = 36 × salary) |
| `/api/check-eligibility/` | POST | Check loan approval + credit score |
| `/api/create-loan/` | POST | Create loan if approved (auto-generates loan_id) |
| `/api/view-loan/{loan_id}/` | GET | Get loan details with nested customer info |
| `/api/view-loans/{customer_id}/` | GET | Get all loans for a customer |

---

## Key Implementation Details

### 1. **Credit Scoring (4 Factors)**
- On-time repayment ratio: **30%**
- Number of loans taken: **20%**
- Recent loan activity (current year): **20%**
- Total loan volume vs salary: **30%**
- **New customers: Score = 51** (passes > 50 approval threshold)

### 2. **Eligibility Rules** (in order)
1. **REJECT** if `current_debt > approved_limit`
2. **REJECT** if `total_EMI > 50% of monthly_salary`
3. **APPROVE** if `credit_score > 50`
4. **If 30 < score ≤ 50**: Approve only if `interest_rate > 12%` (else adjust to 12%)
5. **If 10 < score ≤ 30**: Approve only if `interest_rate > 16%` (else adjust to 16%)
6. **REJECT** if `score ≤ 10`

### 3. **EMI Calculation**
Compound interest formula: **P × r × (1+r)^n / ((1+r)^n - 1)**

### 4. **Data Ingestion**
- **300 customers** imported from `customer_data.xlsx`
- **753 loans** imported from `loan_data.xlsx`
- Auto-increment for new registrations (max_id + 1)

---

## Database Schema

### **customers** table
```
customer_id (IntegerField, PK) - Auto-generated
first_name, last_name
phone_number (unique)
age, monthly_salary
approved_limit = 36 × monthly_salary (rounded to nearest 100,000)
current_debt (float, default=0)
```

### **loans** table
```
loan_id (IntegerField, PK) - Auto-generated
customer_id (FK)
loan_amount, tenure (months), interest_rate
monthly_repayment (calculated EMI)
emis_paid_on_time (count)
start_date, end_date
```

---

## Tech Stack

- **Framework**: Django 5.0 + Django REST Framework 3.15
- **Database**: PostgreSQL 14
- **Server**: Gunicorn (4 workers)
- **Cache**: Redis 7
- **Containerization**: Docker + Docker Compose

---

## Quick Start

```bash
docker-compose up --build
```

API will be available at: **http://localhost:8000**

The system automatically:
1. Creates PostgreSQL database
2. Runs migrations
3. Ingests Excel data (300 customers + 753 loans)
4. Starts Django server

---

## Files for Evaluation

| File | Purpose |
|------|---------|
| `core/models.py` | Customer & Loan models with IntegerField PKs |
| `core/views.py` | 5 API endpoints implementation |
| `core/utils.py` | Credit scoring, EMI, eligibility logic |
| `core/serializers.py` | Request/response validation |
| `core/management/commands/ingest_data.py` | Excel data import (300 customers, 753 loans) |
| `Dockerfile` | Container setup |
| `docker-compose.yml` | Multi-container orchestration |
| `requirements.txt` | Dependencies (Django 5.0, DRF 3.15, PostgreSQL, etc.) |
| `customer_data.xlsx` | 300 sample customers |
| `loan_data.xlsx` | 753 sample loans |

---

## Status

✅ **All 5 APIs implemented and working**  
✅ **Excel data ingestion complete (300 customers + 753 loans)**  
✅ **Credit scoring & eligibility rules working**  
✅ **Docker containerization ready**  
✅ **Database migrations applied**
  
