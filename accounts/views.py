from django.shortcuts import render
from .forms import RegisterForm
from shop.models import User
from django.contrib.auth.decorators import login_required

@login_required
def userInfoList(request):
    userInfo = User.objects.get(id=request.user.id)
    return render(request, 'registration/userInfo_list.html', {'userInfo': userInfo})

def register(request):
    if request.method == 'POST':
        user_form = RegisterForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            return render(request, 'registration/register_done.html', {'new_user':new_user})
    else :
        user_form = RegisterForm()

    return render(request, 'registration/register.html', {'form':user_form})