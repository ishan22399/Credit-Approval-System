"""
Management command to ingest customer and loan data from Excel files.
"""

import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Customer, Loan
from datetime import datetime
import os


class Command(BaseCommand):
    help = 'Ingest customer and loan data from Excel files'

    def handle(self, *args, **options):
        self.ingest_customers()
        self.ingest_loans()
        self.stdout.write(self.style.SUCCESS('Data ingestion completed successfully.'))

    def ingest_customers(self):
        """
        Ingest customer data from customer_data.xlsx
        """
        # Look for Excel file in project root (/app/)
        excel_path = os.path.join('/app', 'customer_data.xlsx')
        
        if not os.path.exists(excel_path):
            self.stdout.write(self.style.WARNING(f'Customer data file not found at {excel_path}'))
            return
        
        try:
            df = pd.read_excel(excel_path)
            
            # Map Excel columns to model fields
            column_mapping = {
                'Customer ID': 'customer_id',
                'First Name': 'first_name',
                'Last Name': 'last_name',
                'Phone Number': 'phone_number',
                'Age': 'age',
                'Monthly Salary': 'monthly_salary',
                'Approved Limit': 'approved_limit',
            }
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Also add current_debt if not present
            if 'current_debt' not in df.columns:
                df['current_debt'] = 0.0
            
            self.stdout.write(f"Mapped columns: {list(df.columns)}")
            
            skipped = 0
            created = 0
            skipped_reasons = {'null': 0, 'zero': 0, 'duplicate': 0}
            
            for idx, row in df.iterrows():
                # Skip if customer_id is missing, 0, or null
                customer_id = row.get('customer_id')
                
                # Debug: show first few rows
                if idx < 3:
                    self.stdout.write(f"Row {idx}: customer_id={customer_id} (type: {type(customer_id).__name__})")
                
                if pd.isna(customer_id):
                    skipped_reasons['null'] += 1
                    skipped += 1
                    continue
                
                # Handle string/float conversions
                try:
                    customer_id = int(float(customer_id))
                except (ValueError, TypeError):
                    skipped_reasons['null'] += 1
                    skipped += 1
                    continue
                
                if customer_id == 0 or customer_id == '':
                    skipped_reasons['zero'] += 1
                    skipped += 1
                    continue
                
                # Check if customer already exists
                if Customer.objects.filter(customer_id=customer_id).exists():
                    skipped_reasons['duplicate'] += 1
                    skipped += 1
                    continue
                
                try:
                    customer = Customer.objects.create(
                        customer_id=customer_id,
                        first_name=str(row.get('first_name', 'Unknown')).strip(),
                        last_name=str(row.get('last_name', '')).strip(),
                        phone_number=str(row.get('phone_number', '')).strip(),
                        age=int(row.get('age', 0)) if pd.notna(row.get('age')) else 0,
                        monthly_salary=float(row.get('monthly_salary', 0)) if pd.notna(row.get('monthly_salary')) else 0,
                        approved_limit=float(row.get('approved_limit', 0)) if pd.notna(row.get('approved_limit')) else 0,
                        current_debt=float(row.get('current_debt', 0)) if pd.notna(row.get('current_debt')) else 0,
                    )
                    created += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error creating customer {customer_id}: {str(e)}"))
                    skipped += 1
            
            self.stdout.write(self.style.SUCCESS(f'Created {created} customers, skipped {skipped} (null: {skipped_reasons["null"]}, zero: {skipped_reasons["zero"]}, duplicate: {skipped_reasons["duplicate"]})'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error ingesting customers: {str(e)}'))

    def ingest_loans(self):
        """
        Ingest loan data from loan_data.xlsx
        """
        # Look for Excel file in project root (/app/)
        excel_path = os.path.join('/app', 'loan_data.xlsx')
        
        if not os.path.exists(excel_path):
            self.stdout.write(self.style.WARNING(f'Loan data file not found at {excel_path}'))
            return
        
        try:
            df = pd.read_excel(excel_path)
            
            # Map Excel columns to model fields
            column_mapping = {
                'Customer ID': 'customer_id',
                'Loan ID': 'loan_id',
                'Loan Amount': 'loan_amount',
                'Tenure': 'tenure',
                'Interest Rate': 'interest_rate',
                'Monthly payment': 'monthly_repayment',
                'EMIs paid on Time': 'emis_paid_on_time',
                'Date of Approval': 'start_date',
                'End Date': 'end_date',
            }
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            self.stdout.write(f"Mapped loan columns: {list(df.columns)}")
            
            skipped = 0
            created = 0
            
            for _, row in df.iterrows():
                # Skip if loan_id is missing, 0, or null
                loan_id = row.get('loan_id')
                if pd.isna(loan_id) or loan_id == 0 or loan_id == '':
                    skipped += 1
                    continue
                
                loan_id = int(loan_id)
                
                # Skip if customer_id is missing, 0, or null
                customer_id = row.get('customer_id')
                if pd.isna(customer_id) or customer_id == 0 or customer_id == '':
                    skipped += 1
                    continue
                
                customer_id = int(customer_id)
                
                # Check if loan already exists
                if Loan.objects.filter(loan_id=loan_id).exists():
                    skipped += 1
                    continue
                
                # Get customer
                try:
                    customer = Customer.objects.get(customer_id=customer_id)
                except Customer.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Customer {customer_id} not found for loan {loan_id}"))
                    skipped += 1
                    continue
                
                # Parse dates
                start_date = row.get('start_date')
                end_date = row.get('end_date')
                
                if pd.notna(start_date):
                    if isinstance(start_date, str):
                        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    else:
                        start_date = start_date.date() if hasattr(start_date, 'date') else start_date
                else:
                    start_date = timezone.now().date()
                
                if pd.notna(end_date):
                    if isinstance(end_date, str):
                        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    else:
                        end_date = end_date.date() if hasattr(end_date, 'date') else end_date
                else:
                    end_date = None
                
                loan = Loan.objects.create(
                    loan_id=loan_id,
                    customer=customer,
                    loan_amount=float(row.get('loan_amount', 0)) if pd.notna(row.get('loan_amount')) else 0,
                    tenure=int(row.get('tenure', 0)) if pd.notna(row.get('tenure')) else 0,
                    interest_rate=float(row.get('interest_rate', 0)) if pd.notna(row.get('interest_rate')) else 0,
                    monthly_repayment=float(row.get('monthly_repayment', 0) or row.get('emi', 0)) if pd.notna(row.get('monthly_repayment') or row.get('emi')) else 0,
                    emis_paid_on_time=int(row.get('emis_paid_on_time', 0)) if pd.notna(row.get('emis_paid_on_time')) else 0,
                    start_date=start_date,
                    end_date=end_date,
                )
                created += 1
            
            self.stdout.write(self.style.SUCCESS(f'Created {created} loans, skipped {skipped} existing/invalid loans'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error ingesting loans: {str(e)}'))
