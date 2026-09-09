import datetime
from django.utils import timezone
from django.db.models import Sum, Count, F, Q, Avg
from .models import (
    ServiceRequest, TechnicianWalletTransaction, WithdrawalRequest,
    customer_signup, Technician_signup, ReferralLog, TechnicianIncentiveAward,
    SupportTicket, Offer, CustomerOffer, Service
)

def get_date_range(filter_type):
    now = timezone.now()
    if filter_type == 'today':
        return now.replace(hour=0, minute=0, second=0, microsecond=0), now
    elif filter_type == 'yesterday':
        start = (now - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end
    elif filter_type == 'last_7':
        return now - datetime.timedelta(days=7), now
    elif filter_type == 'last_30':
        return now - datetime.timedelta(days=30), now
    elif filter_type == 'this_month':
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), now
    elif filter_type == 'this_year':
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0), now
    return None, None

def get_comprehensive_analytics(date_filter='all_time'):
    start_date, end_date = get_date_range(date_filter)
    
    def apply_date(qs, date_field):
        if start_date and end_date:
            return qs.filter(**{f"{date_field}__range": (start_date, end_date)})
        return qs

    # 1. Sales & Bookings (Source: ServiceRequest)
    # Authoritative Sale: payment_status == 'paid'
    sales_qs = apply_date(ServiceRequest.objects.filter(payment_status='paid'), 'updated_at')
    total_sales = sales_qs.aggregate(Sum('amount'))['amount__sum'] or 0

    bookings_qs = apply_date(ServiceRequest.objects.all(), 'created_at')
    total_bookings = bookings_qs.count()
    completed_bookings = bookings_qs.filter(status='Completed').count()
    cancelled_bookings = bookings_qs.filter(status='Cancelled').count() # Ensure this state exists

    # 2. Technician Earnings (Source: TechnicianWalletTransaction JOB_EARNING)
    earnings_qs = apply_date(TechnicianWalletTransaction.objects.filter(transaction_type='JOB_EARNING'), 'created_at')
    tech_earnings = earnings_qs.aggregate(Sum('amount'))['amount__sum'] or 0

    # 3. Platform Income
    # Business logic: actual customer payments - actual technician earnings
    platform_income = total_sales - tech_earnings

    # 4. Offers & Discounts (Source: ServiceRequest applied_offer)
    discount_qs = sales_qs.filter(applied_offer__isnull=False).select_related('applied_offer')
    
    discounts_sum = 0
    # Evaluate manually to ensure accurate difference against base service price
    for req in discount_qs:
        service = Service.objects.filter(name__iexact=req.service_detail.service_category).first()
        if service and service.price > req.amount:
            discounts_sum += (service.price - req.amount)

    # 5. Referral Rewards (Source: ReferralLog)
    ref_qs = apply_date(ReferralLog.objects.all(), 'created_at')
    referral_rewards = ref_qs.aggregate(Sum('reward_amount'))['reward_amount__sum'] or 0

    # 6. Technician Incentives (Source: TechnicianIncentiveAward)
    inc_qs = apply_date(TechnicianIncentiveAward.objects.all(), 'awarded_at')
    incentive_payouts = inc_qs.aggregate(Sum('reward_amount'))['reward_amount__sum'] or 0

    # 7. Withdrawals (Source: WithdrawalRequest)
    withdraw_req_qs = apply_date(WithdrawalRequest.objects.all(), 'requested_at')
    total_withdrawals_requested = withdraw_req_qs.aggregate(Sum('amount'))['amount__sum'] or 0
    
    withdraw_appr_qs = apply_date(WithdrawalRequest.objects.filter(status='APPROVED'), 'processed_at')
    total_withdrawals_approved = withdraw_appr_qs.aggregate(Sum('amount'))['amount__sum'] or 0

    withdraw_rej_qs = apply_date(WithdrawalRequest.objects.filter(status='REJECTED'), 'processed_at')
    total_withdrawals_rejected = withdraw_rej_qs.aggregate(Sum('amount'))['amount__sum'] or 0

    pending_withdrawals = WithdrawalRequest.objects.filter(status='PENDING').aggregate(Sum('amount'))['amount__sum'] or 0

    # 8. Refunds / Reversals (Source: TechnicianWalletTransaction REVERSAL)
    rev_qs = apply_date(TechnicianWalletTransaction.objects.filter(transaction_type='REVERSAL'), 'created_at')
    total_reversals = rev_qs.aggregate(Sum('amount'))['amount__sum'] or 0

    # 9. Growth Metrics
    new_customers = apply_date(customer_signup.objects.all(), 'user__date_joined').count()
    new_technicians = apply_date(Technician_signup.objects.all(), 'user__date_joined').count()

    # 10. Service Performance (Top Services by Bookings)
    top_services = bookings_qs.values('service_detail__service_category').annotate(
        count=Count('id'),
        sales=Sum('amount', filter=Q(payment_status='paid'))
    ).order_by('-count')[:5]

    return {
        'date_filter': date_filter,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'tech_earnings': tech_earnings,
        'platform_income': platform_income,
        'discounts_sum': discounts_sum,
        'referral_rewards': referral_rewards,
        'incentive_payouts': incentive_payouts,
        'total_withdrawals_requested': total_withdrawals_requested,
        'total_withdrawals_approved': total_withdrawals_approved,
        'total_withdrawals_rejected': total_withdrawals_rejected,
        'pending_withdrawals': pending_withdrawals,
        'total_reversals': total_reversals,
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'new_customers': new_customers,
        'new_technicians': new_technicians,
        'top_services': list(top_services)
    }

