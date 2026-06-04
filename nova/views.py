import json
import unicodedata

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count, Prefetch
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import (
    ContactRequestForm,
    NewsCommentForm,
    NewsPostForm,
    ProjectCommentForm,
    ProjectForm,
    ProjectImageForm,
    ProjectReviewForm,
    UserRegisterForm,
)
from .models import (
    ChatbotFaq,
    ChatbotMessage,
    NewsComment,
    NewsPost,
    Project,
    ProjectComment,
    ProjectImage,
    ProjectReview,
)
def home(request):
    """The Nova Build home page (Kreu).

    Pulls a few featured projects from the database so the landing page
    is data-driven instead of static HTML.
    """
    featured_projects = (
        Project.objects
        .annotate(rating_count=Count('reviews', distinct=True))
        .order_by('-created_at')[:3]
    )
    return render(request, 'nova/home.html', {'featured_projects': featured_projects})


def about(request):
    """The 'Rreth nesh' page."""
    return render(request, 'nova/about.html')


# =============================================================================
# News (mirrors PostListView / PostDetailView / PostCreateView / ... )
# =============================================================================

class NewsListView(ListView):
    model = NewsPost
    template_name = 'nova/news_list.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']


class NewsDetailView(DetailView):
    model = NewsPost
    template_name = 'nova/news_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = NewsCommentForm()
        return context


class NewsCreateView(LoginRequiredMixin, CreateView):
    model = NewsPost
    form_class = NewsPostForm
    template_name = 'nova/news_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Lajmi u publikua me sukses.')
        return super().form_valid(form)

    def get_success_url(self):
        if not hasattr(self, 'object') or not self.object.pk:
            return reverse('news-list')
        return reverse('news-detail', kwargs={'pk': self.object.pk})


class NewsUpdateView(LoginRequiredMixin, UpdateView):
    model = NewsPost
    form_class = NewsPostForm
    template_name = 'nova/news_form.html'

    def get_queryset(self):
        # Only the author can update their own news post.
        return super().get_queryset().filter(author=self.request.user)


class NewsDeleteView(LoginRequiredMixin, DeleteView):
    model = NewsPost
    template_name = 'nova/news_confirm_delete.html'

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)

    def get_success_url(self):
        messages.success(self.request, 'Lajmi u fshi me sukses.')
        return reverse('news-list')


@login_required
def add_news_comment(request, pk):
    post = get_object_or_404(NewsPost, pk=pk)
    if request.method == 'POST':
        form = NewsCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Komenti u shtua.')
        else:
            messages.error(request, 'Komenti nuk është i vlefshëm.')
    return redirect('news-detail', pk=post.pk)


@login_required
def delete_news_comment(request, pk):
    comment = get_object_or_404(NewsComment, pk=pk)
    post_pk = comment.post.pk
    if request.user == comment.author or request.user.is_staff:
        comment.delete()
        messages.success(request, 'Komenti u fshi.')
    else:
        messages.error(request, 'Nuk mund ta fshish këtë koment.')
    return redirect('news-detail', pk=post_pk)


