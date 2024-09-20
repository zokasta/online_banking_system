from rest_framework import serializers
from bank.models import User, Account, Transaction , City, State, CreditCard, Report



class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name']

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'state']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','name', 'username', 'email', 'phone', 'password', 'pan_card', 'aadhar_card', 'dob', 'type','mpin','is_ban','city']
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
            mpin=validated_data['mpin'],
            city_id = validated_data.pop('city_id',None),
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


class CreditCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCard
        # Specify the fields you want to include in the serialized data
        fields = ['user','id','cvv', 'card_number', 'expiration_date', 'cvv', 'status', 'is_freeze', 'limit_use', 'created_at', 'updated_at']
        # Exclude sensitive information like CVV if needed
        # extra_kwargs = {
        #     'cvv': {'write_only': True}  # This ensures CVV is only writable, not readable in responses
        # }
    
    # Optionally, you can add custom validation if needed
    def validate_card_number(self, value):
        if len(value) != 16:
            raise serializers.ValidationError("Card number must be exactly 16 digits")
        return value

    def validate_expiration_date(self, value):
        # Optionally, you can add more logic to check if the date is in the future
        return value

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'user', 'message', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']  
