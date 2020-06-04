#__author:  Administrator
#date:  2017/1/5
#模拟出admin注册时的一些功能
from app1 import models
from django.shortcuts import render, redirect, HttpResponse
enabled_admins = {}

class BaseAdmin(object):
    list_display = []
    list_filters = []
    list_per_page = 2
    search_fields = []
    ordering = None
    filter_horizontal = []
    actions = ["delete_select_objs"]
    readonly_fields = []
    readonly_table = False
    modelform_exclude_fields = []

    def delete_select_objs(self, request, querysets):
        app_name = self.model._meta.app_label
        table_name = self.model._meta.model_name
        print("delete_select_objs", self, request, querysets[0]._meta.model_name)
        if self.readonly_table:
            errors = {"readonly_table": "table is readonly, cannot be deleted or modified!" }
        else:
            errors = {}
        if request.POST.get("delete_confirm") == "yes":
            if not self.readonly_table:
                querysets.delete()
            return redirect("/king_admin//%s/%s" % (app_name, table_name))
        selected_ids = ','.join([str(i.id) for i in querysets])
        return render(request, "king_admin/table_obj_delete.html", {"admin_class": self,
                                                                    "obj": querysets,
                                                                    "app_name": app_name,
                                                                    "table_name": table_name,
                                                                    "selected_ids": selected_ids,
                                                                    "action": request._admin_action,
                                                                    "errors": errors})

    def default_form_validation(self):
        '''用户可以在此进行自定义的表单验证，相当于django form 的clean方法'''
        pass

class CustomerAdmin(BaseAdmin):
    list_display = ['id','qq','name','source','consult_course','date','status', 'enroll']
    list_filters = ['source','consult_course','status', 'date']
    search_fields = ('qq', 'name', 'consult_course__name')
    ordering = "id"
    filter_horizontal = ('tags',)
    actions = ["delete_select_objs", "test"]
    #readonly_fields = ["qq", "tags"]
    #readonly_table = True

    def test(self, request, queryset):
        print("in test")
    test.display_name = "测试动作"

    def enroll(self):
        if self.instance.status == 0:
            link_name = "报名新课程"
        else:
            link_name = "报名"
        return '''<a href = "/app1/customer/%s/enrollment/">%s</a>''' %(self.instance.id, link_name)
    enroll.display_name = "报名链接"

    def default_form_validation(self):
        print("----customer validation", self)

    def clean_name(self):
        print("name clean validation", self.cleaned_data["name"])
        if not self.cleaned_data["name"]:
            self.add_error("name", "cannot be null")
    #model = models.Customer
class UserProfileAdmin(BaseAdmin):
    list_display = ["email", "name"]
    readonly_fields = ["password"]
    filter_horizontal = ('groups', 'user_permissions')
    modelform_exclude_fields = ["last_login",]

class CustomerFollowUpAdmin(BaseAdmin):
    list_display = ('customer','consultant','date')
    list_filters = ['customer', 'date']


''''''
class CourseRecordAdmin(BaseAdmin):
    list_display = [ "from_class","day_num", "teacher", "homework_content"]

    def initialize_studyrecords(self, request, queryset):
        if len(queryset) > 1:
            return HttpResponse("只能选择一个班级")
        else:
            new_obj_list = []
            for enroll_obj in queryset[0].from_class.enrollment_set.all():
                '''非事务型的创建数据'''
                # models.StudyRecord.objects.get_or_create(
                #     student=enroll_obj,
                #     course_record = queryset[0],
                #     attendance=0,
                #     score=0,
                # )非批量创建

                '''事务型的创建数据'''

                new_obj_list.append(models.StudyRecord(
                    student=enroll_obj,
                    course_record = queryset[0],
                    attendance=0,
                    score=0,
                ))
            try:
                models.StudyRecord.objects.bulk_create(new_obj_list) #批量创建
            except Exception as e:
                return HttpResponse("批量初始化学习记录失败，请检查该节课是否有对应的学习记录")
            return redirect(("/king_admin//app1/studyrecord/"))#?course_record%s
    initialize_studyrecords.display_name = "初始化本节课的学习记录"
    actions = ["initialize_studyrecords",]

class StudyRecordAdmin(BaseAdmin):
    list_display = ["student", "course_record", "attendance", "score"]
    list_filters = ["course_record"]
    list_editable = ["attendance","score"]
''''''

def register(model_class,admin_class=None):
    if model_class._meta.app_label not in enabled_admins:
        enabled_admins[model_class._meta.app_label] = {} #enabled_admins['crm'] = {}
    #admin_obj = admin_class()
    admin_class.model = model_class #绑定model 对象和admin 类
    enabled_admins[model_class._meta.app_label][model_class._meta.model_name] = admin_class
    #enabled_admins['crm']['customerfollowup'] = CustomerFollowUpAdmin


register(models.Customer,CustomerAdmin)
register(models.CustomerFollowUp,CustomerFollowUpAdmin)
register(models.UserProfile, UserProfileAdmin)
register(models.CourseRecord, CourseRecordAdmin)
register(models.StudyRecord, StudyRecordAdmin)



