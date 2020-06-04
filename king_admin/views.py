from django.shortcuts import render, redirect
import importlib
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from king_admin.utils import  table_filter, table_sort, table_search
# Create your views here.
from king_admin import king_admin
from king_admin.forms import create_model_form
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    #print(king_admin.enabled_admins['crm']['customerfollowup'].model )
    #返回只显示app名和表名的页面，并返回给前端包含有app名，表名和admin要显示，过滤等的数据
    return render(request, "king_admin/table_index.html",{'table_list':king_admin.enabled_admins})

@login_required
def display_table_objs(request, app_name, table_name):
    #admin_class为admin注册前要加的一些功能们
    admin_class = king_admin.enabled_admins[app_name][table_name]

    if request.method == "POST":#action来了
        print(request.POST)
        selected_ids = request.POST.get("selected_ids")
        action = request.POST.get("action")
        if selected_ids:
            selected_objs = admin_class.model.objects.filter(id__in = selected_ids.split(','))
        else:
            raise KeyError("No object selected")

        if hasattr(admin_class, action):
            action_func = getattr(admin_class, action)
            request._admin_action = action
            return action_func(admin_class, request, selected_objs)

    #object_list为过滤后的数据对象，filter_conditions为过滤的条件
    object_list, filter_condtions = table_filter(request, admin_class)

    object_list = table_search(request, admin_class, object_list)

    #p排序后的object_list,orderby_key是排完序后加或者去掉“-”
    object_list, orderby_key = table_sort(request, admin_class, object_list)
    paginator = Paginator(object_list, admin_class.list_per_page)  # Show 25 contacts per page

    page = request.GET.get('page')
    try:
        query_sets = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        query_sets = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        query_sets = paginator.page(paginator.num_pages)

    return render(request, "king_admin/table_objs.html", \
                  {"admin_class": admin_class,
                   "filter_condtions": filter_condtions,
                   "query_sets": query_sets,
                  "orderby_key": orderby_key,
                   "previous_orderby": request.GET.get("o") or '',
                   "search_text": request.GET.get("_q", ''),})

@login_required
def table_obj_change(request, app_name, table_name, obj_id):
    admin_class = king_admin.enabled_admins[app_name][table_name]
    _model_form_class = create_model_form(request, admin_class)

    obj = admin_class.model.objects.get(id=obj_id)

    if request.method == "POST":
        '''加了instance=obj就是更新，不加的话就是创建表'''
        model_form_obj = _model_form_class(request.POST, instance=obj)

        if model_form_obj.is_valid():
            #print("----model", model_form_obj.cleaned_data)
            model_form_obj.save()
    else:
        '''instance传入一行table对象，就会显示出这一行的数据在modelform上'''
        model_form_obj = _model_form_class(instance=obj)
    return render(request, "king_admin/table_obj_change.html",{"model_form_obj": model_form_obj,
                                                               "admin_class": admin_class,
                                                               "app_name":app_name,
                                                               "table_name": table_name})

@login_required
def table_obj_add(request, app_name, table_name):
    admin_class = king_admin.enabled_admins[app_name][table_name]
    admin_class.is_add_form = True
    _model_form_class = create_model_form(request, admin_class)

    if request.method == "POST":
        '''加了instance=obj就是更新，不加的话就是创建表'''
        model_form_obj = _model_form_class(request.POST)
        if model_form_obj.is_valid():
            model_form_obj.save()
            return redirect(request.path.replace("/add", ""))
    else:
        '''instance传入一行table对象，就会显示出这一行的数据在modelform上'''
        model_form_obj = _model_form_class()
    return render(request, "king_admin/table_obj_add.html", {"model_form_obj": model_form_obj,
                                                  "admin_class": admin_class})

@login_required
def table_obj_delete(request,app_name, table_name, obj_id):
    admin_class = king_admin.enabled_admins[app_name][table_name]
    obj = admin_class.model.objects.get(id=obj_id)

    if not admin_class.readonly_table:
        errors = {"readonly_table": "table is readonly, obj [%s] cannot be deleted" % obj}
    else:
        errors = {}
    if request.method == "POST":
        if not admin_class.readonly_table:
            obj.delete()

        return redirect("/king_admin//%s/%s" %(app_name, table_name))
    return render(request, "king_admin/table_obj_delete.html",{"admin_class": admin_class,
                                                               "obj": obj,
                                                               "app_name":app_name,
                                                               "table_name": table_name,
                                                               "errors": errors
                                                               })

@login_required
def password_rest(request, app_name, table_name, obj_id):
    admin_class = king_admin.enabled_admins[app_name][table_name]
    _model_form_class = create_model_form(request, admin_class)

    obj = admin_class.model.objects.get(id=obj_id)
    errors = {}
    if request.method == "POST":
        _password1 = request.POST.get("password1")
        _password2 = request.POST.get("password2")

        if _password1 == _password2:
            if len(_password2) > 5:
                obj.set_password(_password1)
                obj.save()
            else:
                errors["password_too_short"] = "must not less than 6 letters"
            return redirect(request.path.rstrip("password/"))  # 回到change页面
        else:
            errors["invalia_password"] = "password are not the same"

    return render(request, 'king_admin/password_rest.html', {"obj": obj,
                                                             "errors": errors})