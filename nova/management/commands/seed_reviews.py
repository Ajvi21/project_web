"""
Custom management command: `python manage.py seed_reviews`

Creates a pool of demo users and gives every project 10-15 reviews (1-5 stars)
together with a matching Albanian comment.

Design notes:
- ProjectReview has a UniqueConstraint on (project, user): one review per user
  per project. So we need a pool of distinct users, and for each project we
  pick a random subset of 10-15 of them.
- Comment text is chosen to match the star rating: 4-5 stars get positive
  comments, 3 stars mixed, 1-2 stars critical. This keeps the averages and the
  text consistent.
- Demo users are created with an unusable password (set_unusable_password),
  so nobody can actually log in as them. They exist only to own the reviews.
- Idempotent-ish: it skips a (project, user) pair if that review already
  exists, so re-running will not crash on the unique constraint. To start
  clean, use the --fresh flag which deletes seeded reviews/comments first.

Run from the project root (folder containing manage.py):

    python manage.py seed_reviews
    python manage.py seed_reviews --fresh     # wipe seeded data first
"""

import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from nova.models import Project, ProjectComment, ProjectReview


# Demo reviewers: (username, first_name, last_name).
# Usernames stay prefixed with "demo_" so the command can find and clean them,
# but the site displays the full real-looking name, never the username.
DEMO_USERS = [
    ('demo_arben', 'Arben', 'Hoxha'),
    ('demo_elira', 'Elira', 'Krasniqi'),
    ('demo_ilir', 'Ilir', 'Berisha'),
    ('demo_doruntina', 'Doruntina', 'Shala'),
    ('demo_gentian', 'Gentian', 'Dervishi'),
    ('demo_blerina', 'Blerina', 'Çela'),
    ('demo_kreshnik', 'Kreshnik', 'Leka'),
    ('demo_vjollca', 'Vjollca', 'Nika'),
    ('demo_endrit', 'Endrit', 'Gjoni'),
    ('demo_majlinda', 'Majlinda', 'Prifti'),
    ('demo_fatjon', 'Fatjon', 'Marku'),
    ('demo_teuta', 'Teuta', 'Bardhi'),
    ('demo_klodian', 'Klodian', 'Rama'),
    ('demo_drita', 'Drita', 'Vata'),
    ('demo_besnik', 'Besnik', 'Mema'),
    ('demo_sara', 'Sara', 'Lleshi'),
    ('demo_armando', 'Armando', 'Brahimi'),
    ('demo_jonida', 'Jonida', 'Kola'),
    ('demo_rexhep', 'Rexhep', 'Demiri'),
    ('demo_anisa', 'Anisa', 'Tahiri'),
    ('demo_florian', 'Florian', 'Beqiri'),
    ('demo_megi', 'Megi', 'Doçi'),
]

# Comments grouped by sentiment, picked to match the star rating.
POSITIVE = [  # 4-5 stars
    'Projekt fantastik, cilësia e ndërtimit duket që në foton e parë.',
    'Lokacioni dhe dizajni janë shumë mbresëlënëse. E rekomandoj pa hezitim.',
    'Hapësirat janë menduar shumë mirë, gjithçka duket profesionale.',
    'Pamja dhe materialet janë në nivel të lartë. Punë e shkëlqyer.',
    'Më pëlqeu shumë qasja moderne dhe ekuilibri me natyrën.',
    'Një nga projektet më të bukura që kam parë kohët e fundit.',
    'Detajet arkitekturore janë mahnitëse, duket investim serioz.',
    'Komuniteti dhe ambientet e përbashkëta janë pikërisht ç’kërkoja.',
    'Cilësi, estetikë dhe funksionalitet — të gjitha bashkë.',
    'Përshtypje shumë pozitive, ekipi ka bërë punë të jashtëzakonshme.',
]
MIXED = [  # 3 stars
    'Projekt i mirë në përgjithësi, por do doja më shumë gjelbërim.',
    'Dizajni është i bukur, megjithatë parkimi mund të ishte më i gjerë.',
    'Pamja e jashtme është e shkëlqyer, brendësia mund të përmirësohej pak.',
    'Vendndodhja është ideale, por çmimet duken pak të larta.',
    'Ka potencial të madh, pres të shoh përfundimin final.',
    'Mirë, por do të kisha preferuar më shumë hapësira të hapura.',
]
CRITICAL = [  # 1-2 stars
    'Pritshmëritë e mia ishin më të larta për këtë lokacion.',
    'Dizajni nuk më bindi plotësisht, megjithëse ideja është e mirë.',
    'Mendoj se mund të kishte më shumë vëmendje te detajet.',
    'Jo krejt ç’prisja, ndoshta përfundimi do ta ndryshojë përshtypjen.',
]


def comment_for_stars(stars):
    if stars >= 4:
        return random.choice(POSITIVE)
    if stars == 3:
        return random.choice(MIXED)
    return random.choice(CRITICAL)


class Command(BaseCommand):
    help = 'Seed 10-15 reviews and matching comments per project using demo users.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fresh',
            action='store_true',
            help='Delete previously seeded demo reviews/comments before seeding.',
        )

    def handle(self, *args, **options):
        random.seed(42)  # reproducible results

        # 1. Make sure the demo users exist.
        users = []
        for username, first_name, last_name in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': f'{username}@example.com',
                },
            )
            if created:
                user.set_unusable_password()
                user.save()
            else:
                # Keep names in sync if the pool was updated after first run.
                if user.first_name != first_name or user.last_name != last_name:
                    user.first_name = first_name
                    user.last_name = last_name
                    user.save()
            users.append(user)
        self.stdout.write(f'Demo users ready: {len(users)}')

        # 2. Optionally wipe previously seeded data (only from demo users).
        if options['fresh']:
            r = ProjectReview.objects.filter(user__in=users).delete()
            c = ProjectComment.objects.filter(user__in=users).delete()
            self.stdout.write(self.style.WARNING(
                f'Fresh start: removed {r[0]} reviews and {c[0]} comments from demo users.'
            ))

        projects = Project.objects.all()
        if not projects:
            self.stdout.write(self.style.ERROR('No projects found. Run seed_data first.'))
            return

        total_reviews = 0
        total_comments = 0

        for project in projects:
            # Pick 10-15 distinct reviewers for this project.
            n = random.randint(10, 15)
            reviewers = random.sample(users, min(n, len(users)))

            for user in reviewers:
                # Skip if this user already reviewed this project (unique constraint).
                if ProjectReview.objects.filter(project=project, user=user).exists():
                    continue

                # Weighted star distribution: mostly 4-5, some 3, few 1-2.
                stars = random.choices(
                    [5, 4, 3, 2, 1],
                    weights=[40, 30, 18, 8, 4],
                    k=1,
                )[0]

                ProjectReview.objects.create(project=project, user=user, stars=stars)
                total_reviews += 1

                # Most reviewers also leave a comment (about 80%).
                if random.random() < 0.8:
                    ProjectComment.objects.create(
                        project=project,
                        user=user,
                        content=comment_for_stars(stars),
                    )
                    total_comments += 1

            count = project.reviews.count()
            self.stdout.write(self.style.SUCCESS(
                f'  + {project.name}: {count} reviews total'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Added {total_reviews} reviews and {total_comments} comments '
            f'across {projects.count()} projects.'
        ))
