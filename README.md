# Nova Build

A construction company website built with Django. The site has a public side
(landing page, project portfolio, news, contact form) and a private side
(login, admin panel, content management). It started as a static HTML/CSS/JS
site and was rebuilt as a Django application following the architecture from
the web programming course.

## What it does

Visitors can browse construction projects with photos, ratings and comments,
read company news, and send a contact request through a form. Registered
users can rate projects (1 to 5 stars, one rating per user per project),
leave comments, and publish news posts. Staff accounts have an extra layer
on top: they can add or edit projects, manage the photo gallery, and
moderate comments through the Django admin panel.

There is also a small chatbot widget in the corner of every page. It reads
its answers from a database table, so the staff can add new questions and
answers without touching any code. Every conversation is logged.

## Tech stack

- Python 3.10 or newer (tested on 3.12)
- Django 5.1
- SQLite (default Django database, no setup required)
- Pillow for image uploads
- Bootstrap 5.3 for the front-end
- A small amount of vanilla JavaScript for the chatbot widget

## Project layout

```
nova_build_django/
├── manage.py
├── requirements.txt
├── db.sqlite3                      created by `migrate`
├── media/                          uploaded covers and gallery images
├── static/
│   ├── styles/style.css
│   └── js/chatbot.js
├── nova_build_project/             project-level configuration
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── nova/                           the main app
    ├── apps.py
    ├── models.py
    ├── forms.py
    ├── views.py
    ├── urls.py
    ├── admin.py
    ├── tests.py
    ├── migrations/
    ├── management/commands/
    │   └── seed_data.py
    └── templates/
        ├── nova/                   public pages and CRUD templates
        └── user/                   login, register, password reset
```

## Domain model

The `nova` app defines nine models. The first four cover the project portfolio,
the next two handle news posts and their comments, one stores contact form
submissions, and the last two power the chatbot.

| Model            | What it stores                                                            |
| ---------------- | ------------------------------------------------------------------------- |
| `Project`        | Name, description, location, category, status, year, area, cover image    |
| `ProjectImage`   | Gallery photo attached to a project                                       |
| `ProjectReview`  | 1 to 5 star rating, unique per user per project                           |
| `ProjectComment` | User comment on a project                                                 |
| `NewsPost`       | A news article with title, body, author, timestamp                        |
| `NewsComment`    | Comment on a news post                                                    |
| `ContactRequest` | A submission from the contact form                                        |
| `ChatbotFaq`     | Question, keywords, answer that the chatbot can match against             |
| `ChatbotMessage` | Log of every user message and the bot response, plus the matched FAQ     |

Reverse relations are set up with `related_name` so templates can do things
like `project.reviews.all`, `project.gallery_images.all`, and
`post.comments.all` directly.

`ProjectReview` has two database constraints: a unique constraint on
`(project, user)` so nobody can rate the same project twice, and a check
constraint on `stars` so the value is always between 1 and 5.

## Routes

All routes are defined in `nova/urls.py` and given names so templates can
build URLs with `{% url %}` instead of hard-coding paths.

Public:

- `/` home page
- `/about/` about page
- `/contact/` contact form
- `/projects/` project list
- `/projects/<id>/` project detail with gallery, ratings, comments
- `/news/` news list
- `/news/<id>/` news article with comments

Login required:

- `/news/new/`, `/news/<id>/edit/`, `/news/<id>/delete/` author only
- `/projects/<id>/review/` add or update a rating
- `/projects/<id>/comment/` leave a comment
- `/news/<id>/comment/` comment on a news post

Staff only:

- `/projects/new/`, `/projects/<id>/edit/`, `/projects/<id>/delete/`
- `/projects/<id>/gallery/add/` upload a gallery photo
- `/project-images/<id>/delete/` remove a gallery photo

Authentication:

- `/login/`, `/logout/`, `/register/`
- `/password_reset/...` standard Django password reset flow

JSON endpoints used by the chatbot widget:

- `POST /api/chat/` returns the bot answer and logs the exchange
- `GET /api/faqs/` returns the featured FAQs (used for the quick buttons)
- `GET /api/projects/` returns all projects as JSON

## Permissions

The site distinguishes three kinds of visitors:

**Anonymous visitors** can browse everything public: the landing page, the
project portfolio, project detail pages with their galleries and existing
comments, the news section, and the about and contact pages. They can also
submit the contact form and chat with the bot.

**Logged-in users** can additionally rate projects, post comments on
projects and news articles, and write their own news posts. They can edit
or delete their own content but not anybody else's.

