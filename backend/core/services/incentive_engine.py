import logging
from django.db.models import Count
from django.utils import timezone
from core.models import (
    Incentive,
    TechnicianIncentiveAward,
    ServiceRequest,
    TechnicianRating
)
from core.services.technician_wallet import TechnicianWalletService

logger = logging.getLogger(__name__)

class IncentiveEngine:
    @staticmethod
    def _is_incentive_valid(incentive):
        if not incentive.is_active:
            return False
        now = timezone.now()
        if incentive.start_date and now < incentive.start_date:
            return False
        if incentive.end_date and now > incentive.end_date:
            return False
        return True

    @staticmethod
    def evaluate_daily_jobs(technician):
        """
        Evaluates COMPLETED_JOBS_DAILY incentives for the current day.
        Uses the application's timezone for day boundaries.
        """
        incentives = Incentive.objects.filter(
            incentive_type='COMPLETED_JOBS_DAILY',
            is_active=True
        )
        if not incentives.exists():
            return

        now = timezone.localtime(timezone.now())
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        date_str = now.strftime('%Y-%m-%d')

        # Count qualifying completed jobs today
        completed_jobs_count = ServiceRequest.objects.filter(
            technician_username=technician.username,
            status='Completed',
            updated_at__gte=start_of_day,
            updated_at__lte=end_of_day
        ).count()

        for incentive in incentives:
            if not IncentiveEngine._is_incentive_valid(incentive):
                continue

            if completed_jobs_count >= incentive.threshold:
                qualifying_reference = f"daily_{date_str}"
                
                # Check if already awarded
                if TechnicianIncentiveAward.objects.filter(
                    technician=technician, 
                    incentive=incentive,
                    qualifying_reference=qualifying_reference
                ).exists():
                    continue

                try:
                    # Award it
                    TechnicianWalletService.credit_incentive(
                        technician=technician,
                        incentive=incentive,
                        amount=incentive.reward_amount,
                        qualifying_reference=qualifying_reference
                    )
                    logger.info(f"Awarded {incentive.name} to {technician.username} for {date_str}")
                except Exception as e:
                    logger.error(f"Error crediting daily incentive for {technician.username}: {e}")

    @staticmethod
    def evaluate_five_star_ratings(technician):
        """
        Evaluates FIVE_STAR_RATINGS incentive.
        Rewards every multiple of the threshold (e.g., every 5 ratings).
        """
        incentives = Incentive.objects.filter(
            incentive_type='FIVE_STAR_RATINGS',
            is_active=True
        )
        if not incentives.exists():
            return

        # Count total 5-star ratings for this technician
        five_star_count = TechnicianRating.objects.filter(
            technician=technician,
            rating=5
        ).count()

        for incentive in incentives:
            if not IncentiveEngine._is_incentive_valid(incentive):
                continue
                
            if five_star_count == 0 or incentive.threshold <= 0:
                continue

            # Calculate how many milestones the technician has hit
            milestones_hit = five_star_count // incentive.threshold

            if milestones_hit > 0:
                # To support repeatability, we check each milestone hit.
                # E.g. milestone 1, 2, 3.
                for milestone in range(1, milestones_hit + 1):
                    qualifying_reference = f"5_star_milestone_{milestone}"
                    
                    if TechnicianIncentiveAward.objects.filter(
                        technician=technician,
                        incentive=incentive,
                        qualifying_reference=qualifying_reference
                    ).exists():
                        continue # Already awarded this milestone
                        
                    if not incentive.is_repeatable and milestone > 1:
                        # If not repeatable, only award milestone 1
                        break
                        
                    try:
                        TechnicianWalletService.credit_incentive(
                            technician=technician,
                            incentive=incentive,
                            amount=incentive.reward_amount,
                            qualifying_reference=qualifying_reference
                        )
                        logger.info(f"Awarded {incentive.name} (Milestone {milestone}) to {technician.username}")
                    except Exception as e:
                        logger.error(f"Error crediting rating incentive for {technician.username}: {e}")

    @staticmethod
    def get_active_incentives_progress(technician):
        """
        Calculates and returns progress of active incentives for the technician UI.
        """
        active_incentives = Incentive.objects.filter(is_active=True)
        results = []
        
        now = timezone.localtime(timezone.now())
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        date_str = now.strftime('%Y-%m-%d')
        
        # Pre-fetch counts
        completed_jobs_count = ServiceRequest.objects.filter(
            technician_username=technician.username,
            status='Completed',
            updated_at__gte=start_of_day,
            updated_at__lte=end_of_day
        ).count()
        
        five_star_count = TechnicianRating.objects.filter(
            technician=technician,
            rating=5
        ).count()

        for incentive in active_incentives:
            if not IncentiveEngine._is_incentive_valid(incentive):
                continue
                
            progress_data = {
                'id': incentive.id,
                'name': incentive.name,
                'description': incentive.description,
                'type': incentive.incentive_type,
                'threshold': incentive.threshold,
                'reward_amount': incentive.reward_amount,
                'end_date': incentive.end_date,
            }

            if incentive.incentive_type == 'COMPLETED_JOBS_DAILY':
                qualifying_ref = f"daily_{date_str}"
                is_completed = TechnicianIncentiveAward.objects.filter(
                    technician=technician, incentive=incentive, qualifying_reference=qualifying_ref
                ).exists()
                
                if is_completed:
                    progress_data['current_progress'] = incentive.threshold
                    progress_data['remaining'] = 0
                    progress_data['percentage'] = 100
                    progress_data['completed'] = True
                else:
                    progress_data['current_progress'] = completed_jobs_count
                    progress_data['remaining'] = max(0, incentive.threshold - completed_jobs_count)
                    progress_data['percentage'] = int((completed_jobs_count / incentive.threshold) * 100) if incentive.threshold > 0 else 0
                    progress_data['completed'] = False
                    
            elif incentive.incentive_type == 'FIVE_STAR_RATINGS':
                milestones_hit = five_star_count // incentive.threshold if incentive.threshold > 0 else 0
                
                if not incentive.is_repeatable:
                    qualifying_ref = "5_star_milestone_1"
                    is_completed = TechnicianIncentiveAward.objects.filter(
                        technician=technician, incentive=incentive, qualifying_reference=qualifying_ref
                    ).exists()
                    
                    if is_completed:
                        progress_data['current_progress'] = incentive.threshold
                        progress_data['remaining'] = 0
                        progress_data['percentage'] = 100
                        progress_data['completed'] = True
                    else:
                        progress_data['current_progress'] = five_star_count
                        progress_data['remaining'] = max(0, incentive.threshold - five_star_count)
                        progress_data['percentage'] = int((five_star_count / incentive.threshold) * 100) if incentive.threshold > 0 else 0
                        progress_data['completed'] = False
                else:
                    # Repeatable
                    progress_in_current = five_star_count - (milestones_hit * incentive.threshold)
                    
                    progress_data['current_progress'] = progress_in_current
                    progress_data['remaining'] = incentive.threshold - progress_in_current
                    progress_data['percentage'] = int((progress_in_current / incentive.threshold) * 100) if incentive.threshold > 0 else 0
                    progress_data['completed'] = False
                    
            results.append(progress_data)
            
        return results
