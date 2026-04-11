# Keycloak Admin Interface Security Best Practices

## Table of Contents

-   [Overview](#overview)
-   [Best Practices](#best-practices)
-   [Network Architecture](#network-architecture)
-   [Authentication Hardening](#authentication-hardening)
-   [Monitoring and Auditing](#monitoring-and-auditing)
-   [Is Public Exposure Ever
    Acceptable?](#is-public-exposure-ever-acceptable)
-   [Recommended Setup](#recommended-setup)
-   [Summary](#summary)

------------------------------------------------------------------------

## Overview

The Keycloak Admin Console is a high-value attack target and must be
secured accordingly. Exposing it improperly can lead to full system
compromise.

------------------------------------------------------------------------

## Best Practices

### 1. Keep Admin Interface Private

-   Restrict access to internal networks only
-   Use VPN (WireGuard, Tailscale) or SSH tunnels
-   Avoid public exposure

### 2. Separate Public and Admin Endpoints

-   Public: OIDC endpoints (`/realms/*`)
-   Private: Admin endpoints (`/admin`, `/realms/master`)

### 3. Use a Reverse Proxy

-   Restrict access by IP allowlists
-   Optionally enforce mTLS
-   Add additional authentication layer

------------------------------------------------------------------------

## Network Architecture

Recommended flow:

Internet → Reverse Proxy → Keycloak (Private Network)

Admin access: - Only via VPN or SSH tunnel

------------------------------------------------------------------------

## Authentication Hardening

-   Enable MFA (2FA) for admin users
-   Disable default admin account
-   Enforce strong password policies
-   Enable brute-force protection
-   Apply least privilege principle

------------------------------------------------------------------------

## Monitoring and Auditing

-   Enable admin event logging
-   Forward logs to SIEM systems (ELK, Splunk)
-   Monitor:
    -   Failed login attempts
    -   Role changes
    -   Configuration changes

------------------------------------------------------------------------

## Is Public Exposure Ever Acceptable?

Only in limited scenarios: - Temporary setups - Demos or testing
environments

Risks: - Credential stuffing attacks - Exploitation of vulnerabilities -
Misconfiguration exposure

------------------------------------------------------------------------

## Recommended Setup

-   Keycloak deployed in private network
-   Public access limited to OIDC endpoints
-   Admin access via:
    -   VPN
    -   SSH tunnel
-   Firewall rules enforced via infrastructure-as-code (e.g., Terraform)

Optional: - Reverse proxy (Traefik, NGINX) with: - IP whitelisting -
Rate limiting

------------------------------------------------------------------------

## Summary

-   Best practice: Admin interface is NOT publicly accessible
-   Acceptable: Public but heavily restricted
-   Bad practice: Fully open admin interface

Rule of thumb: If `/admin` is reachable from the internet, it is being
actively targeted.
