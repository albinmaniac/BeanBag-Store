from django.db import models
from django.contrib.auth.models import AbstractUser
from random import randint


# Create your models here.

class User(AbstractUser):
    phone = models.CharField(max_length=15, unique=False)

    is_verified = models.BooleanField(default=False)

    otp = models.CharField(max_length=6, blank=True, null=True)  

    def generate_otp(self):

        self.otp = str(randint(100000, 999999))  

        self.save()

    


class BaseModel(models.Model):

    created_date=models.DateTimeField(auto_now_add=True)

    updated_date=models.DateTimeField(auto_now=True)

    is_active=models.BooleanField(default=True)


class Size(BaseModel):

    name=models.CharField(max_length=70,unique=True)

    def __str__(self):
        
        return self.name


class Color(BaseModel):
    name = models.CharField(max_length=50, unique=True)

    hex_code = models.CharField(max_length=7, unique=True)

    def __str__(self):
        return self.name



class Material(BaseModel):
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name



class Tag(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class BeanBag(BaseModel):
    title = models.CharField(max_length=100)

    description = models.TextField()

    picture = models.ImageField(upload_to="beanbag_images", null=True, blank=True)

    CATEGORY_CHOICES = [
    ('CLASSIC', 'Classic Bean Bags'),
    ('SOCCER', 'Soccer Bean Bags'),
    ('CHAIRS', 'Chair Bean Bags'),
    ('Refillers','Refillers'),
    ('LUXURY', 'Luxury Bean Bags'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='CLASSIC')

    tag_objects = models.ManyToManyField(Tag)

    material_objects = models.ManyToManyField(Material)

    def __str__(self):
        return self.title


class BeanBagVariant(BaseModel):

    beanbag_object = models.ForeignKey(BeanBag, on_delete=models.CASCADE, related_name="variants")

    size_object = models.ForeignKey(Size, on_delete=models.CASCADE)

    color_object = models.ForeignKey(Color, on_delete=models.CASCADE)

    price = models.FloatField(help_text="Price in Rupees")



class Cart(BaseModel):

    beanbag_variant_object = models.ForeignKey(BeanBagVariant, on_delete=models.CASCADE)

    material_object = models.ForeignKey(Material, on_delete=models.CASCADE, null=True, blank=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField()

    is_order_placed = models.BooleanField(default=False)

    def item_total(self):
        return self.quantity * self.beanbag_variant_object.price



class Order(BaseModel):

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")

    address = models.TextField()

    phone = models.CharField(max_length=20)

    PAYMENT_OPTIONS = (
        ("COD", "Cash On Delivery"),
        ("ONLINE", "Online Payment")
    )
    payment_method = models.CharField(max_length=15, choices=PAYMENT_OPTIONS, default="COD")

    rzp_order_id = models.CharField(max_length=100, null=True)

    is_paid = models.BooleanField(default=False)

    def order_total(self):
        total = sum([oi.item_total() for oi in self.orderitems.all()])
        return total



class OrderItem(BaseModel):

    order_object = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="orderitems")

    beanbag_variant_object = models.ForeignKey(BeanBagVariant, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)
    price = models.FloatField()

    def item_total(self):
        return self.price * self.quantity
    

    
class Review(models.Model):

    beanbag = models.ForeignKey(BeanBag, on_delete=models.CASCADE, related_name="reviews")

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  

    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.beanbag.title} - {self.rating}⭐"
    
    class Meta:
        unique_together = ("beanbag", "user")  



class Wishlist(BaseModel):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    
    beanbag_variant = models.ForeignKey(
        BeanBagVariant, on_delete=models.CASCADE, related_name="wishlisted_by"
    )  

    class Meta:
        unique_together = ("user", "beanbag_variant")

    def __str__(self):
        return f"{self.user.username} - {self.beanbag_variant.beanbag_object.title} ({self.beanbag_variant.size_object.name}, {self.beanbag_variant.color_object.name})"