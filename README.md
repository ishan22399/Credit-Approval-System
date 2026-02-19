# Credit Approval System

## Problem

Build a **Django REST API backend system** for credit approval that:
- Manages 300+ customers and 750+ loan records from Excel files
- Calculates personalized credit scores based on loan history
- Approves/rejects loans based on eligibility rules
- Provides 5 core REST APIs for customer and loan management

## Solution

### Architecture
- **Django 5.0 + DRF** - RESTful API endpoints
- **PostgreSQL 14** - Production database
- **Redis 7** - Caching and async tasks
- **Docker Compose** - Containerized deployment
- **Gunicorn** - WSGI application server

### 5 APIs Implemented

1. **POST /api/register/** - Register new customer (auto-generates ID, calculates approved limit)
2. **POST /api/check-eligibility/** - Check loan approval with credit score
3. **POST /api/create-loan/** - Create loan if approved (auto-generates loan ID)
4. **GET /api/view-loan/{loan_id}/** - Get single loan with customer details
5. **GET /api/view-loans/{customer_id}/** - Get all loans for a customer

### Key Features

✅ **Auto-Increment IDs** - New registrations get auto-generated customer_id (max + 1)  
✅ **Credit Scoring** - 4-factor algorithm: on-time ratio (30%), loan count (20%), recent activity (20%), loan volume (30%)  
✅ **Eligibility Rules**:
   - Rule 1: Reject if current_debt > approved_limit
   - Rule 2: Reject if total EMI > 50% of monthly salary
   - Rule 3: Approve based on credit score bands with interest rate adjustments

✅ **Excel Data Import** - 300 customers + 753 loans from Excel files  
✅ **EMI Calculation** - Compound interest formula: P × r × (1+r)^n / ((1+r)^n - 1)  
✅ **Nested Responses** - View loan includes full customer details  
✅ **Django Admin** - Manage customers and loans with admin interface

## Quick Start (Docker)

```bash
docker-compose up --build
```

The system will:
1. Start PostgreSQL database
2. Run migrations
3. Ingest Excel data (customer_data.xlsx, loan_data.xlsx)
4. Start Django server on http://localhost:8000

## Test APIs

Manual test in PowerShell:
```powershell
# Register new customer
$body = @{first_name="John"; last_name="Doe"; phone_number="9876543210"; age=30; monthly_salary=50000} | ConvertTo-Json
$r = Invoke-RestMethod -Uri "http://localhost:8000/api/register/" -Method POST -ContentType "application/json" -Body $body
$r.customer_id  # See auto-generated ID

# Check eligibility
$body = @{customer_id=1; loan_amount=150000; interest_rate=10; tenure=12} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/check-eligibility/" -Method POST -ContentType "application/json" -Body $body
```

## Project Structure

```
├── core/                          # Django app
│   ├── models.py                  # Customer & Loan models
│   ├── views.py                   # 5 API endpoints
│   ├── serializers.py             # Request/response validation
│   ├── utils.py                   # Credit scoring, EMI, eligibility logic
│   ├── urls.py                    # URL routing
│   ├── management/commands/
│   │   └── ingest_data.py         # Excel data import script
│   └── admin.py                   # Django admin interface
├── credit_system/                 # Django settings
│   ├── settings.py                # Database, apps, middleware
│   ├── urls.py                    # Main URL routing
│   └── wsgi.py                    # WSGI config
├── Dockerfile                     # Container image
├── docker-compose.yml             # Multi-container orchestration
├── requirements.txt               # Python dependencies
├── manage.py                      # Django CLI
├── customer_data.xlsx             # 300 imported customers
└── loan_data.xlsx                 # 753 imported loans
```

## Database Schema

**customers** table:
- customer_id (INT, PK) - Auto-generated for new registrations
- first_name, last_name, phone_number (unique)
- age, monthly_salary
- approved_limit = 36 × monthly_salary (rounded to nearest 100,000)
- current_debt (tracks active loan amounts)

**loans** table:
- loan_id (INT, PK) - Auto-generated
- customer_id (FK)
- loan_amount, tenure (months), interest_rate
- monthly_repayment (EMI calculated)
- emis_paid_on_time (for credit score)
- start_date, end_date

## Credit Score Calculation

For new customers: **51** (passes eligibility threshold of > 50)

For existing customers:
```
Score = 30% × on_time_ratio + 20% × (loans_count / 5) 
        + 20% × (recent_loans / 3) + 30% × (total_volume / (2×annual_salary))
```

## Eligibility Decision Logic

```
IF current_debt > approved_limit
    REJECT
ELSE IF total_EMI > 50% × monthly_salary
    REJECT
ELSE IF credit_score > 50
    APPROVE
ELSE IF 30 < credit_score ≤ 50
    APPROVE IF interest_rate > 12% (else adjust to 12%)
ELSE IF 10 < credit_score ≤ 30
    APPROVE IF interest_rate > 16% (else adjust to 16%)
ELSE
    REJECT
```

## Deployment

The system is production-ready with:
- Multi-worker Gunicorn (4 workers)
- PostgreSQL persistent volumes
- Redis for caching
- Health checks for all services
- Environment variable configuration
- Proper error handling and validation

---

**Status**: ✅ Complete with all 5 APIs tested and working  
**Data**: ✅ 300 customers + 753 loans imported from Excel  
**Container**: ✅ Docker configuration with auto-deployment  
