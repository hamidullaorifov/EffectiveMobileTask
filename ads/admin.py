from django.contrib import admin
from .models import ExchangeProposal, Ad


class AdAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'description', 'image_url', 'category', 'condition', 'created_at']


class ProposalAdmin(admin.ModelAdmin):
    list_display = ['id', 'ad_sender', 'ad_receiver', 'status', 'created_at']


admin.site.register(Ad, AdAdmin)
admin.site.register(ExchangeProposal, ProposalAdmin)
