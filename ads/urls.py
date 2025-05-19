from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    AdListView, AdCreateView, AdDetailView, AdUpdateView, AdDeleteView,
    ProposalCreateView, ProposalListView, ProposalUpdateView, generate_ads
)
from .api_views import (
    AdListCreateAPIView, AdRetrieveUpdateDestroyAPIView,
    ExchangeProposalListCreateAPIView, ExchangeProposalRetrieveUpdateAPIView)

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

schema_view = get_schema_view(
   openapi.Info(
      title="Barter Platform API",
      default_version='v1',
      description="API documentation for Barter Platform",
   ),
   public=True,
)

api_urlpatterns = [
    path('api/ads/', AdListCreateAPIView.as_view(), name='api_ad_list'),
    path('api/ads/<int:pk>/', AdRetrieveUpdateDestroyAPIView.as_view(), name='api_ad_detail'),
    path('api/proposals/', ExchangeProposalListCreateAPIView.as_view(), name='api_proposal_list'),
    path('api/proposals/<int:pk>/', ExchangeProposalRetrieveUpdateAPIView.as_view(), name='api_proposal_detail'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
]

urlpatterns += api_urlpatterns
