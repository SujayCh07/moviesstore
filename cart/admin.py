from django import forms
from django.contrib import admin
from django.template.response import TemplateResponse

# Register your models here.
from .models import Order, Item, TopBuyer, PurchaseRanking
from .utils import users_by_movies_bought
admin.site.register(Order)
admin.site.register(Item)

class TopBuyerAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def changelist_view(self, request, extra_context=None):
        buyers = users_by_movies_bought().filter(movies_bought__gt=0)
        top = buyers.first()
        context = {
            **self.admin_site.each_context(request),
            'title': 'Top Buyer',
            'opts': self.model._meta,
            'movies_bought': top.movies_bought if top else 0,
            'top_buyers': buyers.filter(movies_bought=top.movies_bought)
                if top else [],
        }
        return TemplateResponse(request,
            'admin/cart/topbuyer/top_buyer.html', context)
admin.site.register(TopBuyer, TopBuyerAdmin)

class RankingSizeForm(forms.Form):
    limit = forms.IntegerField(min_value=1, required=False,
        label='Users to display')

class PurchaseRankingAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def changelist_view(self, request, extra_context=None):
        # Queried on every request, so a refresh picks up new purchases.
        users = list(users_by_movies_bought())
        form = RankingSizeForm(request.GET)
        limit = None
        if form.is_valid():
            limit = form.cleaned_data['limit']
        # Standard competition ranking: tied users share a rank (1, 1, 3).
        rankings = []
        for position, user in enumerate(users, start=1):
            if rankings and user.movies_bought == rankings[-1]['movies_bought']:
                rank = rankings[-1]['rank']
            else:
                rank = position
            rankings.append({'rank': rank, 'username': user.username,
                'movies_bought': user.movies_bought})
        context = {
            **self.admin_site.each_context(request),
            'title': 'Purchase Rankings',
            'opts': self.model._meta,
            'form': form,
            'rankings': rankings[:limit],
            'total_users': len(rankings),
        }
        return TemplateResponse(request,
            'admin/cart/purchaseranking/purchase_rankings.html', context)
admin.site.register(PurchaseRanking, PurchaseRankingAdmin)
