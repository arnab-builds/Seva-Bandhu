from django.conf import settings


def supabase_config(request):
    """Expose only runtime Supabase web configuration to the templates that need it."""
    return {"supabase_config": getattr(settings, "SUPABASE_CONFIG", {})}


def firebase_config(request):
    """Expose legacy firebase_config if referenced."""
    return {"firebase_config": getattr(settings, "FIREBASE_CONFIG", {})}

