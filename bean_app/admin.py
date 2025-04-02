from django.contrib import admin
from .models import User,Size,Color,Material,Tag,BeanBag,BeanBagVariant

# Register your models here.

admin.site.register(User)
admin.site.register(Size)
admin.site.register(Color)
admin.site.register(Material)
admin.site.register(Tag)
admin.site.register(BeanBag)
admin.site.register(BeanBagVariant)


