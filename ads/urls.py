from django.urls import path
from .views import (
    AdListView, AdCreateView, AdDetailView, AdUpdateView, AdDeleteView,
    ProposalCreateView, ProposalListView, ProposalUpdateView, generate_ads
)

urlpatterns = [
    path('', AdListView.as_view(), name='ad_list'),
    path('new/', AdCreateView.as_view(), name='ad_create'),
    path('<int:pk>/', AdDetailView.as_view(), name='ad_detail'),
    path('<int:pk>/edit/', AdUpdateView.as_view(), name='ad_edit'),
    path('<int:pk>/delete/', AdDeleteView.as_view(), name='ad_delete'),

    path('<int:ad_receiver_pk>/propose/', ProposalCreateView.as_view(), name='send_proposal'),
    path('proposals/', ProposalListView.as_view(), name='manage_proposals'),
    path('proposals/<int:pk>/update/', ProposalUpdateView.as_view(), name='update_proposal_status'),
    path('generate/', generate_ads, name='generate_ads')
]
