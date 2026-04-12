from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render


def health(request):
    return JsonResponse({"status": "ok"})


def landing(request):
    return render(request, "core/landing.html", {
        "email": request.jwt_email,
        "roles": request.jwt_roles,
    })


def _portal_view(request, portal, required_role, template):
    if required_role not in request.jwt_roles:
        return HttpResponseForbidden(
            f"<h1>403 Forbidden</h1><p>This portal requires the <strong>{required_role}</strong> role.</p>",
            content_type="text/html",
        )
    return render(request, template, {
        "email": request.jwt_email,
        "roles": request.jwt_roles,
        "portal": portal,
    })


def tenant_portal(request):
    return _portal_view(request, "tenant", "tenant", "core/tenant.html")


def landlord_portal(request):
    return _portal_view(request, "landlord", "landlord", "core/landlord.html")


def agency_portal(request):
    return _portal_view(request, "agency", "agent", "core/agency.html")
