from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from functools import wraps

from .models import (
    customer_signup,
    Technician_signup,
    Service,
    ServiceRequest,
    ServiceAddress,
    ServiceDetail,
    TechnicianNotification
)

# --- DECORATOR ---
def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin_login')
        if not request.user.is_superuser:
            # Optionally clear session if they are a regular user trying to access admin
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# --- AUTHENTICATION ---
def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard')
        
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'You do not have Super Admin privileges.')
        else:
            messages.error(request, 'Invalid username or password.')
            
    return render(request, 'admin_custom/login.html')

def admin_logout_view(request):
    logout(request)
    return redirect('admin_login')

# --- DASHBOARD ---
@superuser_required
def admin_dashboard_view(request):
    customers = customer_signup.objects.all()
    technicians = Technician_signup.objects.all()
    services = Service.objects.all()
    requests = ServiceRequest.objects.all()

    context = {
        'total_customers': customers.count(),
        'total_technicians': technicians.count(),
        'total_services': services.count(),
        'active_services': services.filter(is_enabled=True).count(),
        'disabled_services': services.filter(is_enabled=False).count(),
        'total_requests': requests.count(),
        'pending_requests': requests.filter(status='Pending').count(),
        'completed_requests': requests.filter(status='Completed').count(),
        'recent_customers': customers.order_by('-id')[:5],
        'recent_technicians': technicians.order_by('-id')[:5],
        'recent_services': services.order_by('-id')[:5],
        'recent_requests': requests.order_by('-created_at')[:5],
    }
    return render(request, 'admin_custom/dashboard.html', context)

