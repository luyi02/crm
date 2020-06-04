from django.shortcuts import render, redirect, HttpResponse
from app1.forms import EnrollmentForm, CustomerForm, PaymentForm
from app1 import models
from django.db import IntegrityError
import string, random, os
from django.core.cache import cache
from crm import settings
# Create your views here.
def index(req):
    return render(req, "index.html")
def customer_list(req):
    return render(req, "sales/customer.html")

def enrollment(request, customer_id):
    customer_obj = models.Customer.objects.get(id=customer_id)
    msgs = {}
    msg = '''请将该链接发送给客户填写:
                127.0.0.1:8006/app1/customer/registration/{enroll_obj_id}/{random_str}'''
    random_str = "".join(random.sample(string.ascii_lowercase + string.digits, 8))

    if request.method == "POST":
        enroll_form = EnrollmentForm(request.POST)
        if enroll_form.is_valid():
            try:
                enroll_form.cleaned_data["customer"] = customer_obj
                enroll_obj = models.Enrollment(**enroll_form.cleaned_data)
                enroll_obj.save()
                print("eroll_obj", enroll_obj)
                cache.set(enroll_obj.id, random_str, 3000)
                msgs["msg"] = msg.format(enroll_obj_id=enroll_obj.id, random_str=random_str)
            except IntegrityError as e:
                enroll_obj = models.Enrollment.objects.get(customer_id=customer_obj.id,
                                         enrolled_class_id=enroll_form.cleaned_data["enrolled_class"].id)

                if enroll_obj.contract_agreed:
                    return redirect("/app1/contract_review/%s" %enroll_obj.id)

                enroll_form.add_error("__all__", "该用户的此条信息已存在，不能重复创建")

                msgs["msg"] = msg.format(enroll_obj_id=enroll_obj.id, random_str=random_str)
    else:
        enroll_form = EnrollmentForm()

    return render(request, "sales/enrollment.html", {"enroll_form":enroll_form,
                                                     "customer_obj": customer_obj,
                                                     "msgs": msgs})

def stu_registration(request, enroll_id, random_str):
    if True:#cache.get(enroll_id) == random_str:
        enroll_obj = models.Enrollment.objects.get(id=enroll_id)
        status = 1
        if request.method == "POST":

            if request.is_ajax():
                #print("ajax post", request.FILES)
                enroll_data_dir = "%s/%s"%(settings.ENROLLED_DATA, enroll_id)
                if not os.path.exists(enroll_data_dir):
                    os.makedirs(enroll_data_dir, exist_ok=True)
                for k, file_obj in request.FILES.items():
                    with open('%s/%s'%(enroll_data_dir, file_obj.name), "wb") as f:
                        for chunk in file_obj.chunks():
                            f.write(chunk)
                return HttpResponse("sucess")

            customer_form = CustomerForm(request.POST,instance=enroll_obj.customer)
            if customer_form.is_valid():
                customer_form.save()
                enroll_obj.contract_agreed = True
                enroll_obj.save()
                return render(request, "sales/stu_registration.html", {"status":1})
        else:
            if enroll_obj.contract_agreed:
                status = 1
            else:
                status = 0
            customer_form = CustomerForm(instance=enroll_obj.customer)

        return render(request, "sales/stu_registration.html",
                          {"customer_form": customer_form,
                           "enroll_obj": enroll_obj,
                           "status": status})
    # else:
    #     return HttpResponse("链接已失效")

def contract_review(request, enroll_id):
    enroll_obj = models.Enrollment.objects.get(id=enroll_id)
    enroll_form = EnrollmentForm(instance=enroll_obj)
    customer_form = CustomerForm(instance=enroll_obj.customer)
    return render(request, "sales/contract_review.html", {
                                                 "enroll_obj": enroll_obj,
                                                 "customer_form": customer_form,
                                                 "enroll_form": enroll_form})

def enrollment_rejection(request, enroll_id):
    enroll_obj = models.Enrollment.objects.get(id=enroll_id)
    enroll_obj.contract_agreed = False
    enroll_obj.save()
    text = "/app1/customer/%s/enrollment/" %enroll_obj.customer.id
    print("ok")
    return redirect("/app1/customer/%s/enrollment" %enroll_obj.customer.id)

def payment(request, enroll_id):
    enroll_obj = models.Enrollment.objects.get(id=enroll_id)
    errors = []
    if request.method == "POST":
        payment_amount = request.POST.get("amount")
        if payment_amount:
            payment_amount = int(payment_amount)
            if payment_amount < 500:
                errors.append("缴费金额不得低于500元")
            else:
                payment_obj = models.Payment.objects.create(
                    customer=enroll_obj.customer,
                    course=enroll_obj.enrolled_class.course,
                    amount=payment_amount,
                    consultant=enroll_obj.consultant
                )

                enroll_obj.contract_approved = True
                enroll_obj.save()

                enroll_obj.customer.status = 0
                enroll_obj.customer.save()
                return redirect("/king_admin//app1/customer")
        else:
            errors.append("缴费金额不得低于500元")


    return render(request, "sales/payment.html",{"enroll_obj": enroll_obj,
                                                 "errors": errors})