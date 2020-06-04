#__author:  Administrator
#date:  2017/1/5

from django import template
from django.utils.safestring import mark_safe
from django.utils.timezone import datetime, timedelta#用的是项目的时区
from collections import Iterable
from django.core.exceptions import FieldDoesNotExist
register = template.Library()

@register.simple_tag
def render_app_name(admin_class):
    return admin_class.model._meta.verbose_name_plural

@register.simple_tag
def get_query_sets(admin_class):
    return admin_class.model.objects.all()

@register.simple_tag
def build_table_row(request, obj, admin_class):
    row_ele = ""
    for index, column in enumerate(admin_class.list_display):
        try:
            field_obj = obj._meta.get_field(column)
            if field_obj.choices:#choices type
                column_data = getattr(obj,"get_%s_display" % column)()
            else:
                column_data = getattr(obj,column)
            if type(column_data).__name__ == 'datetime':
                column_data = column_data.strftime("%Y-%m-%d %H:%M:%S")
            if index == 0:#添加a标签，使得可以跳转到修改页
                column_data = "<a href='%s%s/change/'>%s</a>" %(request.path, obj.id, column_data)


        except FieldDoesNotExist as e:
            if hasattr(admin_class, column):
                column_func = getattr(admin_class, column)
                admin_class.instance = obj
                admin_class.request = request
                column_data = column_func()
        row_ele += "<td>%s</td>" % column_data

    return mark_safe(row_ele)

@register.simple_tag
def render_filter_ele(filter_field,admin_class,filter_condtions):
    #select_ele = '''<select class="form-control" name='%s' ><option value=''>----</option>''' %filter_field
    select_ele = '''<select class="form-control" name='{filter_field_name}' ><option value=''>----</option>'''
    field_obj = admin_class.model._meta.get_field(filter_field)
    if field_obj.choices:
        selected = ''
        for choice_item in field_obj.choices:
            # print("choice",choice_item,filter_condtions.get(condtion),type(filter_condtions.get(condtion)))
            if filter_condtions.get(filter_field) == str(choice_item[0]):
                selected ="selected"

            select_ele += '''<option value='%s' %s>%s</option>''' %(choice_item[0],selected,choice_item[1])
            selected =''

    if type(field_obj).__name__ == "ForeignKey":
        selected = ''
        for choice_item in field_obj.get_choices()[1:]:
            if filter_condtions.get(filter_field) == str(choice_item[0]):
                selected = "selected"
            select_ele += '''<option value='%s' %s>%s</option>''' %(choice_item[0],selected,choice_item[1])
            selected = ''
    '''针对时间进行过滤'''
    if type(field_obj).__name__ in ["DateTimeField", "DateField"]:

        date_ele = []
        today_ele = datetime.now().date()
        date_ele.append(['今天', datetime.now().date()])
        date_ele.append(['昨天', today_ele - timedelta(days=1)])
        date_ele.append(['近七天', today_ele - timedelta(days=7)])
        date_ele.append(['近一个月', today_ele - timedelta(days=30)])
        date_ele.append(['本月', today_ele.replace(day=1)])
        date_ele.append(['近90天', today_ele - timedelta(days=90)])
        date_ele.append(['近180天', today_ele - timedelta(days=180)])
        date_ele.append(['本年', today_ele.replace(month=1, day=1)])
        date_ele.append(['近一年', today_ele - timedelta(days=365)])
        selected = ''
        for item in date_ele:
            select_ele += '''<option value='%s' %s>%s</option>''' % (item[1], selected, item[0])
        filter_field_name = "%s__gte" %filter_field
    else:
        filter_field_name = filter_field
    select_ele += "</select>"
    select_ele = select_ele.format(filter_field_name=filter_field_name)
    return mark_safe(select_ele)

@register.simple_tag
def build_paginators(query_sets, filter_conditions, previous_orderby, search_text):
    '''返回整个分页页面'''
    page_btns = ''
    added_dot_ele = False
    filters= ''
    for k, v in filter_conditions.items():
        filters += '&%s=%s' %(k, v)
    for page_num in query_sets.paginator.page_range:
        if page_num < 3 or page_num > query_sets.paginator.num_pages - 2 or \
                abs(query_sets.number - page_num) <= 1:
            ele_class = ""
            if query_sets.number == page_num:
                added_dot_ele = False
                ele_class = "active"
            page_btns += '''<li class="%s"><a href="?page=%s%s&o=%s&_q=%s">%s</a></li>''' %(ele_class, page_num, filters, previous_orderby,search_text, page_num)
        else:#显示...
            if added_dot_ele == False:
                page_btns += "<li><a>...</a></li>"
                added_dot_ele = True
    return mark_safe(page_btns)

