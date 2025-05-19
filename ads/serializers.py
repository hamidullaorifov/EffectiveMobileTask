from rest_framework import serializers
from .models import Ad, ExchangeProposal
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class AdCreateUpdateSerializer(serializers.ModelSerializer):
    image_url = serializers.URLField(required=False, allow_null=True)
    category = serializers.ChoiceField(choices=Ad.CATEGORY_CHOICES)
    condition = serializers.ChoiceField(choices=Ad.CONDITION_CHOICES)

    class Meta:
        model = Ad
        fields = ['id', 'title', 'description', 'image_url', 'category', 'condition', 'created_at']
        read_only_fields = ['created_at']


class AdRetrieveSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Ad
        fields = ['id', 'user', 'title', 'description', 'image_url', 'category', 'condition', 'created_at']


class ExchangeProposalRetrieveSerializer(serializers.ModelSerializer):
    ad_sender = AdRetrieveSerializer(read_only=True)
    ad_receiver = AdRetrieveSerializer(read_only=True)
    ad_sender_id = serializers.PrimaryKeyRelatedField(
        queryset=Ad.objects.all(),
        source='ad_sender',
        write_only=True
    )
    ad_receiver_id = serializers.PrimaryKeyRelatedField(
        queryset=Ad.objects.all(),
        source='ad_receiver',
        write_only=True
    )

    class Meta:
        model = ExchangeProposal
        fields = ['id', 'ad_sender', 'ad_receiver', 'ad_sender_id', 'ad_receiver_id', 'comment', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']


class ExchangeProposalCreateSerializer(serializers.ModelSerializer):
    ad_sender_id = serializers.PrimaryKeyRelatedField(
        queryset=Ad.objects.all(),
        source='ad_sender',
        write_only=True
    )
    ad_receiver_id = serializers.PrimaryKeyRelatedField(
        queryset=Ad.objects.all(),
        source='ad_receiver',
        write_only=True
    )

    class Meta:
        model = ExchangeProposal
        fields = ['id', 'ad_sender_id', 'ad_receiver_id', 'comment', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']


class ExchangeProposalStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeProposal
        fields = ['status']
