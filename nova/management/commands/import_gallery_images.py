"""
Custom management command: `python manage.py import_gallery_images`

Imports the photos from the `media_import/` folder into each project's gallery
(the ProjectImage model), with a short Albanian caption for every photo, just
like the captions shown on the public project pages.

How it works:
- Each subfolder of media_import/ maps to one project (by its exact name in
  the database).
- Files are read in sorted order. The 1st, 2nd and 3rd photo of each project
  get the three captions defined in GALLERY below.
- Idempotent: re-running it skips photos that were already imported, so you
  will not get duplicates.

Run it from the project root (the folder that contains manage.py):

    python manage.py import_gallery_images
"""

from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from nova.models import Project, ProjectImage


# Maps each media_import subfolder -> (exact project name in the DB, [captions])
# The captions are in the same order as the sorted image files (1, 2, 3).
GALLERY = {
    'dhermi_coast_villas': {
        'project': 'Dhërmi Coast Villas',
        'captions': [
            'Pamje nga ajri e kompleksit të vilave dhe bregdetit',
            'Pishina dhe tarraca me pamje nga deti Jon',
            'Vilat e ndriçuara në mbrëmje',
        ],
    },
    'park_avenue_center': {
        'project': 'Park Avenue Center',
        'captions': [
            'Sheshi i hyrjes me hapësira publike dhe gjelbërim',
            'Detaj i fasadës nga xhami dhe çeliku',
            'Korridori tregtar në katin përdhe',
        ],
    },
    'river_residence': {
        'project': 'River Residence',
        'captions': [
            'Shëtitorja buzë lumit në mbrëmje',
            'Reflektimi i ndërtesës në ujë',
            'Tarraca e përbashkët me pamje nga lumi',
        ],
    },
    'green_gate_living': {
        'project': 'Green Gate Living',
        'captions': [
            'Oborri i gjelbër i parë nga lart',
            'Banorët duke shijuar hapësirat e përbashkëta',
            'Ndriçimi i oborrit në mbrëmje',
        ],
    },
    'business_center_prime': {
        'project': 'Business Center Prime',
        'captions': [
            'Qendra e biznesit e ndriçuar natën',
            'Korridori i brendshëm me ndarje xhami',
            'Hyrja në nivelin e rrugës',
        ],
    },
    'tower_bridge_living': {
        'project': 'Tower Bridge Living',
        'captions': [
            'Ballkonet e gjera me pamje urbane',
            'Dyqane dhe kafene në nivelin e rrugës',
            'Kulla e ndriçuar mbi panoramën e qytetit',
        ],
    },
    'skyline_terrace': {
        'project': 'Skyline Terrace',
        'captions': [
            'Pamje nga ajri e kullës dhe liqenit',
            'Tarracat panoramike në perëndim të diellit',
            'Pamja nga ballkoni drejt liqenit',
        ],
    },
    'atrium_office_park': {
        'project': 'Atrium Office Park',
        'captions': [
            'Atriumi qendror me çati xhami',
            'Hapësirat e zyrave me dritë natyrale',
            'Fasada e ndërtesës e ndriçuar natën',
        ],
    },
    'marina_bay_residences': {
        'project': 'Marina Bay',
        'captions': [
            'Zona e pishinës dhe plazhit',
            'Perëndimi i diellit nga ndërtesa drejt detit',
            'Ballkonet me pamje nga gjiri i Durrësit',
        ],
    },
}


class Command(BaseCommand):
    help = 'Import gallery photos from media_import/ into each project, with captions.'

    def handle(self, *args, **options):
        media_import_dir = Path('media_import')
        if not media_import_dir.exists():
            self.stdout.write(self.style.ERROR(
                'media_import/ folder not found. Run this from the folder that '
                'contains manage.py.'
            ))
            return

        imported = 0
        skipped = 0

        for folder_name, info in GALLERY.items():
            project_name = info['project']
            captions = info['captions']
            folder_path = media_import_dir / folder_name

            if not folder_path.exists():
                self.stdout.write(self.style.WARNING(
                    f'Folder not found, skipping: {folder_name}'
                ))
                continue

            try:
                project = Project.objects.get(name=project_name)
            except Project.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'Project "{project_name}" not in database, skipping folder {folder_name}'
                ))
                continue

            # All images in the folder, any extension, sorted by filename.
            image_files = sorted(
                p for p in folder_path.iterdir()
                if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}
            )
            if not image_files:
                self.stdout.write(self.style.WARNING(
                    f'No images in {folder_name}'
                ))
                continue

            for idx, image_path in enumerate(image_files):
                caption = captions[idx] if idx < len(captions) else ''
                # Stable target filename used both to save and to detect duplicates.
                safe_name = project_name.replace(' ', '_')
                target_filename = f'{safe_name}_{idx + 1}{image_path.suffix.lower()}'

                already = ProjectImage.objects.filter(
                    project=project,
                    image=f'project_gallery/{target_filename}',
                ).exists()
                if already:
                    self.stdout.write(self.style.WARNING(
                        f'  ~ skip (exists): {project_name} / {image_path.name}'
                    ))
                    skipped += 1
                    continue

                with open(image_path, 'rb') as fh:
                    content = ContentFile(fh.read())

                proj_image = ProjectImage(project=project, caption=caption)
                proj_image.image.save(target_filename, content, save=True)

                self.stdout.write(self.style.SUCCESS(
                    f'  + {project_name} / {image_path.name}  ->  "{caption}"'
                ))
                imported += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {imported} imported, {skipped} skipped. '
            f'Total gallery images now: {ProjectImage.objects.count()}.'
        ))
