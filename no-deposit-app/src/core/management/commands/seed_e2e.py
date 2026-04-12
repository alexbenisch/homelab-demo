"""
Management command: seed_e2e

Creates a reproducible test property for the full tenant→agent→landlord
end-to-end test cycle. Must be run after all three test users (tenant1,
landlord1, agent1) have logged in at least once so their UserProfiles exist.

Usage:
    python manage.py seed_e2e
    python manage.py seed_e2e --reset        # delete previous cycle data first
    python manage.py seed_e2e --landlord-email landlord1@example.com

Output (last line, machine-parseable):
    PROPERTY_ID=<n>

Exit codes:
    0 — property seeded (or already exists); ID printed
    1 — no landlord profile found (run e2e login pass first)
"""

from django.core.management.base import BaseCommand, CommandError

SENTINEL_ADDRESS = "E2E Test Property, 1 Demo Street, London E1 1AA"


class Command(BaseCommand):
    help = "Seed a test property for the e2e CRUD flow"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all applications/guarantees/claims for the test property before seeding",
        )
        parser.add_argument(
            "--landlord-email",
            default=None,
            help="Find landlord profile by email (default: first profile with role=landlord)",
        )

    def handle(self, *args, **options):
        from properties.models import Property
        from users.models import UserProfile

        # ── 1. Find landlord profile ──────────────────────────────────────────
        if options["landlord_email"]:
            landlord = UserProfile.objects.filter(
                role="landlord", email=options["landlord_email"]
            ).first()
            if not landlord:
                raise CommandError(
                    f"No landlord profile found with email={options['landlord_email']!r}. "
                    "Has landlord1 logged in yet?"
                )
        else:
            landlord = UserProfile.objects.filter(role="landlord").order_by("created_at").first()
            if not landlord:
                raise CommandError(
                    "No landlord UserProfile found in the database.\n"
                    "Run the login-only e2e pass first so landlord1's profile is created:\n"
                    "  python scripts/e2e-api-tests.py\n"
                    "Then re-run this command."
                )

        ident = landlord.email or landlord.keycloak_sub
        self.stdout.write(f"Using landlord: {ident} (pk={landlord.pk})")

        # ── 2. Find or create the sentinel property ───────────────────────────
        prop, created = Property.objects.get_or_create(
            address=SENTINEL_ADDRESS,
            defaults={
                "landlord": landlord,
                "rent_amount": "1200.00",
                "status": "available",
            },
        )

        if not created:
            self.stdout.write(f"Test property already exists (pk={prop.pk})")

            # ── 3. Optionally reset cycle data ────────────────────────────────
            if options["reset"]:
                self._reset(prop)
                # Ensure property is available again after reset
                prop.status = "available"
                prop.save(update_fields=["status"])
                self.stdout.write(self.style.WARNING("Test data reset complete"))
            else:
                self.stdout.write(
                    "  Pass --reset to delete previous cycle data (applications/guarantees/claims)"
                )
        else:
            self.stdout.write(self.style.SUCCESS(f"Created test property (pk={prop.pk})"))

        # Machine-parseable output — always last line
        self.stdout.write(f"PROPERTY_ID={prop.pk}")

    def _reset(self, prop):
        """Delete all test cycle data for this property, oldest dependencies first."""
        from claims.models import DamageClaim
        from guarantees.models import Guarantee
        from properties.models import RentalApplication

        applications = RentalApplication.objects.filter(property=prop)
        guarantees = Guarantee.objects.filter(application__in=applications)
        claims = DamageClaim.objects.filter(guarantee__in=guarantees)

        claim_count = claims.count()
        guarantee_count = guarantees.count()
        application_count = applications.count()

        claims.delete()
        guarantees.delete()
        applications.delete()

        self.stdout.write(
            f"  Deleted: {claim_count} claim(s), "
            f"{guarantee_count} guarantee(s), "
            f"{application_count} application(s)"
        )
