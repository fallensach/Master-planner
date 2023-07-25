from django.db import models, IntegrityError
from planning.management.commands.scrappy.program_plan import ProgramPlan
from typing import Union
import uuid

    
class MainField(models.Model):
    field_name = models.CharField(max_length=15, primary_key=True)

    def __str__(self):
        return self.field_name

class Course(models.Model):
    course_code = models.CharField(max_length=6, primary_key=True)
    examinator = models.CharField(max_length=50, null=True)
    course_name = models.CharField(max_length=120)
    hp = models.CharField(max_length=5, default=1)
    level = models.CharField(max_length=20)
    vof = models.CharField(max_length=5)
    campus = models.CharField(max_length=20, null=True)
    main_fields = models.ManyToManyField(MainField)

    def __str__(self):
        return f"{self.course_code}, {self.hp}, {self.level}"

class Examination(models.Model):
    id = models.AutoField(primary_key=True)
    hp = models.CharField(max_length=5)
    name = models.CharField(max_length=50)
    grading = models.CharField(max_length=15)
    code = models.CharField(max_length=10)
    course = models.ForeignKey(Course,on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name, self.course

class Schedule(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    period = models.IntegerField()
    semester = models.IntegerField()
    block = models.CharField(max_length=10)
    
    def save(self, *args, **kwargs):
        self.id = f"{self.semester}.{self.period}.{self.block}"
        super(Schedule, self).save(*args, **kwargs)

    def __str__(self):
        return f"sem: {self.semester}, per: {self.period}, block: {self.block}"

class Profile(models.Model):
    profile_name = models.CharField(max_length=120)
    profile_code = models.CharField(max_length=10, primary_key=True)

    def __str__(self):
        return self.profile_name

class Program(models.Model):
    program_code = models.CharField(max_length=10, primary_key=True)
    program_name = models.CharField(max_length=100)
    profiles = models.ManyToManyField(Profile)

    def __str__(self):
        return self.program_name

class Scheduler(models.Model):
    # scheduler_id = models.AutoField(primary_key=True)
    scheduler_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    profiles = models.ManyToManyField(Profile)
    linked = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{str(self.course)}\n{str(self.program)}\n{str(self.profiles)}\n{str(self.schedule)}"

def register_programs(program_data: list[tuple[str, str]]):
    # print("starting register_programs") 
    programs = []
    for code, name in program_data:
        program = Program(program_code=code, program_name=name)
        programs.append(program)
    
    Program.objects.bulk_create(programs)

def register_profiles(profile_data: list[tuple[str, str, str]]) -> None:
    # print("starting register_profiles")
    profiles = {}
    program_profile_list = []
    for name, code, program_code in profile_data:
        profile = Profile(profile_code=code,
                          profile_name=name
                          )
        program_profile = Program.profiles.through(program_id=program_code,
                                                   profile_id=code)
        program_profile_list.append(program_profile)
        profiles[code] = profile
    
    Profile.objects.bulk_create(profiles.values())
    Program.profiles.through.objects.bulk_create(program_profile_list)

def register_courses(data: dict[Union[str, int]]) -> None:
    schedulers = []
    courses = {}
    schedules = {}
    scheduler_profiles_list = []
    test = {}
    
    for course_data in data:
        semester = course_data["semester"]
        period = course_data["period"]
        block = course_data["block"]

        if (course_data["program_code"], course_data["course_code"], f"{semester}.{period}.{block}") in test:
            scheduler_id = test[course_data["program_code"], course_data["course_code"], f"{semester}.{period}.{block}"]
        else:
            course = Course(course_code=course_data["course_code"],
                            course_name=course_data["course_name"],
                            hp=course_data["hp"],
                            level=course_data["level"],
                            vof=course_data["vof"]
                            )

            semester = course_data["semester"]
            period = course_data["period"]
            block = course_data["block"]
            schedule_id = f"{semester}.{period}.{block}"

            schedule = Schedule(id=schedule_id,
                                block=block,
                                semester=semester,
                                period=period
                                )
            courses[course.course_code] = course
            schedules[schedule.id] = schedule

            # profile = Profile.objects.get(profile_code=course_data["profile_code"])
            # create instance of course in Scheduler
            scheduler = Scheduler(course=course,
                                  program_id=course_data["program_code"], # TODO HERE IS THE BUG, should not add everytime
                                  schedule=schedule
                                  )

            
            schedulers.append(scheduler)

            scheduler_id = scheduler.scheduler_id
            test[scheduler.program_id, scheduler.course_id, scheduler.schedule_id] = scheduler_id

        scheduler_profile = Scheduler.profiles.through(profile_id=course_data["profile_code"],
                                                       scheduler_id=scheduler_id)
        scheduler_profiles_list.append(scheduler_profile)
        # scheduler.profiles.add( course_data["profile_code"])
    
    Course.objects.bulk_create(courses.values())
    Schedule.objects.bulk_create(schedules.values())                            
    Scheduler.objects.bulk_create(schedulers)
    Scheduler.profiles.through.objects.bulk_create(scheduler_profiles_list, ignore_conflicts=True)
    
    linked_course_instances = []
    for course_instance in Scheduler.objects.all():
        if "*" in course_instance.course.hp and course_instance.schedule.period == 2:
            first_part = Scheduler.objects.get(course=course_instance.course,
                                               program=course_instance.program,
                                               schedule__period=1,
                                               schedule__semester=course_instance.schedule.semester
                                               )

            first_part.linked = course_instance
            course_instance.linked = first_part
            linked_course_instances.extend([first_part, course_instance])
    Scheduler.objects.bulk_update(linked_course_instances, ["linked"])

def get_courses_term(program: any, semester: str, profile=None): # TODO fix typing, döpa om funktion
    period_1 = list(Scheduler.objects.filter(program=program, 
                                             profiles=profile,
                                             schedule__semester=semester, 
                                             schedule__period=1))
    
    period_2 = list(Scheduler.objects.filter(program=program, 
                                             profiles=profile,
                                             schedule__semester=semester,
                                             schedule__period=2))

    return {1: period_1, 2: period_2}

def register_course_details(data, course_code):
    examinations = []
    fields = []
    created: bool
    
    print(f'Adding examination: {course_code}')
    for examination in data["examination"]:
        course = Course.objects.get(course_code=course_code)
        exam = Examination(
            code=examination["code"],
            course=course,
            hp=examination["hp"],
            name=examination["name"],
            grading=examination["grading"]
        )
        examinations.append(exam)
        
    for field in data["main_field"]:
        main_field, created = MainField.objects.get_or_create(field_name=field)
        fields.append(main_field)
        
    updated_course = Course.objects.filter(course_code=course_code)
    course = Course.objects.get(course_code=course_code)
    course.main_fields.add(*fields)
    updated_course.update(examinator=data["examinator"])
    updated_course.update(campus=data["location"])
        
    if created:
        MainField.objects.bulk_create(fields)
    
    Examination.objects.bulk_create(examinations)