# =============================================================================
# Projects (mirrors the Movie CRUD from Lesson 07)
# =============================================================================

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allows only staff users to access the view (Lesson 06)."""
    raise_exception = True

    def test_func(self):
        return self.request.user.is_staff


class ProjectListView(ListView):
    """Public listing of all Nova Build projects with rating aggregates."""

    model = Project
    template_name = 'nova/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return (
            Project.objects
            .annotate(
                avg_rating=Avg('reviews__stars'),
                rating_count=Count('reviews', distinct=True),
            )
            .order_by('-created_at')
        )


class ProjectDetailView(DetailView):
    """Public detail page with gallery, ratings, and comments (Lesson 07)."""

    model = Project
    template_name = 'nova/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        return (
            Project.objects
            .annotate(
                avg_rating=Avg('reviews__stars'),
                rating_count=Count('reviews', distinct=True),
            )
            .prefetch_related(
                'gallery_images',
                Prefetch(
                    'project_comments',
                    queryset=ProjectComment.objects.select_related('user').order_by('-created_at'),
                ),
                Prefetch(
                    'reviews',
                    queryset=ProjectReview.objects.select_related('user').order_by('-updated_at'),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        user_review = None
        if self.request.user.is_authenticated:
            user_review = project.reviews.filter(user=self.request.user).first()
        context['user_review'] = user_review
        context['review_form'] = ProjectReviewForm(instance=user_review)
        context['comment_form'] = ProjectCommentForm()
        context['image_form'] = ProjectImageForm() if self.request.user.is_staff else None
        return context


class ProjectCreateView(StaffRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'nova/project_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Projekti u krijua me sukses.')
        return response


class ProjectUpdateView(StaffRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'nova/project_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Projekti u përditësua me sukses.')
        return response


class ProjectDeleteView(StaffRequiredMixin, DeleteView):
    model = Project
    template_name = 'nova/project_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, 'Projekti u fshi me sukses.')
        return reverse('project-list')


@login_required
@require_POST
def add_or_update_project_review(request, pk):
    """Upsert behaviour: one review per (project, user) (Lesson 07)."""
    project = get_object_or_404(Project, pk=pk)
    existing = ProjectReview.objects.filter(project=project, user=request.user).first()
    form = ProjectReviewForm(request.POST, instance=existing)
    if form.is_valid():
        review = form.save(commit=False)
        review.project = project
        review.user = request.user
        review.save()
        if existing:
            messages.success(request, 'Vlerësimi yt u përditësua.')
        else:
            messages.success(request, 'Vlerësimi yt u shtua.')
    else:
        messages.error(request, 'Vlerësimi duhet të jetë midis 1 dhe 5.')
    return redirect('project-detail', pk=project.pk)


@login_required
@require_POST
def delete_project_review(request, pk):
    review = get_object_or_404(ProjectReview, pk=pk)
    project_pk = review.project.pk
    if request.user != review.user and not request.user.is_staff:
        return HttpResponseForbidden('Nuk lejohesh ta fshish këtë vlerësim.')
    review.delete()
    messages.success(request, 'Vlerësimi u fshi me sukses.')
    return redirect('project-detail', pk=project_pk)


@login_required
@require_POST
def add_project_comment(request, pk):
    project = get_object_or_404(Project, pk=pk)
    form = ProjectCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.project = project
        comment.user = request.user
        comment.save()
        messages.success(request, 'Komenti u shtua.')
    else:
        messages.error(request, 'Komenti nuk është i vlefshëm.')
    return redirect('project-detail', pk=project.pk)


@login_required
@require_http_methods(['GET', 'POST'])
def edit_project_comment(request, pk):
    comment = get_object_or_404(ProjectComment, pk=pk)
    if request.user != comment.user and not request.user.is_staff:
        return HttpResponseForbidden('Nuk lejohesh ta editosh këtë koment.')
    if request.method == 'POST':
        form = ProjectCommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Komenti u përditësua.')
            return redirect('project-detail', pk=comment.project.pk)
    else:
        form = ProjectCommentForm(instance=comment)
    return render(
        request,
        'nova/project_comment_form.html',
        {'form': form, 'project': comment.project, 'comment': comment},
    )


@login_required
@require_POST
def delete_project_comment(request, pk):
    comment = get_object_or_404(ProjectComment, pk=pk)
    project_pk = comment.project.pk
    if request.user != comment.user and not request.user.is_staff:
        return HttpResponseForbidden('Nuk lejohesh ta fshish këtë koment.')
    comment.delete()
    messages.success(request, 'Komenti u fshi.')
    return redirect('project-detail', pk=project_pk)


@login_required
@require_POST
def add_project_image(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not request.user.is_staff:
        return HttpResponseForbidden('Vetëm stafi mund të menaxhojë galerinë.')
    form = ProjectImageForm(request.POST, request.FILES)
    if form.is_valid():
        image = form.save(commit=False)
        image.project = project
        image.save()
        messages.success(request, 'Imazhi u shtua në galeri.')
    else:
        messages.error(request, 'Imazhi i ngarkuar nuk është i vlefshëm.')
    return redirect('project-detail', pk=project.pk)


@login_required
@require_POST
def delete_project_image(request, pk):
    image = get_object_or_404(ProjectImage, pk=pk)
    project_pk = image.project.pk
    if not request.user.is_staff:
        return HttpResponseForbidden('Vetëm stafi mund të fshijë imazhet.')
    image.delete()
    messages.success(request, 'Imazhi u fshi nga galeria.')
    return redirect('project-detail', pk=project_pk)


# =============================================================================
# Authentication (mirrors the register view from Lesson 06)
# =============================================================================

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Llogaria u krijua për {username}! Tani mund të kyçesh.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'user/register.html', {'form': form})


# =============================================================================
# Contact form (Nova-specific, uses ContactRequest model + Django messages)
# =============================================================================

def contact(request):
    if request.method == 'POST':
        form = ContactRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Mesazhi u dërgua me sukses. Do të kontaktohesh sa më shpejt.',
            )
            return redirect('contact')
        messages.error(request, 'Ka gabime në formë. Ju lutemi rishikoni fushat.')
    else:
        form = ContactRequestForm()
    return render(request, 'nova/contact.html', {'form': form})


# =============================================================================
# Chatbot endpoint (carried over from the original Nova Build site,
# rewritten using the Django ORM and the ChatbotFaq / ChatbotMessage models).
# =============================================================================

def _normalize_text(text: str) -> str:
    """Lowercase + strip accents + drop non-alphanumeric -- same logic as the
    original server.py from the static project."""
    normalized = unicodedata.normalize('NFD', text.lower())
    without_accents = ''.join(
        ch for ch in normalized if unicodedata.category(ch) != 'Mn'
    )
    cleaned = ''.join(ch if ch.isalnum() else ' ' for ch in without_accents)
    return ' '.join(cleaned.split())


@csrf_exempt
@require_POST
def chatbot_api(request):
    """POST /api/chat -> JSON {response, matched}.

    csrf_exempt is used so the chatbot widget can post from any of the
    static pages without first injecting a CSRF token; this matches the
    behaviour of the original server.py.
    """
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        payload = {}

    message = (payload.get('message') or '').strip()
    if not message:
        return JsonResponse({
            'response': 'Shkruaj një pyetje për Nova Build.',
            'matched': False,
        })

    normalized = _normalize_text(message)
    matched_faq = None
    for faq in ChatbotFaq.objects.order_by('-is_featured', 'id'):
        keywords = [_normalize_text(kw) for kw in faq.keywords.split(',')]
        if any(kw and kw in normalized for kw in keywords):
            matched_faq = faq
            break

    if matched_faq:
        response_text = matched_faq.answer
    else:
        response_text = (
            'Më vjen keq, nuk e njoh këtë pyetje. Provo të pyesësh për '
            'projektet, kontaktin, funksionalitetet, teknologjitë ose '
            'responsive design.'
        )

    ChatbotMessage.objects.create(
        user_message=message[:500],
        bot_response=response_text,
        matched_faq=matched_faq,
    )

    return JsonResponse({
        'response': response_text,
        'matched': matched_faq is not None,
    })


def chatbot_faqs_api(request):
    """GET /api/faqs -> JSON list of featured FAQs (drives the quick buttons)."""
    faqs = ChatbotFaq.objects.filter(is_featured=True).order_by('id')
    data = [{'question': f.question, 'answer': f.answer} for f in faqs]
    return JsonResponse(data, safe=False)


def projects_api(request):
    """GET /api/projects -> JSON list of all projects (kept for parity with
    the original server.py)."""
    projects = Project.objects.order_by('id').values(
        'name', 'location', 'category', 'status', 'description',
    )
    return JsonResponse(list(projects), safe=False)
