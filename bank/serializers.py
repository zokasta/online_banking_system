from rest_framework import serializers
from bank.models import User, Account, Transaction 

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','name', 'username', 'email', 'phone', 'password', 'pan_card', 'aadhar_card', 'dob', 'type','mpin','is_ban']
        extra_kwargs = {'password': {'write_only': True},'mpin': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create(
            name=validated_data['name'],
            username=validated_data['username'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            pan_card=validated_data['pan_card'],
            aadhar_card=validated_data['aadhar_card'],
            dob=validated_data['dob'],
            type=validated_data['type'],
            mpin=validated_data['mpin']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = "__all__"
        read_only_fields = ['account_number', 'created_at', 'updated_at']

class TransactionSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    sender_name = serializers.SerializerMethodField()
    receiver_name = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['sender', 'receiver', 'amount', 'created_at', 'updated_at', 'date', 'status', 'sender_name', 'receiver_name','id']
        read_only_fields = ['created_at', 'updated_at']

    def get_date(self, obj):
        return obj.created_at.strftime('%d %b %Y')

    def get_status(self, obj):
        return 'Credit' if obj.type == obj.TransactionType.CREDIT_CARD else 'Debit'

    def get_sender_name(self, obj):
        return obj.sender.user.name

    def get_receiver_name(self, obj):
        return obj.receiver.user.name
