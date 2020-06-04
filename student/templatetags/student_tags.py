#_author: "luyi"
#date: 2020-06-01
from django import template
register = template.Library()
from django.db.models import Sum
@register.simple_tag
def get_score_enroll_obj(enroll_obj, customer_obj):
    study_records = enroll_obj.studyrecord_set.\
        filter(course_record__from_class_id = enroll_obj.enrolled_class.id)

    return study_records.aggregate(Sum("score"))

