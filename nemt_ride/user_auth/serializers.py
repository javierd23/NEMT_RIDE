from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserRoles


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRoles
        fields = ['id', 'role']


class SignUpSerializer(serializers.ModelSerializer):
    
    # I added this primary key to allow user to select the role, this could be change if 
    # we want to assign the role based on the endpoint or something else.
    role = serializers.PrimaryKeyRelatedField(queryset=UserRoles.objects.all(), required=False) 
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 
                  'password', 
                  'first_name', 
                  'last_name', 
                  'phone_number', 
                  'role'
        ]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            username=attrs['email'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('This account is inactive.')
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    role = UserRoleSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id_user', 'email', 'first_name', 'last_name',
            'phone_number', 'role', 'is_active', 'date_joined',
        ]
        read_only_fields = ['id_user', 'email', 'date_joined',
                            'is_active']
