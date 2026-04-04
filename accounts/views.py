from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from .models import User
from .forms import UserRegistrationForm, UserProfileForm

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            messages.success(request, 'Đăng ký thành công!')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            messages.success(request, f'Chào mừng {user.get_full_name() or user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng')
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Đăng xuất thành công!')
    return redirect('home')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật thông tin thành công!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def order_history_view(request):
    orders = request.user.orders.all()
    return render(request, 'accounts/order_history.html', {'orders': orders})