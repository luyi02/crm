#_author: "luyi"
#date: 2020-05-30
from django.shortcuts import render,redirect
from django.contrib.auth import login, authenticate, logout
def acc_login(request):
    errors = {}
    if request.method == "POST":
        _email = request.POST.get("email")
        _password = request.POST.get("password")

        user = authenticate(username = _email, password = _password)
        if user:
            login(request, user)

            next_url = request.GET.get("next", "/")
            return redirect("/index")
        else:
            errors["errors"] = "Wrong username or password"
    return render(request, "login.html", {"errors": errors})

def acc_logout(request):

    logout(request)
    return redirect("/account/login/")

def index(request):
    return render(request, "index.html")