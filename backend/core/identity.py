"""
Centralized Identity and Display Name Resolution for Seva Bandhu.

Handles consistent display-name and email resolution across Customer,
Technician, Service Request, and Admin representations:
1. Real person's name (Django User first_name + last_name) is preferred.
2. Explicit booking contact names are honored where applicable.
3. Username is used only as a final fallback.
4. Emails consistently come from the common Django User.
"""


def get_customer_display_name(customer=None, service=None, user=None):
    """
    Resolve customer display name with proper precedence:
    1. Explicit customer/contact name on booking (if service provided)
    2. Django User full name (if first_name/last_name populated on common User)
    3. Customer profile username
    4. Django User username
    5. Final fallback: service.customer_username or 'Valued Customer'
    """
    if service is not None:
        service_detail = getattr(service, 'service_detail', None)
        if service_detail is not None:
            contact_name = (
                getattr(service_detail, 'customer_name', None)
                or getattr(service_detail, 'contact_name', None)
            )
            if contact_name and str(contact_name).strip():
                return str(contact_name).strip()

        customer_name_attr = getattr(service, 'customer_name', None)
        if customer_name_attr and str(customer_name_attr).strip():
            return str(customer_name_attr).strip()

    if customer is None and service is not None:
        customer = getattr(service, 'customer', None)

    resolved_user = user
    if resolved_user is None and customer is not None:
        resolved_user = getattr(customer, 'user', None)

    if resolved_user is not None:
        first = getattr(resolved_user, 'first_name', '') or ''
        last = getattr(resolved_user, 'last_name', '') or ''
        full_name = f"{first} {last}".strip()
        if full_name:
            return full_name

    if customer and getattr(customer, 'username', None):
        c_username = str(customer.username).strip()
        if c_username:
            return c_username

    if resolved_user and getattr(resolved_user, 'username', None):
        u_username = str(resolved_user.username).strip()
        if u_username:
            return u_username

    if service and getattr(service, 'customer_username', None):
        sc_username = str(service.customer_username).strip()
        if sc_username:
            return sc_username

    return "Valued Customer"


def get_technician_display_name(technician=None, service=None, user=None):
    """
    Resolve technician display name with proper precedence:
    1. Django User full name (if first_name/last_name populated on common User)
    2. Technician profile username
    3. Django User username
    4. Final fallback: service.technician_username or 'Technician'
    """
    if technician is None and service is not None:
        technician = getattr(service, 'technician', None)

    resolved_user = user
    if resolved_user is None and technician is not None:
        resolved_user = getattr(technician, 'user', None)

    if resolved_user is not None:
        first = getattr(resolved_user, 'first_name', '') or ''
        last = getattr(resolved_user, 'last_name', '') or ''
        full_name = f"{first} {last}".strip()
        if full_name:
            return full_name

    if technician and getattr(technician, 'username', None):
        t_username = str(technician.username).strip()
        if t_username:
            return t_username

    if resolved_user and getattr(resolved_user, 'username', None):
        u_username = str(resolved_user.username).strip()
        if u_username:
            return u_username

    if service and getattr(service, 'technician_username', None):
        st_username = str(service.technician_username).strip()
        if st_username:
            return st_username

    return "Technician"


def get_user_common_email(user=None, profile=None):
    """
    Resolve email address strictly from the common Django User.
    Falls back to profile.email only if user.email is blank.
    """
    if user and getattr(user, 'email', None) and str(user.email).strip():
        return str(user.email).strip()
    if profile:
        profile_user = getattr(profile, 'user', None)
        if profile_user and getattr(profile_user, 'email', None) and str(profile_user.email).strip():
            return str(profile_user.email).strip()
        if getattr(profile, 'email', None) and str(profile.email).strip():
            return str(profile.email).strip()
    return ""

