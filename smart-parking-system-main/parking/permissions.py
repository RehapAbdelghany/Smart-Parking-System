from rest_framework import permissions
import os

class IsCameraNode(permissions.BasePermission):
    """
    صلاحية خاصة تسمح فقط للكاميرات بالوصول (عن طريق API Key في الـ Header)
    """
    def has_permission(self, request, view):
        secret_key = os.getenv('CAMERA_SECRET_KEY', 'my_ultra_secure_camera_token_2026')
        # التأكد من وجود الـ Header ومطابقته
        client_key = request.headers.get('X-camera-Key')
        return client_key == secret_key

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    تسمح للمستخدم برؤية حجوزاته فقط، وللأدمن برؤية كل شيء.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff