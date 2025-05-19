from django.contrib import admin
from .models import ExchangeProposal, Ad


class AdAdmin(admin.ModelAdmin):
    list_display = ['id', 'user']


class ProposalAdmin(admin.ModelAdmin):
    list_display = ['id', 'ad_sender', 'ad_receiver']


admin.site.register(Ad, AdAdmin)
admin.site.register(ExchangeProposal, ProposalAdmin)
