from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from bean_app.models import User
from django.db.models import Q

class EmailBackEnd(BaseBackend):
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user_object = User.objects.get(Q(email=username) | Q(phone=username))
        except User.DoesNotExist:
            return None  
        except User.MultipleObjectsReturned:
            return None  

        
        if user_object and user_object.check_password(password):
            return user_object
        return None  

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None  