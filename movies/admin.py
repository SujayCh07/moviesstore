from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Count
from django.template.response import TemplateResponse
# Register your models here.
from .models import Movie, Review, Rating, TopReviewer
class MovieAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']
admin.site.register(Movie, MovieAdmin)
admin.site.register(Review)
admin.site.register(Rating)

class TopReviewerAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        movies_reviewed = Count('review')
        reviewers = (
            User.objects
            .annotate(comment_count=movies_reviewed)
            .filter(comment_count__gt=0)
            .order_by("-comment_count", "username")
        )

        top_reviewer = reviewers.first()
        top_count = top_reviewer.comment_count if top_reviewer else 0

        context = {
            **self.admin_site.each_context(request),
            "title": "Top Reviewer",
            "opts": self.model._meta,
            "comment_count": top_count,
            "top_reviewers": reviewers.filter(comment_count=top_count),
        }

        return TemplateResponse(
            request,
            "admin/movies/topreviewer/top_reviewer.html",
            context,
        )


admin.site.register(TopReviewer, TopReviewerAdmin)
