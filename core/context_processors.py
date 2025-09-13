from .models import SiteSettings

def site_context(request):
    site_settings = SiteSettings.objects.all().first()
    return {'site_context':site_settings}
