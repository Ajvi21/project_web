"""
"""

from django.contrib import admin

from .models import (
    ChatbotFaq,
    ChatbotMessage,
    ContactRequest,
    NewsComment,
    NewsPost,
    Project,
    ProjectComment,
    ProjectImage,
    ProjectReview,
)


admin.site.site_header = 'Nova Build Admin'
admin.site.site_title = 'Nova Build Admin'
admin.site.index_title = 'Menaxhimi i përmbajtjes'


admin.site.register(NewsPost)
admin.site.register(NewsComment)


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'category', 'status', 'year', 'created_at')
    list_filter = ('category', 'status', 'year')
    search_fields = ('name', 'location', 'description')
    inlines = [ProjectImageInline]


@admin.register(ProjectReview)
class ProjectReviewAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'stars', 'updated_at')
    list_filter = ('stars', 'updated_at')
    search_fields = ('project__name', 'user__username')


@admin.register(ProjectComment)
class ProjectCommentAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'created_at')
    search_fields = ('project__name', 'user__username', 'content')


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'surname', 'email', 'subject', 'is_handled', 'created_at')
    list_filter = ('is_handled', 'created_at')
    search_fields = ('name', 'surname', 'email', 'subject', 'message')
    list_editable = ('is_handled',)



@admin.register(ChatbotFaq)
class ChatbotFaqAdmin(admin.ModelAdmin):
    list_display = ('question', 'is_featured', 'created_at')
    list_filter = ('is_featured',)
    search_fields = ('question', 'keywords', 'answer')
    list_editable = ('is_featured',)


@admin.register(ChatbotMessage)
class ChatbotMessageAdmin(admin.ModelAdmin):
    list_display = ('user_message', 'matched_faq', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user_message', 'bot_response')
