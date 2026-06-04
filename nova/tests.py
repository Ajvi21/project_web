from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Project, ProjectReview


class ProjectModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('jeton', password='pwd12345')
        self.project = Project.objects.create(
            name='Test Tower',
            description='A test description.',
            location='Tiranë',
            category='rezidenciale',
            status='ne_zhvillim',
            year=2026,
            floor_area_m2=2500,
        )

    def test_str_includes_status_label(self):
        self.assertIn('Test Tower', str(self.project))

    def test_unique_review_per_user(self):
        ProjectReview.objects.create(project=self.project, user=self.user, stars=4)
        with self.assertRaises(Exception):
            # second review by same user on same project must fail.
            ProjectReview.objects.create(project=self.project, user=self.user, stars=5)


class ProjectAccessTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user('admin', password='pwd12345', is_staff=True)
        cls.regular = User.objects.create_user('alban', password='pwd12345')

    def test_anonymous_can_list_projects(self):
        response = self.client.get(reverse('project-list'))
        self.assertEqual(response.status_code, 200)

    def test_non_staff_cannot_create_project(self):
        self.client.login(username='alban', password='pwd12345')
        response = self.client.get(reverse('project-create'))
        # UserPassesTestMixin with raise_exception=True returns 403.
        self.assertEqual(response.status_code, 403)

    def test_staff_can_open_create_form(self):
        self.client.login(username='admin', password='pwd12345')
        response = self.client.get(reverse('project-create'))
        self.assertEqual(response.status_code, 200)


class ContactFormTests(TestCase):

    def test_contact_post_saves_request(self):
        response = self.client.post(reverse('contact'), {
            'name': 'Test',
            'surname': 'User',
            'email': 'test@example.com',
            'phone': '+355 69 000 0000',
            'subject': 'Interesim',
            'message': 'Po interesohem për një projekt rezidencial.',
        })
        # Redirect on success
        self.assertEqual(response.status_code, 302)
