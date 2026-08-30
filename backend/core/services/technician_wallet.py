from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from core.models import (
    TechnicianWallet, 
    TechnicianWalletTransaction, 
    TechnicianIncentiveAward,
    WithdrawalRequest
)

class TechnicianWalletService:
    @staticmethod
    def get_or_create_wallet(technician):
        wallet, created = TechnicianWallet.objects.get_or_create(technician=technician)
        return wallet

    @staticmethod
    def calculate_earnings(service_request):
        """
        Currently technician gets 100% of the amount.
        In the future, platform fee logic can be added here.
        """
        return service_request.amount

    @staticmethod
    @transaction.atomic
    def credit_job_earnings(technician, service_request):
        amount = TechnicianWalletService.calculate_earnings(service_request)
        if amount <= 0:
            return None

        # Lock the wallet row
        wallet = TechnicianWallet.objects.select_for_update().get(technician=technician)

        # Update balances
        wallet.available_balance += amount
        wallet.total_earnings += amount
        wallet.save()

        # Create Transaction
        trans = TechnicianWalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='JOB_EARNING',
            description=f"Earnings for Job #{service_request.id}",
            reference_id=str(service_request.id)
        )
        return trans

    @staticmethod
    @transaction.atomic
    def credit_incentive(technician, incentive, amount, qualifying_reference):
        """
        Credits an incentive to the wallet and creates the award record.
        Must be called within IncentiveEngine which checks for duplicates.
        """
        wallet = TechnicianWallet.objects.select_for_update().get(technician=technician)
        
        wallet.available_balance += amount
        wallet.total_incentive_earnings += amount
        wallet.save()

        trans = TechnicianWalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='INCENTIVE',
            description=f"Incentive Reward: {incentive.name}",
            reference_id=f"INC_{incentive.id}"
        )

        award = TechnicianIncentiveAward.objects.create(
            technician=technician,
            incentive=incentive,
            qualifying_reference=qualifying_reference,
            reward_amount=amount,
            transaction=trans
        )
        return award

    @staticmethod
    @transaction.atomic
    def request_withdrawal(technician, amount):
        amount = Decimal(amount)
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero.")

        wallet = TechnicianWallet.objects.select_for_update().get(technician=technician)

        if amount > wallet.available_balance:
            raise ValueError("Insufficient balance.")

        # Deduct to reserve funds
        wallet.available_balance -= amount
        wallet.save()

        # Create Transaction (represents the reserved funds)
        trans = TechnicianWalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='WITHDRAWAL',
            description="Withdrawal Request (Pending)"
        )

        # Create Request
        req = WithdrawalRequest.objects.create(
            technician=technician,
            amount=amount,
            status='PENDING',
            transaction=trans
        )
        
        # Update transaction reference
        trans.reference_id = f"WD_{req.id}"
        trans.save()
        
        return req

    @staticmethod
    @transaction.atomic
    def reject_withdrawal(withdrawal_request, admin_notes=""):
        if withdrawal_request.status != 'PENDING':
            raise ValueError("Only pending requests can be rejected.")

        technician = withdrawal_request.technician
        wallet = TechnicianWallet.objects.select_for_update().get(technician=technician)

        # Refund the balance
        amount = withdrawal_request.amount
        wallet.available_balance += amount
        wallet.save()

        # Create Reversal Transaction
        TechnicianWalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='REVERSAL',
            description=f"Withdrawal Rejected - Refund",
            reference_id=f"WD_{withdrawal_request.id}"
        )

        # Update Request Status
        withdrawal_request.status = 'REJECTED'
        withdrawal_request.admin_notes = admin_notes
        withdrawal_request.processed_at = timezone.now()
        withdrawal_request.save()

    @staticmethod
    @transaction.atomic
    def approve_withdrawal(withdrawal_request, admin_notes=""):
        if withdrawal_request.status != 'PENDING':
            raise ValueError("Only pending requests can be approved.")

        withdrawal_request.status = 'APPROVED'
        if admin_notes:
            withdrawal_request.admin_notes = admin_notes
        withdrawal_request.save()

    @staticmethod
    @transaction.atomic
    def complete_withdrawal(withdrawal_request, admin_notes=""):
        if withdrawal_request.status not in ['PENDING', 'APPROVED']:
            raise ValueError("Only pending or approved requests can be completed.")

        technician = withdrawal_request.technician
        wallet = TechnicianWallet.objects.select_for_update().get(technician=technician)

        # Money was already deducted on request. Just update lifetime stat.
        wallet.total_withdrawn += withdrawal_request.amount
        wallet.save()

        # Update transaction description
        if withdrawal_request.transaction:
            withdrawal_request.transaction.description = "Withdrawal Completed"
            withdrawal_request.transaction.save()

        withdrawal_request.status = 'COMPLETED'
        if admin_notes:
            withdrawal_request.admin_notes = admin_notes
        withdrawal_request.processed_at = timezone.now()
        withdrawal_request.save()
