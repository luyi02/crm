from django.shortcuts import render, HttpResponse
from app1 import models
from crm import settings
import os, json
# Create your views here.
def stu_my_classes(req):
    return render(req, "student/stu_my_classes.html")

def studyrecords(request, enroll_obj_id):
    enroll_obj = models.Enrollment.objects.get(id=enroll_obj_id)
    return render(request, "student/studyrecords.html",{"enroll_obj": enroll_obj})

def homework_detail(request, studyrecord_id):
    studyrecord_obj = models.StudyRecord.objects.get(id=studyrecord_id)

    if request.method == "POST":
        print(request.FILES)
        homework_path = "{base_dir}/{course_id}/{course_record_id}/{studyrecord_id}".format(
            base_dir=settings.HOMEWORK_DATA,
            course_id=studyrecord_obj.student.enrolled_class.id,
            course_record_id=studyrecord_obj.course_record_id,
            studyrecord_id=studyrecord_obj.id
        )

        if not os.path.isdir(homework_path):
            os.makedirs(homework_path, exist_ok=True)

        for k, file_obj in request.FILES.items():
            with open('%s/%s' % (homework_path, file_obj.name), "wb") as f:
                for chunk in file_obj.chunks():
                    f.write(chunk)
        return HttpResponse(json.dumps({"status": 0, "msg": "file upload sucess"}))

    return render(request, "student/homework_detail.html", {"studyrecord_obj":studyrecord_obj})