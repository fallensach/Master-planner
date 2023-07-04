from ninja import NinjaAPI, ModelSchema, Schema
from django.http.response import JsonResponse
from planning.models import Schedule, Course, Scheduler, Examination
from planning.management.commands.scrappy.courses import fetch_course_info
from accounts.models import get_user, Account
from typing import List
from .schemas import *

api = NinjaAPI()

@api.get('get_schedule/{schedule_id}', response=ScheduleSchema)
def get_schedule(request, schedule_id):
    schedule = Schedule.objects.get(schedule_id=schedule_id)
    return schedule

# @api.post('account/{choice}')
# def choice(request, scheduler_id):
#     account = Account.objects.get(user=request.user)
# @api.get('') 

@api.get('get_course/{course_code}', response=CourseSchema)
def get_course(request, course_code):
    course_info = Course.objects.get(course_code=course_code)
    return course_info

@api.get('get_courses/{profile}/{semester}', response=SemesterCourses)
def get_semester_courses(request, profile, semester):
    program = Account.objects.get(user=request.user).program
    
    period1 = Scheduler.objects.filter(program=program, 
                                       profile=profile, 
                                       schedule__semester=f"Termin {semester}",
                                       schedule__period="Period 1")
    period2 = Scheduler.objects.filter(program=program, 
                                       profile=profile, 
                                       schedule__semester=f"Termin {semester}",
                                       schedule__period="Period 2")
        
    data = {"period_1": list(period1),
            "period_2": list(period2)}
    
    return data


@api.get('get_extra_course_info/{course_code}')
def get_extra_course_info(request, course_code):
    extra_info = fetch_course_info(course_code)
    course = Course.objects.get(course_code=course_code)
    extra_info["course_code"] = course.course_code
    extra_info["course_name"] = course.course_name
    """    
    return  {"examination": [{"code": "lab",
                              "name":  "laboration",
                              "scope": "6",
                              "grading": "u/g"}],
             "examinator": "cyrille",
             "location": "valla",
             "main_field": ["matematik"]
                }"""
    return extra_info