# --- CUSTOMERS ---
@superuser_required
def admin_customers_list(request):
    query = request.GET.get('q', '')
    customers = customer_signup.objects.all().order_by('-id')
    
    if query:
        customers = customers.filter(
            username__icontains=query
        ) | customers.filter(
            email__icontains=query
        ) | customers.filter(
            contact__icontains=query
        )

    paginator = Paginator(customers.distinct(), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_custom/customers.html', {'page_obj': page_obj, 'query': query})

@superuser_required
def admin_customer_detail(request, id):
    customer = get_object_or_404(customer_signup, id=id)
    requests = ServiceRequest.objects.filter(customer_username=customer.username).order_by('-created_at')
    return render(request, 'admin_custom/customer_detail.html', {'customer': customer, 'requests': requests})

@superuser_required
def admin_customer_deactivate(request, id):
    if request.method == "POST":
        customer = get_object_or_404(customer_signup, id=id)
        user = customer.user
        if user.is_active:
            user.is_active = False
            messages.success(request, f'Customer {customer.username} deactivated successfully.')
        else:
            user.is_active = True
            messages.success(request, f'Customer {customer.username} activated successfully.')
        user.save()
    return redirect('admin_customers_list')

# --- TECHNICIANS ---
@superuser_required
def admin_technicians_list(request):
    query = request.GET.get('q', '')
    technicians = Technician_signup.objects.all().order_by('-id')
    
    if query:
        technicians = technicians.filter(
            username__icontains=query
        ) | technicians.filter(
            email__icontains=query
        ) | technicians.filter(
            service_category__icontains=query
        )

    paginator = Paginator(technicians.distinct(), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_custom/technicians.html', {'page_obj': page_obj, 'query': query})

@superuser_required
def admin_technician_detail(request, id):
    technician = get_object_or_404(Technician_signup, id=id)
    requests = ServiceRequest.objects.filter(technician_username=technician.username).order_by('-created_at')
    return render(request, 'admin_custom/technician_detail.html', {'technician': technician, 'requests': requests})

@superuser_required
def admin_technician_deactivate(request, id):
    if request.method == "POST":
        technician = get_object_or_404(Technician_signup, id=id)
        user = technician.user
        if user.is_active:
            user.is_active = False
            messages.success(request, f'Technician {technician.username} deactivated successfully.')
        else:
            user.is_active = True
            messages.success(request, f'Technician {technician.username} activated successfully.')
        user.save()
    return redirect('admin_technicians_list')

# --- SERVICES ---
@superuser_required
def admin_services_list(request):
    query = request.GET.get('q', '')
    services = Service.objects.all().order_by('name')
    if query:
        services = services.filter(name__icontains=query)
    
    paginator = Paginator(services, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_custom/services.html', {'page_obj': page_obj, 'query': query})

@superuser_required
def admin_service_add(request):
    if request.method == "POST":
        name = request.POST.get('name')
        price = request.POST.get('price')
        is_enabled = request.POST.get('is_enabled') == 'on'
        image = request.FILES.get('image')
        
        if Service.objects.filter(name__iexact=name).exists():
            messages.error(request, 'A service with this name already exists.')
        else:
            Service.objects.create(
                name=name,
                price=price,
                is_enabled=is_enabled,
                image=image
            )
            messages.success(request, 'Service created successfully.')
            return redirect('admin_services_list')

    return render(request, 'admin_custom/service_form.html', {'action': 'Add'})

@superuser_required
def admin_service_edit(request, id):
    service = get_object_or_404(Service, id=id)
    
    if request.method == "POST":
        service.name = request.POST.get('name')
        service.price = request.POST.get('price')
        service.is_enabled = request.POST.get('is_enabled') == 'on'
        
        image = request.FILES.get('image')
        if image:
            service.image = image
            
        try:
            service.save()
            messages.success(request, 'Service updated successfully.')
            return redirect('admin_services_list')
        except Exception as e:
            messages.error(request, f'Error updating service: {str(e)}')
            
    return render(request, 'admin_custom/service_form.html', {'action': 'Edit', 'service': service})

@superuser_required
def admin_service_toggle(request, id):
    if request.method == "POST":
        service = get_object_or_404(Service, id=id)
        service.is_enabled = not service.is_enabled
        service.save()
        status = "enabled" if service.is_enabled else "disabled"
        messages.success(request, f'Service {service.name} has been {status}.')
    return redirect('admin_services_list')

@superuser_required
def admin_service_delete(request, id):
    if request.method == "POST":
        service = get_object_or_404(Service, id=id)
        # Check if the service name is used in ServiceDetail records
        is_used = ServiceDetail.objects.filter(service_category=service.name).exists()
        if is_used:
            # Instead of deleting, just disable it
            service.is_enabled = False
            service.save()
            messages.warning(request, f'Service {service.name} is referenced by historical requests. It has been disabled instead of deleted.')
        else:
            service.delete()
            messages.success(request, f'Service {service.name} deleted successfully.')
    return redirect('admin_services_list')


# --- SERVICE REQUESTS ---
@superuser_required
def admin_service_requests_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    requests_qs = ServiceRequest.objects.all().select_related('service_detail', 'service_address').order_by('-created_at')
    
    if query:
        requests_qs = requests_qs.filter(
            customer_username__icontains=query
        ) | requests_qs.filter(
            technician_username__icontains=query
        ) | requests_qs.filter(
            service_detail__service_category__icontains=query
        )
        
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
        
    paginator = Paginator(requests_qs.distinct(), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_custom/service_requests.html', {
        'page_obj': page_obj, 
        'query': query,
        'status_filter': status_filter
    })

# --- SERVICE ADDRESSES ---
@superuser_required
def admin_service_addresses_list(request):
    query = request.GET.get('q', '')
    addresses = ServiceAddress.objects.all().order_by('-created_at')
    if query:
        addresses = addresses.filter(city__icontains=query) | addresses.filter(pincode__icontains=query) | addresses.filter(street_area__icontains=query)
    
    paginator = Paginator(addresses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'admin_custom/service_addresses.html', {'page_obj': page_obj, 'query': query})

# --- SERVICE DETAILS ---
@superuser_required
def admin_service_details_list(request):
    query = request.GET.get('q', '')
    details = ServiceDetail.objects.all().order_by('-created_at')
    if query:
        details = details.filter(service_category__icontains=query) | details.filter(contact_number__icontains=query)
    
    paginator = Paginator(details, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'admin_custom/service_details.html', {'page_obj': page_obj, 'query': query})

# --- TECHNICIAN NOTIFICATIONS ---
@superuser_required
def admin_notifications_list(request):
    query = request.GET.get('q', '')
    notifications = TechnicianNotification.objects.all().select_related('technician').order_by('-created_at')
    if query:
        notifications = notifications.filter(technician__username__icontains=query) | notifications.filter(title__icontains=query)
        
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'admin_custom/technician_notifications.html', {'page_obj': page_obj, 'query': query})

