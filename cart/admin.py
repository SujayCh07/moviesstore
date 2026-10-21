from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Sum
from django.template.response import TemplateResponse

# Register your models here.
from .models import Order, Item, TopBuyer
admin.site.register(Order)
admin.site.register(Item)

class TopBuyerAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def changelist_view(self, request, extra_context=None):
        buyers = User.objects.annotate(
            movies_bought=Sum('order__item__quantity')
        ).filter(movies_bought__isnull=False).order_by('-movies_bought')
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
