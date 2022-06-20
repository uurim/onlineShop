from shop.models import User
from django import forms
from django.shortcuts import render

class RegisterForm(forms.ModelForm):

    password = forms.CharField(label='Password', widget = forms.PasswordInput)
    password2 = forms.CharField(label='Repeat Password', widget=forms.PasswordInput)

    class Meta :
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'gender', 'birthdate', 'address']

        def clean_password2(self):
            cd=self.cleaned_data
            if cd['password']!=cd['password2']:
                raise forms.ValidationError
            return cd['password2']

