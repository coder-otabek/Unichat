from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User

class UserSerializer(serializers.ModelSerializer):
    is_admin = serializers.SerializerMethodField()
    class Meta:
        model  = User
        fields = ['id','email','full_name','is_admin','is_active','date_joined']
    def get_is_admin(self, obj):
        return obj.is_staff or obj.is_superuser

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model  = User
        fields = ['email','full_name','password']
    def validate_email(self, v):
        v = v.lower()
        if User.objects.filter(email=v).exists():
            raise serializers.ValidationError("Bu email allaqachon ro'yxatdan o'tgan")
        return v
    def create(self, data):
        return User.objects.create_user(
            email=data['email'], username=data['email'],
            full_name=data['full_name'], password=data['password']
        )

class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    def validate(self, data):
        user = authenticate(username=data['email'].lower(), password=data['password'])
        if not user:
            raise serializers.ValidationError("Email yoki parol noto'g'ri")
        if not user.is_active:
            raise serializers.ValidationError("Hisobingiz bloklangan")
        data['user'] = user
        return data

def tokens_for(user):
    r = RefreshToken.for_user(user)
    return {'access_token': str(r.access_token), 'refresh': str(r), 'user': UserSerializer(user).data}
