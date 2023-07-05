from django.shortcuts import render, redirect
from .forms import ProgramForm, Profiles
from planning.models import get_profile_courses, get_program_courses, get_courses_term, Program, Profile, Schedule, Scheduler
from accounts.models import Account, get_user
from django.contrib.auth.models import User


# def get_data(profil):
#     return {"semester": {"period1" : [{"course_code": "tata24", "details": []}]}}


COURSE_TAGS = {
                "Kurskod": "",
                "Kursnamn": "",
                "Hp": "",
                "Nivå": "",
                "Vof": "",
                "Detaljer": "",
                }


def home(request):
    if not request.user.is_authenticated:
        return redirect("login")
    
    account = Account.objects.get(user=get_user(request.user.username))

    if account.program is None:
        return redirect("setup")

    user_program = account.program
    profiles = [(profile.profile_code, profile.profile_name) for profile in user_program.profiles.all()]
    profiles_dict = dict(profiles) 
    
    if request.method == "POST":
        if "pick_profile" in request.POST:
            profile_code = request.POST["profiles"]
            profile_name = Profile.objects.get(profile_code=profile_code).profile_name
            form = Profiles(profiles)
            semester = 7
        else:
            profile_code = request.POST.get("profile_code")
        
        if "t7" in request.POST:
            semester = int(request.POST.get("t7")[-1:])
        
        elif "t8" in request.POST:
            semester = int(request.POST.get("t8")[-1:])
        
        elif "t9" in request.POST:
            semester = int(request.POST.get("t9")[-1:])
            
        form = Profiles(profiles)
        profile_name = profiles_dict[profile_code]
        profile = Profile.objects.get(profile_code=profile_code)
        semester_courses = get_courses_term(program=account.program, semester=semester, profile=profile)
            
    else:
        profile_code = "free"
        profile = Profile.objects.get(profile_code=profile_code)
        profile_name = profile.profile_name
        semester_courses = get_courses_term(program=account.program, semester=7, profile=profile)
        form = Profiles(profiles)
        print(semester_courses)

    
    return render(request, "home.html", {"term_courses": semester_courses, 
                                             "program_name": user_program, 
                                             "termin": "Termin 7", 
                                             "form": form, 
                                             "profile_picked": True, 
                                             "profile_code": profile_code, 
                                             "profile_name": profile_name, 
                                             "course_tags": COURSE_TAGS}
                                         )

def setup(request):
    if not request.user.is_authenticated:
        return redirect("login")
    
    if request.method == "POST":
        form = ProgramForm(request.POST)
        if form.is_valid():
            program_code = request.POST.get("program").upper()
            program = Program.objects.filter(program_code=program_code)
            if program:
                user = User.objects.get(username=request.user.username)
                account = Account.objects.get(user=user)
                program = program[0]
                account.program = program
                account.save()
            return redirect("home")
                
    else:
        form = ProgramForm()

    return render(request, "setup.html", {"form": form})
