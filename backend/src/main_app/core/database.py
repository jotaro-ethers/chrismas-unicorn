from supabase import Client, create_client
from .config import settings


def get_supabase_client() -> Client:
    """Get a Supabase client with anon key."""
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_supabase_service_client() -> Client:
    """Get a Supabase client with service role key for admin operations."""
    return create_client(settings.supabase_url, settings.supabase_service_key)