"""
Custom management command: `python manage.py seed_data`

Seeds the database with the same projects and chatbot FAQs that were hard-coded
in the original static Nova Build project (database/init_database.py).

Idempotent: running it more than once will not duplicate rows because we use
update_or_create / get_or_create on stable unique fields (name for projects,
question for FAQs).
"""

from django.core.management.base import BaseCommand

from nova.models import ChatbotFaq, Project


PROJECTS = [
    {
        'name': 'Dhërmi Coast Villas',
        'location': 'Jug i Shqipërisë',
        'category': 'rezidenciale',
        'status': 'koncept',
        'year': 2026,
        'floor_area_m2': 1800,
        'description': (
            'Vila moderne pranë bregdetit me qasje të pastër arkitekturore, '
            'privatësi dhe pamje të hapur drejt detit.'
        ),
    },
    {
        'name': 'Park Avenue Center',
        'location': 'Tiranë',
        'category': 'mixed_use',
        'status': 'ne_ndertim',
        'year': 2026,
        'floor_area_m2': 14500,
        'description': (
            'Projekt mixed-use me një kombinim të zyrave, njësive tregtare dhe '
            'apartamenteve premium në qendër të Tiranës.'
        ),
    },
    {
        'name': 'River Residence',
        'location': 'Tiranë',
        'category': 'multifunksional',
        'status': 'ne_ndertim',
        'year': 2025,
        'floor_area_m2': 9200,
        'description': (
            'Objekt multifunksional me identitet urban të fortë dhe organizim '
            'efikas të hapësirave të brendshme.'
        ),
    },
    {
        'name': 'Green Gate Living',
        'location': 'Tiranë',
        'category': 'apartamente',
        'status': 'perfunduar',
        'year': 2023,
        'floor_area_m2': 11000,
        'description': (
            'Kompleks rezidencial me fokus te gjelbërimi, drita natyrale dhe '
            'cilësia e përfundimeve.'
        ),
    },
    {
        'name': 'Business Center Prime',
        'location': 'Tiranë',
        'category': 'biznes',
        'status': 'perfunduar',
        'year': 2022,
        'floor_area_m2': 7800,
        'description': (
            'Qendër biznesi me fasadë moderne, recepsion, parking dhe një '
            'prezencë të fortë urbane.'
        ),
    },
    {
        'name': 'Tower Bridge Living',
        'location': 'Tiranë',
        'category': 'rezidenciale',
        'status': 'perfunduar',
        'year': 2024,
        'floor_area_m2': 10500,
        'description': (
            'Rezidencë urbane me ballkone të gjera, vetrata moderne dhe '
            'standard të lartë komoditeti.'
        ),
    },
]


FAQS = [
    {
        'question': 'Cilat projekte ofroni?',
        'keywords': 'projekt,projektet,rezidenca,ndertim,ndërtim,vila,biznes',
        'answer': (
            'Nova Build prezanton projekte rezidenciale dhe biznesi si Dhërmi '
            'Coast Villas, Park Avenue Center, River Residence dhe Green Gate Living.'
        ),
        'is_featured': True,
    },
    
    {
        'question': "Si mund t'ju kontaktoj?",
        'keywords': 'kontakt,telefon,email,takim,rezervo,adresa',
        'answer': (
            'Mund të kontaktosh Nova Build në +355 69 700 40 40, me email '
            'info@novabuild.al ose përmes formës në faqen Kontakt.'
        ),
        'is_featured': True,
    },
    
    {
        'question': 'A është faqja responsive?',
        'keywords': 'responsive,telefon,mobile,celular,tablet',
        'answer': (
            'Po, faqja dhe chatbot-i janë responsive dhe përshtaten për '
            'desktop, tablet dhe telefon.'
        ),
        'is_featured': True,
    },
    {
        'question': 'Cilat janë funksionalitetet e faqes?',
        'keywords': 'funksionalitet,funksionalitetet,cfare ben,çfare bën,ofron',
        'answer': (
            'Faqja ofron navigim në faqen kryesore, projektet, lajmet, rreth '
            'nesh, kontaktin dhe chatbot-in ndihmës për pyetje të shpejta.'
        ),
        'is_featured': False,
    },
    {
        'question': 'Me cilat teknologji është ndërtuar?',
        'keywords': 'teknologji,html,css,javascript,bootstrap,django,python',
        'answer': (
            'Faqja është ndërtuar me Django 5.1, SQLite, Bootstrap 5.3, HTML, '
            'CSS dhe JavaScript, sipas arkitekturës MTV.'
        ),
        'is_featured': False,
    },
    {
        'question': 'Çfarë bën chatbot-i?',
        'keywords': 'chatbot,asistent,pyetje,pergjigje,përgjigje',
        'answer': (
            'Chatbot-i ruan pyetjet dhe përgjigjet në databazë, kërkon në '
            'tabelën ChatbotFaq dhe kthen përgjigjen më të përshtatshme.'
        ),
        'is_featured': False,
    },
    {
        'question': 'Në cilat zona ndodhen projektet?',
        'keywords': 'zone,zona,vendndodhje,lokacion,tirane,tiranë,bregdet,jug',
        'answer': (
            'Shumica e projekteve tona ndodhen në Tiranë, ndërsa Dhërmi Coast '
            'Villas ndodhet në Jug të Shqipërisë.'
        ),
        'is_featured': False,
    },
]


class Command(BaseCommand):
    help = 'Seed the database with Nova Build sample projects and chatbot FAQs.'

    def handle(self, *args, **options):
        # Projects --------------------------------------------------------
        for data in PROJECTS:
            project, created = Project.objects.update_or_create(
                name=data['name'],
                defaults={k: v for k, v in data.items() if k != 'name'},
            )
            self.stdout.write(
                ('  + ' if created else '  ~ ') + f'Project: {project.name}'
            )

        # Chatbot FAQs ----------------------------------------------------
        for data in FAQS:
            faq, created = ChatbotFaq.objects.update_or_create(
                question=data['question'],
                defaults={k: v for k, v in data.items() if k != 'question'},
            )
            self.stdout.write(
                ('  + ' if created else '  ~ ') + f'FAQ: {faq.question}'
            )

        self.stdout.write(self.style.SUCCESS(
            f'Done. {Project.objects.count()} projects and '
            f'{ChatbotFaq.objects.count()} FAQs in the database.'
        ))
