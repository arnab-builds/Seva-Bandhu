from django.db.models import Count
from core.models import Service, ServiceRequest, SupportTicket

class ServiceRatingEngine:
    # Configurable Bayesian Smoothing Constants
    PRIOR_CONFIDENCE = 10.0      # Virtual completed bookings
    PRIOR_COMPLAINT_RATE = 0.02  # 2% virtual complaint rate
    PENALTY_MULTIPLIER = 10.0    # Maps complaint rate directly to rating scale

    @classmethod
    def get_all_service_ratings(cls):
        """
        Returns a dictionary mapping service_name to a dictionary of rating details.
        Optimized to use aggregation instead of N+1 queries.
        """
        # 1. Aggregate bookings per service (only completed)
        bookings_data = ServiceRequest.objects.filter(status='Completed')\
            .values('service_detail__service_category')\
            .annotate(completed_count=Count('id'))
            
        booking_counts = {
            item['service_detail__service_category']: item['completed_count'] 
            for item in bookings_data if item['service_detail__service_category']
        }
        
        # 2. Aggregate validated complaints per service
        # A validated complaint is one that is 'Resolved' and not explicitly 'Declined' or 'Rejected'.
        complaints_data = SupportTicket.objects.filter(
            ticket_type='Complaint',
            status='Resolved'
        ).exclude(
            action_taken__icontains='Rejected'
        ).exclude(
            action_taken__icontains='Declined'
        ).values('related_booking__service_detail__service_category')\
         .annotate(complaint_count=Count('id'))
         
        complaint_counts = {
            item['related_booking__service_detail__service_category']: item['complaint_count'] 
            for item in complaints_data if item['related_booking__service_detail__service_category']
        }
        
        ratings = {}
        for service in Service.objects.all():
            completed = booking_counts.get(service.name, 0)
            complaints = complaint_counts.get(service.name, 0)
            
            if completed == 0:
                ratings[service.name] = {
                    "rating": 0.0,
                    "booking_count": 0,
                    "validated_complaint_count": 0,
                    "complaint_rate": 0.0,
                    "complaint_rate_percent": 0.0,
                    "has_data": False
                }
                continue
                
            complaint_rate = complaints / completed
            
            # Bayesian Smoothing
            smoothed_rate = (complaints + (cls.PRIOR_CONFIDENCE * cls.PRIOR_COMPLAINT_RATE)) / (completed + cls.PRIOR_CONFIDENCE)
            
            penalty = smoothed_rate * cls.PENALTY_MULTIPLIER
            rating = 5.0 - penalty
            
            # Clamp between 1.0 and 5.0
            if rating < 1.0: rating = 1.0
            if rating > 5.0: rating = 5.0
            
            ratings[service.name] = {
                "rating": round(rating, 1),
                "booking_count": completed,
                "validated_complaint_count": complaints,
                "complaint_rate": round(complaint_rate, 4),
                "complaint_rate_percent": round(complaint_rate * 100, 2),
                "has_data": True
            }
            
        return ratings
