from django import forms
from django.contrib.auth.forms import UserCreationForm
from bean_app.models import Review

from bean_app.models import User,Order

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control '
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['phone'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("A user with this phone number already exists.")
        return phone
    
    def clean_email(self):
        email=self.cleaned_data.get("email")

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

        
    
class SignInForm(forms.Form):

    username = forms.CharField(max_length=100,
                               widget=forms.TextInput(attrs={'class': 'form-control mb-3 border-2px', 'placeholder': 'Enter your username'})
    )
    password = forms.CharField(max_length=200,
                               widget=forms.PasswordInput(attrs={'class': 'form-control mb-3', 'placeholder': 'Enter your password'})
    )


class OtpVerifyForm(forms.Form):

    otp=forms.CharField(max_length=10)


class OrderForm(forms.ModelForm):

    class Meta:

        model=Order

        fields=['address','phone','payment_method']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['address'].widget.attrs['class'] = 'form-control'
        self.fields['phone'].widget.attrs['class'] = 'form-control'
        self.fields['payment_method'].widget.attrs['class'] = 'form-select'

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(choices=[(i, i) for i in range(1, 6)]),  
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Write your review..."}),
        }