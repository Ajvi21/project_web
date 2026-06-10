"""
Custom management command: `python manage.py seed_news`

Creates a set of 12 company news articles for Nova Build, written in a natural
Albanian voice. Each article has a heading (title) and a full body shown on its
own page when clicked.

Notes:
- Articles are authored by the first staff/superuser found, so the author shows
  up as a real account (e.g. Ajvi). If no staff user exists, it falls back to
  the first user in the database.
- Idempotent: an article is skipped if one with the same title already exists,
  so re-running will not create duplicates.
- Use --fresh to delete all previously seeded articles (matched by title) and
  recreate them.

Run from the project root (folder containing manage.py):

    python manage.py seed_news
    python manage.py seed_news --fresh
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from nova.models import NewsPost


ARTICLES = [
    (
        'Nova Build nis punimet për rezidencën Skyline Terrace',
        'Këtë javë nisën zyrtarisht punimet për Skyline Terrace, rezidencën tonë '
        'të re me nëntë kate pranë Liqenit të Thatë. Faza e parë përfshin '
        'gërmimet dhe themelet, ndërsa struktura kryesore pritet të ngrihet brenda '
        'vitit të ardhshëm.\n\n'
        'Projekti është menduar për dritë natyrale maksimale dhe tarraca '
        'panoramike në çdo apartament. Të interesuarit mund të rezervojnë një '
        'takim prezantues përmes faqes së kontaktit.'
    ),
    (
        'Green Gate Living vlerësohet për cilësinë në ndërtim',
        'Kompleksi ynë rezidencial Green Gate Living mori një vlerësim të veçantë '
        'në panairin kombëtar të ndërtimit. Juria veçoi standardin e përfundimeve, '
        'gjelbërimin e brendshëm dhe efikasitetin energjetik të objektit.\n\n'
        'Ky njohje vjen pas dy vitesh punë dhe konfirmon angazhimin tonë për '
        'cilësi në çdo detaj. Faleminderit të gjithë banorëve që na besuan.'
    ),
    (
        'Hapen rezervimet për Marina Bay në Durrës',
        'Pas interesimit të lartë, kemi hapur zyrtarisht rezervimet për '
        'apartamentet e fazës së parë në Marina Bay. Klientët e parë përfitojnë '
        'çmime promocionale dhe mundësi personalizimi të ambienteve të brendshme.\n\n'
        'Apartamentet ndodhen vetëm 150 metra nga deti dhe ofrojnë pamje të hapur '
        'drejt gjirit të Durrësit. Kontaktoni zyrën tonë për detaje.'
    ),
    (
        'Park Avenue Center arrin gjysmën e strukturës',
        'Punimet në Park Avenue Center ecin sipas planit. Struktura ka arritur '
        'gjysmën e lartësisë së planifikuar dhe faza e fasadës pritet të nisë në '
        'muajt e ardhshëm.\n\n'
        'Ky projekt mixed-use do të bashkojë zyra, njësi tregtare dhe apartamente '
        'premium në një nga zonat më dinamike të Tiranës.'
    ),
    (
        'Një fjalë për filozofinë tonë të ndërtimit',
        'Në Nova Build besojmë se një ndërtesë e mirë nuk matet vetëm me metra '
        'katrorë, por me mënyrën si njerëzit e jetojnë hapësirën. Prandaj çdo '
        'projekt nis me një pyetje të thjeshtë: si do të ndihet dikush që jeton '
        'këtu çdo ditë?\n\n'
        'Drita, ajrosja, qetësia dhe lidhja me mjedisin përreth janë po aq të '
        'rëndësishme sa pamja e jashtme. Kjo qasje na ka udhëhequr që në projektin '
        'tonë të parë.'
    ),
    (
        'Teknologjitë që përdorim për efikasitet energjetik',
        'Çdo objekt i ri i Nova Build projektohet me izolim termik të '
        'përmirësuar, dritare me performancë të lartë dhe sisteme që ulin '
        'konsumin e energjisë.\n\n'
        'Qëllimi ynë është që banorët të kenë komoditet gjatë gjithë vitit, me '
        'kosto sa më të ulëta mirëmbajtjeje. Investimi në teknologji sot do të '
        'thotë kursim afatgjatë për familjet.'
    ),
    (
        'Tower Bridge Living: jeta urbane në qendër',
        'Tower Bridge Living tashmë është i banuar dhe po krijon një komunitet të '
        'gjallë në zemër të qytetit. Dyqanet dhe kafenetë në nivelin e rrugës i '
        'kanë dhënë zonës një energji të re.\n\n'
        'Ballkonet e gjera dhe dritaret nga dyshemeja te tavani mbeten ndër '
        'detajet më të pëlqyera nga banorët tanë.'
    ),
    (
        'River Residence afër përfundimit të fazës strukturore',
        'Punimet në River Residence po i afrohen përfundimit të fazës '
        'strukturore. Vendndodhja buzë lumit dhe shëtitorja e jashtme do të jenë '
        'pikat kryesore të këtij projekti multifunksional.\n\n'
        'Në muajt në vijim do të nisë instalimi i fasadës dhe rregullimi i '
        'hapësirave të gjelbra përreth.'
    ),
    (
        'Dhërmi Coast Villas: koncepti merr formë',
        'Po punojmë në fazën e konceptit për Dhërmi Coast Villas, një grup vilash '
        'moderne pranë bregdetit jugor. Arkitektura minimaliste dhe pamja e hapur '
        'drejt detit Jon janë në qendër të dizajnit.\n\n'
        'Synojmë të krijojmë një hapësirë që respekton peizazhin natyror dhe '
        'ofron privatësi e qetësi për banorët.'
    ),
    (
        'Si të rezervoni një takim me ekipin tonë',
        'Nëse jeni të interesuar për një nga projektet tona ose dëshironi thjesht '
        'më shumë informacion, mund të rezervoni një takim falas me ekipin tonë.\n\n'
        'Plotësoni formën në faqen e kontaktit ose na telefononi drejtpërdrejt. '
        'Do t’ju përgjigjemi sa më shpejt për të caktuar një orar të përshtatshëm.'
    ),
    (
        'Business Center Prime: hapësira moderne për biznese',
        'Business Center Prime vazhdon të tërheqë kompani që kërkojnë zyra '
        'bashkëkohore me lokacion strategjik. Fasada moderne dhe ambientet '
        'profesionale e bëjnë një adresë të dëshiruar pune.\n\n'
        'Disa hapësira janë ende të disponueshme. Kontaktoni për të mësuar më '
        'shumë rreth mundësive të qirasë.'
    ),
    (
        'Faleminderit komunitetit tonë në rritje',
        'Ndërsa mbyllim një periudhë me shumë projekte aktive, duam të falënderojmë '
        'çdo klient, banor dhe partner që na ka shoqëruar deri këtu.\n\n'
        'Nova Build u ndërtua mbi besimin dhe cilësinë, dhe ky komunitet në rritje '
        'është motivimi ynë më i madh për të vazhduar. Kjo është vetëm fillimi.'
    ),
]


class Command(BaseCommand):
    help = 'Seed 12 Nova Build news articles in Albanian.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fresh',
            action='store_true',
            help='Delete previously seeded articles (by title) before seeding.',
        )

    def handle(self, *args, **options):
        # Pick an author: first staff/superuser, else first user.
        author = (
            User.objects.filter(is_staff=True).order_by('id').first()
            or User.objects.order_by('id').first()
        )
        if author is None:
            self.stdout.write(self.style.ERROR(
                'No users found. Create a superuser first (python manage.py createsuperuser).'
            ))
            return

        titles = [title for title, _ in ARTICLES]

        if options['fresh']:
            deleted = NewsPost.objects.filter(title__in=titles).delete()
            self.stdout.write(self.style.WARNING(
                f'Fresh start: removed {deleted[0]} existing seeded articles.'
            ))

        created = 0
        skipped = 0

        # (days_ago, hour, minute) for each article, newest first.
        # This spreads the 12 posts across roughly the last five months,
        # each on a different day and at a different time of day.
        date_offsets = [
            (3, 9, 15), (12, 14, 40), (21, 11, 5), (34, 16, 20),
            (48, 8, 50), (63, 13, 10), (79, 10, 35), (97, 15, 55),
            (118, 9, 45), (134, 17, 25), (152, 12, 30), (171, 14, 5),
        ]
        now = timezone.now()

        for index, (title, content) in enumerate(ARTICLES):
            if NewsPost.objects.filter(title=title).exists():
                self.stdout.write(self.style.WARNING(f'  ~ skip (exists): {title}'))
                skipped += 1
                continue

            post = NewsPost.objects.create(title=title, content=content, author=author)

            # date_posted uses auto_now_add=True, which forces "now" on create.
            # We override it afterwards with .update(), which bypasses auto_now_add.
            days, hour, minute = date_offsets[index % len(date_offsets)]
            posted_at = (now - timedelta(days=days)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            NewsPost.objects.filter(pk=post.pk).update(date_posted=posted_at)

            self.stdout.write(self.style.SUCCESS(
                f'  + {title}  ({posted_at:%d %b %Y, %H:%M})'
            ))
            created += 1

        author_name = author.get_full_name() or author.username
        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {created} created, {skipped} skipped. '
            f'Author: {author_name}. '
            f'Total news now: {NewsPost.objects.count()}.'
        ))