@register.simple_tag
def build_table_header_column(column, orderby_key, filter_condtions, admin_class):
    filters = ''
    for k, v in filter_condtions.items():
        filters += '&%s=%s' % (k, v)
    ele = '''<td><a href="?o={orderby}%s">{columns}</a>
    {sort_icon}
    </td>'''%filters
    if orderby_key:
        if orderby_key.startswith("-"):
            sort_icon = '''<span class="glyphicon glyphicon-chevron-up"></span>'''
        else:
            sort_icon = '''<span class="glyphicon glyphicon-chevron-down"></span>'''
        if orderby_key.strip("-") == column:
            orderby_key = orderby_key
        else:
            orderby_key = column
            sort_icon = ''

        try:
            column_verbose_name = admin_class.model._meta.get_field(column).verbose_name.upper()
        except FieldDoesNotExist as e:
            column_verbose_name = getattr(admin_class, column).display_name
            ele = '''<td><a href="javascript:void(0);">{column}</a></td>'''.format(column=column_verbose_name)
            return mark_safe(ele)
        ele = ele.format(orderby=orderby_key, columns=column_verbose_name, sort_icon=sort_icon)

    else:
        try:
            column_verbose_name = admin_class.model._meta.get_field(column).verbose_name.upper()
        except FieldDoesNotExist as e:
            column_verbose_name = getattr(admin_class, column).display_name
            ele = '''<td><a href="javascript:void(0);">{column}</a></td>'''.format(column=column_verbose_name)
            return mark_safe(ele)
        ele = ele.format(orderby=column, columns=column_verbose_name,sort_icon='')
    return mark_safe(ele)

@register.simple_tag
def get_model_name(admin_class):
    '''返回表名'''
    return admin_class.model._meta.verbose_name_plural

@register.simple_tag
def get_m2m_obj_list(admin_class, field,  model_form_obj):
    '''返回m2m所有待选数据'''

    field_obj = getattr(admin_class.model, field.name)
    '''所有数据'''
    all_obj_list =  field_obj.rel.model.objects.all()

    '''选中的数据'''
    if model_form_obj.instance.id:
        obj_instance_field = getattr(model_form_obj.instance, field.name)
        selected_obj_list = obj_instance_field.all()
    else:#代表这是在创建新的数据
        return all_obj_list
    standby_obj_list = []
    for obj in all_obj_list:
        if obj not in selected_obj_list:
            standby_obj_list.append(obj)
    return standby_obj_list

@register.simple_tag
def get_m2m_selected_obj_list(model_form_obj, field):
    '''返回m2m已选中的数据'''
    if model_form_obj.instance.id:
        field_obj = getattr(model_form_obj.instance, field.name)
        return field_obj.all()

def recursive_related_objs_lookup(objs):
    # model_name = objs[0]._meta.model_name
    ul_ele = "<ul>"
    for obj in objs:
        li_ele = '''<li>%s:%s</li>'''%(obj._meta.verbose_name, obj.__str__().strip("<>"))
        ul_ele += li_ele
        '''把所有直接关联的m2m字段取出来'''
        for m2m_field in obj._meta.local_many_to_many:
            sub_ul_ele = "<ul>"
            m2m_field_obj = getattr(obj, m2m_field.name)#getattr(customer里的数据对象, 'tags')
            for o in m2m_field_obj.select_related():#customer.tags.select_related()
                li_ele = '''<li>%s:%s</li>'''%(m2m_field.verbose_name, o.__str__().strip("<>"))
                sub_ul_ele += li_ele
            sub_ul_ele += "</ul>"
            ul_ele += sub_ul_ele

        for related_obj in obj._meta.related_objects:
            '''related_obj.__repr__()=='<ManyToOneRel: app1.payment>’,把related_obj变成一个字符串
            
            '''
            if "ManyToManyRel"  in related_obj.__repr__():
                if hasattr(obj, related_obj.get_accessor_name()):  # 反向获取表
                    accessor_obj = getattr(obj, related_obj.get_accessor_name())

                    if hasattr(accessor_obj, 'all'):  # all()==select_related()
                        target_objs = accessor_obj.all()  # 获取反向获取到的表的所有数据

                        sub_ul_ele = "<ul style = 'color:red'>"
                        for o in target_objs:
                            li_ele = '''<li>%s:%s</li>''' % (o._meta.verbose_name, o.__str__().strip("<>"))
                            sub_ul_ele += li_ele
                        sub_ul_ele += "</ul>"
                        ul_ele += sub_ul_ele
            elif hasattr(obj, related_obj.get_accessor_name()):#反向获取表
                accessor_obj = getattr(obj, related_obj.get_accessor_name())

                if hasattr(accessor_obj, 'all'):#all()==select_related()
                    target_objs = accessor_obj.all()#获取反向获取到的表的所有数据

                if len(target_objs) > 0:
                    nodes = recursive_related_objs_lookup(target_objs)
                    ul_ele += nodes
    ul_ele += "</ul>"
    return ul_ele
@register.simple_tag
def display_obj_related(objs):
    if not isinstance(objs, Iterable):
        objs = [objs, ]
    if objs:
        model_class = objs[0]._meta.model
        model_name = objs[0]._meta.model_name
    return mark_safe(recursive_related_objs_lookup(objs))

@register.simple_tag
def get_action_verbose_name(admin_class, action):

    action_func = getattr(admin_class, action)
    return action_func.display_name if hasattr(action_func, "display_name") else action