**Staff users** (anyone with `is_staff=True`, including superusers) can do
everything above, plus create, edit and delete projects, manage the photo
gallery, and moderate any comment or rating. They also have access to the
Django admin at `/admin/`.

In code, login restrictions use `LoginRequiredMixin` on class-based views
and `@login_required` on function-based views. Staff restrictions go
through a small `StaffRequiredMixin` built on `UserPassesTestMixin`.

## Setup

Clone or unzip the project, then from the project root:

```bash
python -m venv venv
source venv/bin/activate          # macOS or Linux
.\venv\Scripts\Activate.ps1       # Windows PowerShell

pip install -r requirements.txt

python manage.py makemigrations nova
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

The site is then at <http://localhost:8000/> and the admin at
<http://localhost:8000/admin/>. Sign into the admin with the superuser you
just created.

`seed_data` is a custom management command that populates the database with
six sample projects and a starter set of chatbot FAQs. It is safe to run
more than once: it uses `update_or_create` on the unique fields, so rows
are updated in place rather than duplicated.

If `pip install -r requirements.txt` fails on the Pillow line, see the
troubleshooting note at the bottom.

## Where the submitted contact forms go

When somebody fills in the form on `/contact/`, the data is validated by
`ContactRequestForm`, saved into the `ContactRequest` table, and a flash
message is shown to the visitor. To read the submissions:

1. Open <http://localhost:8000/admin/> and log in.
2. In the **Nova** section click **Contact requests**.
3. Each row shows the name, email, subject, date and an "Is handled"
   checkbox. Tick the checkbox once a request has been replied to. The
   list is searchable by name, email and subject.

If you prefer the command line, `python manage.py shell` works too:

```python
from nova.models import ContactRequest
for r in ContactRequest.objects.all():
    print(r.created_at, r.name, r.email, r.subject)
```

## How the chatbot works

The widget in `static/js/chatbot.js` posts the user's message to
`/api/chat/`. The view normalises the text (lowercases it, strips accents,
drops punctuation) and loops through `ChatbotFaq` entries looking for a
keyword match. If a match is found, the stored answer is returned and the
matched FAQ is recorded against the message in `ChatbotMessage`. If
nothing matches, a fallback reply is sent and the row is still logged with
`matched_faq=NULL`.

To add a new question and answer, open the admin, go to **Chatbot faqs**
and create a row. The `keywords` field is a comma-separated list, for
example `kontakt, telefon, email, takim, rezervo`. Tick **Is featured** if
you want the question to appear as a quick-reply button under the chat
input.

## Running the tests

```bash
python manage.py test nova
```

The current test suite is small. It covers the model constraints (the
unique review constraint, the star range), the access rules (anonymous can
view the project list but cannot reach the create form, a non-staff
logged-in user gets a 403 on the create form, a staff user can open it),
and a happy-path submission through the contact form. Add more tests as
the app grows.

## Notes and gotchas

The site is written in Albanian. The `LANGUAGE_CODE` in `settings.py` is
`sq` and the time zone is `Europe/Tirane`. If you change the language, the
template strings stay in Albanian because they are hard-coded, not run
through `gettext`.

`DEBUG` is `True` and `ALLOWED_HOSTS` is empty. That is fine for local
development but unsafe for a real server. Before deploying, generate a new
`SECRET_KEY`, set `DEBUG=False`, add your domain to `ALLOWED_HOSTS`, and
serve `media/` and `static/` through a real web server instead of Django's
dev server.

The password reset email is configured to print to the console, not to be
sent over SMTP. After requesting a reset, look in the terminal where
`runserver` is running for the reset link.

## Troubleshooting

**`pip install` fails on Pillow with "failed-wheel-build-for-install"**

This happens when pip cannot find a prebuilt Pillow wheel for your Python
version and tries to compile from source. The fix that almost always
works is to upgrade pip inside the venv first:

```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If that does not help, bump the Pillow line in `requirements.txt` to
`Pillow>=11.2.0` (newer wheels are available for Python 3.13+).

**`no such table: nova_project` when loading the page**

You skipped `migrate`. Run `python manage.py migrate` once and reload.

**The landing page has no projects on it**

You skipped `seed_data`. Run `python manage.py seed_data` and reload. You
can also add projects manually through the admin.

**Uploaded images do not show**

Check that `MEDIA_URL` and `MEDIA_ROOT` are set in `settings.py` and that
the project's `urls.py` includes the `static(MEDIA_URL, ...)` line at the
bottom. Both are in this repo already, but if you copy the project into a
different layout you have to re-add them.

## License

Academic project. Use freely.
