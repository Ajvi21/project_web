"""
Models for the Nova Build app.

Follows the patterns taught in Lesson 03 (Models and Migrations):
- ForeignKey to User with related_name for reverse lookup.
- __str__ for admin readability.
- get_absolute_url to drive redirect-after-create/update.
- UniqueConstraint and CheckConstraint on reviews.
- ImageField for project cover and gallery (requires Pillow).

Domain mapping vs. the lessons project:
  Movie         -> Project       (a construction project Nova Build develops)
  MovieImage    -> ProjectImage  (gallery image of a project)
  MovieReview   -> ProjectReview (1..5 star rating, one per user per project)
  MovieComment  -> ProjectComment
  Post          -> NewsPost      (company news / blog entry)
  Comment       -> NewsComment

Nova-specific (carried over from the original site):
  ContactRequest   -> stores submissions from the contact form
  ChatbotFaq       -> question/keyword/answer pairs that drive the chatbot
  ChatbotMessage   -> log of every chatbot exchange
"""

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse


# -----------------------------------------------------------------------------
# News (blog-style) section -- mirrors Post/Comment from the lessons
# -----------------------------------------------------------------------------

class NewsPost(models.Model):
    """A company news article written by a staff member or any logged-in user."""

    title = models.CharField(max_length=120)
    content = models.TextField(blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    date_posted = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_posted']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news-detail', kwargs={'pk': self.pk})


class NewsComment(models.Model):
    """Reader comment on a NewsPost (Lesson 03 reverse relation pattern)."""

    post = models.ForeignKey(
        NewsPost,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    date_commented = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_commented']

    def __str__(self):
        return f'{self.post.title} - {self.author.username}'


# -----------------------------------------------------------------------------
# Project section -- mirrors Movie / MovieImage / MovieReview / MovieComment
# -----------------------------------------------------------------------------

class Project(models.Model):
    """A construction project in the Nova Build portfolio."""

    STATUS_CHOICES = [
        ('koncept', 'Koncept'),
        ('ne_zhvillim', 'Në zhvillim'),
        ('ne_ndertim', 'Në ndërtim'),
        ('perfunduar', 'Përfunduar'),
    ]

    CATEGORY_CHOICES = [
        ('rezidenciale', 'Rezidenciale'),
        ('biznes', 'Biznes'),
        ('mixed_use', 'Biznes + Rezidencë'),
        ('multifunksional', 'Multifunksional'),
        ('apartamente', 'Apartamente'),
    ]

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField()
    location = models.CharField(max_length=120)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES)
    year = models.PositiveSmallIntegerField(default=2026)
    floor_area_m2 = models.PositiveIntegerField(
        help_text='Sipërfaqja totale e ndërtimit në metra katrorë.',
        default=0,
    )
    cover = models.ImageField(upload_to='project_covers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_status_display()})'

    def get_absolute_url(self):
        return reverse('project-detail', kwargs={'pk': self.pk})


class ProjectImage(models.Model):
    """Gallery image for a project (Lesson 03 image upload pattern)."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='gallery_images',
    )
    image = models.ImageField(upload_to='project_gallery/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'Gallery image for {self.project.name}'


class ProjectReview(models.Model):
    """One 1..5 star review per user per project.

    Uses UniqueConstraint + CheckConstraint exactly as MovieReview does in
    Lesson 03.
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_reviews',
    )
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'user'],
                name='unique_project_review_per_user',
            ),
            models.CheckConstraint(
                check=Q(stars__gte=1) & Q(stars__lte=5),
                name='project_review_stars_between_1_5',
            ),
        ]

    def __str__(self):
        return f'{self.project.name} - {self.user.username}: {self.stars}/5'


class ProjectComment(models.Model):
    """Discussion comment a logged-in user leaves on a project."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='project_comments',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_comments',
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment on {self.project.name} by {self.user.username}'


# -----------------------------------------------------------------------------
# Contact form -- carries over the contact_requests table from the original
# project, but built the Django way (a Model with a ModelForm in forms.py).
# -----------------------------------------------------------------------------

class ContactRequest(models.Model):
    """A message submitted through the contact page form."""

    name = models.CharField(max_length=80)
    surname = models.CharField(max_length=80, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    subject = models.CharField(max_length=160, blank=True)
    message = models.TextField()
    is_handled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} <{self.email}> - {self.subject or "(no subject)"}'


# -----------------------------------------------------------------------------
# Chatbot -- carries over the chatbot_faqs and chatbot_messages tables
# from the original project.
# -----------------------------------------------------------------------------

class ChatbotFaq(models.Model):
    """A question/answer pair the Nova chatbot can match against."""

    question = models.CharField(max_length=200, unique=True)
    keywords = models.CharField(
        max_length=255,
        help_text='Fjalët kyçe të ndara me presje, p.sh. "projekt, ndertim, rezidenca".',
    )
    answer = models.TextField()
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', 'id']

    def __str__(self):
        return self.question


class ChatbotMessage(models.Model):
    """A single chatbot exchange (user message + bot response)."""

    user_message = models.CharField(max_length=500)
    bot_response = models.TextField()
    matched_faq = models.ForeignKey(
        ChatbotFaq,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.created_at:%Y-%m-%d %H:%M} - {self.user_message[:40]}'
