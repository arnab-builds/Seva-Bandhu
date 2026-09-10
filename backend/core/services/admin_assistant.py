import re

from django.db.models import Avg, Count, Sum

from core.analytics_helper import get_comprehensive_analytics, get_date_range
from core.models import (
    Offer,
    ReferralLog,
    Service,
    ServiceRequest,
    SupportTicket,
    TechnicianRating,
    Technician_signup,
    TechnicianIncentiveAward,
    TechnicianSupportTicket,
    TechnicianWalletTransaction,
    WithdrawalRequest,
    WalletTransaction,
    customer_signup,
)


class AdminDataAssistant:
    """Local, database-backed assistant for super-admin questions."""

    def normalize(self, message):
        text = message.lower().replace("'s", " ")
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9@._ -]", " ", text)).strip()

    def date_filter(self, text):
        if "today" in text:
            return "today"
        if "yesterday" in text:
            return "yesterday"
        if "this month" in text or "current month" in text:
            return "this_month"
        if "last month" in text or "previous month" in text:
            return "last_month"
        if "this year" in text:
            return "this_year"
        if "last week" in text or "past week" in text or "7 days" in text:
            return "last_7"
        if "last 30" in text or "30 days" in text:
            return "last_30"
        return "all_time"

    def find_named(self, text):
        technicians = list(Technician_signup.objects.all())
        customers = list(customer_signup.objects.all())
        services = list(Service.objects.all())

        def matches(record):
            name = record.username.lower() if hasattr(record, "username") else record.name.lower()
            first_name = name.split()[0]
            return name in text or re.search(r"\b" + re.escape(first_name) + r"\b", text)

        named_technicians = [record for record in technicians if matches(record)]
        named_customers = [record for record in customers if matches(record)]
        named_services = [record for record in services if record.name.lower() in text]
        return named_technicians, named_customers, named_services

    def technician_details(self, technician, text, start, end):
        bookings = ServiceRequest.objects.filter(technician_username=technician.username)
        if start:
            bookings = bookings.filter(created_at__range=(start, end))
        earnings = TechnicianWalletTransaction.objects.filter(
            wallet__technician=technician,
            transaction_type="JOB_EARNING",
        )
        if start:
            earnings = earnings.filter(created_at__range=(start, end))
        total_earnings = earnings.aggregate(total=Sum("amount"))["total"] or 0
        rating = technician.ratings.aggregate(average=Avg("rating"), count=Count("id"))
        needs_detail = any(word in text for word in (
            "contact", "phone", "email", "profile", "details", "information",
            "experience", "location", "rating", "wallet", "status", "category",
            "available", "username",
        ))
        if any(word in text for word in ("income", "earning", "salary", "money")):
            return f"Technician {technician.username}'s job income is Rs {total_earnings}."
        if "booking" in text or "job" in text or "work" in text:
            completed = bookings.filter(status="Completed").count()
            return f"Technician {technician.username} has {bookings.count()} bookings, including {completed} completed."
        if needs_detail or not text:
            wallet = getattr(technician, "wallet", None)
            return (
                f"Technician: {technician.username}\n"
                f"Email: {technician.email}\n"
                f"Contact: {technician.contact}\n"
                f"Category: {technician.service_category or 'Not set'}\n"
                f"Experience: {technician.years_of_experience or 'Not provided'} years\n"
                f"Working locations: {technician.working_locations or 'Not provided'}\n"
                f"Availability: {'Available' if technician.is_available else 'Unavailable'}\n"
                f"Profile completed: {'Yes' if technician.profile_completed else 'No'}\n"
                f"Rating: {round(rating['average'], 1) if rating['average'] else 0} stars ({rating['count']} ratings)\n"
                f"Wallet balance: Rs {wallet.available_balance if wallet else 0}\n"
                f"Total job income: Rs {total_earnings}"
            )
        return None

    def customer_details(self, customer, text, start, end):
        bookings = ServiceRequest.objects.filter(customer_username=customer.username)
        if start:
            bookings = bookings.filter(created_at__range=(start, end))
        if "booking" in text or "order" in text:
            return f"Customer {customer.username} has {bookings.count()} bookings."
        return (
            f"Customer: {customer.username}\n"
            f"Email: {customer.email}\n"
            f"Contact: {customer.contact}\n"
            f"Wallet balance: Rs {customer.wallet_balance}\n"
            f"Email verified: {'Yes' if customer.email_verified else 'No'}\n"
            f"Phone verified: {'Yes' if customer.phone_verified else 'No'}\n"
            f"Bookings: {bookings.count()}\n"
            f"Referral code: {customer.referral_code or 'Not set'}"
        )

    def platform_overview(self):
        analytics = get_comprehensive_analytics("all_time")
        average = TechnicianRating.objects.aggregate(value=Avg("rating"))["value"]
        return (
            "Seva Bandhu platform overview:\n"
            f"Technicians: {Technician_signup.objects.count()}\n"
            f"Customers: {customer_signup.objects.count()}\n"
            f"Services: {Service.objects.count()}\n"
            f"Bookings: {ServiceRequest.objects.count()} ({analytics['completed_bookings']} completed)\n"
            f"Paid sales: Rs {analytics['total_sales']}\n"
            f"Technician earnings: Rs {analytics['tech_earnings']}\n"
            f"Platform income: Rs {analytics['platform_income']}\n"
            f"Offers: {Offer.objects.count()}\n"
            f"Customer complaints: {SupportTicket.objects.count()}\n"
            f"Technician tickets: {TechnicianSupportTicket.objects.count()}\n"
            f"Ratings: {TechnicianRating.objects.count()} (average {round(average, 1) if average else 0} stars)\n"
            f"Withdrawals: {WithdrawalRequest.objects.count()}\n"
            f"Referrals: {ReferralLog.objects.count()}\n"
            f"Incentive awards: {TechnicianIncentiveAward.objects.count()}"
        )

    def service_category(self, text):
        aliases = {
            "ac": "AC Repair",
            "air conditioning": "AC Repair",
            "electrical": "Electrical",
            "electric": "Electrical",
            "plumbing": "Plumbing",
            "plumber": "Plumbing",
            "cleaning": "Cleaning",
            "cleaner": "Cleaning",
        }
        return next((category for alias, category in aliases.items() if alias in text), None)

    def answer(self, message):
        text = self.normalize(message)
        if any(word in text for word in ("weather", "president", "joke", "news")):
            return "I can answer questions about Seva Bandhu admin data only."

        if any(phrase in text for phrase in (
            "platform overview", "platform summary", "business summary", "business overview",
            "dashboard summary", "about the platform", "all information", "everything",
        )):
            return self.platform_overview()

        date_name = self.date_filter(text)
        start, end = get_date_range(date_name)
        technicians, customers, services = self.find_named(text)

        category = self.service_category(text)
        asks_for_names = any(word in text for word in ("name", "names", "list", "show", "who", "available"))
        asks_for_technician = "technician" in text or "technicians" in text or "tech" in text

        if asks_for_technician and category and not technicians:
            query = Technician_signup.objects.filter(service_category__iexact=category)
            if "available" in text:
                query = query.filter(is_available=True)
            names = list(query.order_by("username").values_list("username", flat=True))
            if not names:
                return f"No technicians are registered for {category}."
            return f"Technicians for {category}:\n- " + "\n- ".join(names)

        if asks_for_technician and asks_for_names and not technicians:
            names = list(Technician_signup.objects.order_by("username").values_list("username", flat=True))
            if not names:
                return "No technicians are registered."
            return "Technicians:\n- " + "\n- ".join(names)

        if asks_for_technician and any(word in text for word in ("top", "best", "most", "highest")):
            rows = ServiceRequest.objects.filter(status="Completed").exclude(
                technician_username__isnull=True
            ).exclude(technician_username="")
            if start:
                rows = rows.filter(updated_at__range=(start, end))
            top = rows.values("technician_username").annotate(total=Count("id")).order_by("-total").first()
            if top:
                return f"Top technician is {top['technician_username']} with {top['total']} completed jobs."
            return "No completed technician jobs were found for this period."

        if len(technicians) == 1:
            result = self.technician_details(technicians[0], text, start, end)
            if result:
                return result
        if len(customers) == 1 and not technicians:
            return self.customer_details(customers[0], text, start, end)
        if len(services) == 1 and any(word in text for word in ("price", "cost", "status", "booking", "details")):
            service = services[0]
            count = ServiceRequest.objects.filter(service_detail__service_category__iexact=service.name).count()
            return f"Service: {service.name}\nPrice: Rs {service.price}\nStatus: {'Enabled' if service.is_enabled else 'Disabled'}\nBookings: {count}"

        analytics = get_comprehensive_analytics(date_name)
        if any(word in text for word in ("income", "revenue", "sales", "profit", "turnover", "money made")):
            return (
                f"Financial summary ({date_name}):\n"
                f"Paid sales: Rs {analytics['total_sales']}\n"
                f"Technician earnings: Rs {analytics['tech_earnings']}\n"
                f"Platform income: Rs {analytics['platform_income']}\n"
                f"Discounts: Rs {analytics['discounts_sum']}\n"
                f"Approved withdrawals: Rs {analytics['total_withdrawals_approved']}"
            )
        if any(phrase in text for phrase in ("how many users", "registered users", "user count", "customers joined")):
            return f"There are {customer_signup.objects.count()} registered customers."
        if "rating" in text or "stars" in text:
            average = TechnicianRating.objects.aggregate(value=Avg("rating"))["value"]
            return f"There are {TechnicianRating.objects.count()} ratings with an average of {round(average, 1) if average else 0} stars."
        if "withdrawal" in text:
            total = WithdrawalRequest.objects.aggregate(value=Sum("amount"))["value"] or 0
            return f"There are {WithdrawalRequest.objects.count()} withdrawal requests totaling Rs {total}."
        if "referral" in text:
            total = ReferralLog.objects.aggregate(value=Sum("reward_amount"))["value"] or 0
            return f"There are {ReferralLog.objects.count()} referrals totaling Rs {total} in rewards."
        if "booking" in text or "request" in text:
            query = ServiceRequest.objects.all()
            if "completed" in text:
                query = query.filter(status="Completed")
            return f"There are {query.count()} bookings matching that question."
        if "technician" in text:
            return f"There are {Technician_signup.objects.count()} technicians."
        if "customer" in text or "user" in text:
            return f"There are {customer_signup.objects.count()} customers."
        if "service" in text:
            return f"There are {Service.objects.count()} services."
        if "offer" in text:
            return f"There are {Offer.objects.count()} offers."
        return "Ask about platform overview, income, technicians, customers, services, bookings, offers, ratings, withdrawals, referrals, or a named person's details."


assistant = AdminDataAssistant()


def process_query(message, context=None):
    context = context or {}
    try:
        answer = assistant.answer(message)
        return {"success": True, "answer": answer}, context
    except Exception as error:
        print(f"Admin assistant error: {error}")
        return {"success": False, "answer": "I could not read the admin data right now."}, context
