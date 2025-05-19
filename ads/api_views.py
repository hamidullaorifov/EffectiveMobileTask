from rest_framework import generics, permissions, filters, serializers
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from .models import Ad, ExchangeProposal
from .serializers import (
    AdCreateUpdateSerializer, AdRetrieveSerializer, ExchangeProposalCreateSerializer,
    ExchangeProposalRetrieveSerializer, ExchangeProposalStatusSerializer)
from .permissions import IsOwnerOrReadOnly, IsProposalReceiver, IsProposalParticipant
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

ad_list_params = [
    openapi.Parameter(
        'category',
        openapi.IN_QUERY,
        description="Filter by category",
        type=openapi.TYPE_STRING,
        enum=[choice[0] for choice in Ad.CATEGORY_CHOICES]
    ),
    openapi.Parameter(
        'condition',
        openapi.IN_QUERY,
        description="Filter by condition",
        type=openapi.TYPE_STRING,
        enum=[choice[0] for choice in Ad.CONDITION_CHOICES]
    ),
    openapi.Parameter(
        'user',
        openapi.IN_QUERY,
        description="Filter by user ID",
        type=openapi.TYPE_INTEGER
    ),
    openapi.Parameter(
        'search',
        openapi.IN_QUERY,
        description="Search in title and description",
        type=openapi.TYPE_STRING
    ),
]


class AdListCreateAPIView(generics.ListCreateAPIView):
    queryset = Ad.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'condition', 'user']
    search_fields = ['title', 'description']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        return AdCreateUpdateSerializer if self.request.method == 'GET' else AdRetrieveSerializer

    @swagger_auto_schema(manual_parameters=ad_list_params)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ad.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        return AdRetrieveSerializer if self.request.method == 'GET' else AdCreateUpdateSerializer


class ExchangeProposalListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'ad_sender', 'ad_receiver']

    def get_queryset(self):
        user = self.request.user
        return ExchangeProposal.objects.filter(
            Q(ad_sender__user=user) |
            Q(ad_receiver__user=user)
        ).order_by('-created_at')

    def get_serializer_class(self):
        return ExchangeProposalRetrieveSerializer if self.request.method == 'GET' else ExchangeProposalCreateSerializer

    def perform_create(self, serializer):
        if self.request.user == serializer.validated_data['ad_receiver'].user:
            raise serializers.ValidationError("You cannot send a proposal to yourself.")
        if serializer.validated_data['ad_sender'].user != self.request.user:
            raise serializers.ValidationError("You cannot send a proposal for this ad.")

        serializer.save(ad_sender=serializer.validated_data['ad_sender'])


class ExchangeProposalRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = ExchangeProposal.objects.all()

    def get_serializer_class(self):
        return ExchangeProposalRetrieveSerializer if self.request.method == 'GET' else ExchangeProposalStatusSerializer

    def get_permissions(self):
        return [IsProposalParticipant()] if self.request.method == 'GET' else [IsProposalReceiver()]
