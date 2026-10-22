from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Count, IntegerField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.template.response import TemplateResponse
# Register your models here.
from cart.models import Item
from .models import Movie, Review, Rating, TopReviewer, MovieLeaders
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


class MovieLeadersAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        purchases = (
            Item.objects
            .filter(movie_id=OuterRef('pk'))
            .order_by()
            .values('movie_id')
            .annotate(total=Sum('quantity'))
            .values('total')[:1]
        )
        reviews = (
            Review.objects
            .filter(movie_id=OuterRef('pk'))
            .order_by()
            .values('movie_id')
            .annotate(total=Count('id'))
            .values('total')[:1]
        )
        movies = list(
            Movie.objects
            .annotate(
                purchase_count=Coalesce(
                    Subquery(purchases, output_field=IntegerField()), Value(0)),
                review_count=Coalesce(
                    Subquery(reviews, output_field=IntegerField()), Value(0)),
            )
            .order_by('name', 'pk')
        )
        purchase_count = max(
            (movie.purchase_count for movie in movies), default=0)
        review_count = max(
            (movie.review_count for movie in movies), default=0)
        most_purchased_movies = [
            movie for movie in movies
            if purchase_count > 0 and movie.purchase_count == purchase_count
        ]
        most_reviewed_movies = [
            movie for movie in movies
            if review_count > 0 and movie.review_count == review_count
        ]

        context = {
            **self.admin_site.each_context(request),
            'title': 'Movie Engagement Leaders',
            'opts': self.model._meta,
            'most_purchased_movies': most_purchased_movies,
            'purchase_count': purchase_count,
            'most_reviewed_movies': most_reviewed_movies,
            'review_count': review_count,
        }
        return TemplateResponse(request,
            'admin/movies/movieleaders/movie_leaders.html', context)


admin.site.register(MovieLeaders, MovieLeadersAdmin)
