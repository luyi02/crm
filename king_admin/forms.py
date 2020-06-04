#_author: "luyi"
#date: 2020/5/26

from django.forms import forms, ModelForm, ValidationError
from app1 import models
from django.utils.translation import ugettext as _
def create_model_form(request, admin_class):
    '''动态生成model form'''

    '''__new__方法在__init__方法执行前执行，可用来加css样式
        base_fields是一个包含有字段名和字段对象的一个字典
    '''
    def __new__(cls, *args, **kwargs):
        for field_name, field_obj in cls.base_fields.items():
            #cls.base_fields["qq"].widget.attrs["class"]='form-control'
            field_obj.widget.attrs["class"] = 'form-control'
            if not hasattr(admin_class, "is_add_form"):
                if field_name in admin_class.readonly_fields:
                    field_obj.widget.attrs["disabled"] = 'disabled'

            if hasattr(admin_class, "clean_%s" %field_name):
                field_clean_func = getattr(admin_class, "clean_%s" %field_name)
                setattr(cls, "clean_%s" %field_name, field_clean_func)
        return ModelForm.__new__(cls)

    def default_clean(self):
        '''给所有的form加一个clean验证'''
        error_list = []

        if self.instance.id:#这是一个修改的表单，而不是添加的表单
            for field in admin_class.readonly_fields:
                field_val = getattr(self.instance, field) #获取数据库里的值

                #判断是否为m2m
                if hasattr(field_val, "select_related"):
                    m2m_objs = getattr(field_val, "select_related")().select_related()
                    m2m_vals = [i[0] for i in m2m_objs.values_list("id")]
                    set_m2m_vals = set(m2m_vals)
                    set_m2m_vals_from_frontend = set([i.id for i in self.cleaned_data.get(field)])
                    if set_m2m_vals != set_m2m_vals_from_frontend:
                        error_list.append(
                            ValidationError(
                                _('Field %(field)s is readonly'),
                                code='invalid',
                                params={'field': field}
                            )
                        )
                    continue
                field_val_from_frontend = self.cleaned_data.get(field)#获取前端发送过来的值
                if field_val != field_val_from_frontend:
                    error_list.append(
                        ValidationError(
                            _('Field %(field)s is readonly, data shoule be %(val)s'),
                            code='invalid',
                            params={'field': field, 'val': field_val}
                        )
                    )
                if error_list:
                    raise error_list
                admin_class.default_form_validation(self)
        #判断是否为表只读
        if admin_class.readonly_table:
            error_list.append(
                ValidationError(
                    _('Table is readonly, cannot be modified or added'),
                    code='invalid'
                )
            )
    class Meta:
        model = admin_class.model
        fields = "__all__"
        exclude = admin_class.modelform_exclude_fields
    attrs = {'Meta': Meta, '__new__': __new__}
    '''通过type动态创建modelForm类'''
    _model_form_class = type("DynamicModelForm", (ModelForm,), attrs)
    setattr(_model_form_class, "default_clean", default_clean)
    return _model_form_class