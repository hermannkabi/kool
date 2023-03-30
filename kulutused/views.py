from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, logout as django_logout, login, get_user_model
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm
from kulutused.models import Transaction, Group, UserPrefs
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from django.template.defaulttags import register
from django.contrib.auth.decorators import login_required


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    return value * arg

@register.filter
def contains_user(value, arg):
    return len(Group.objects.get(pk=value).filter(members__username=arg)) > 0

# Create your views here.

# The view for the homepage
# When logged in, redirect to index
def homepage(request):
    if request.user.is_authenticated:
        return redirect("kulutused:index")
    else:
        return render(request, "kulutused/homepage.html")


@login_required
def choose_group(request):

    groups_containing_user = Group.objects.filter(members__username=request.user.username)


    context = {
        "groups":groups_containing_user,
    }

    return render(request, "kulutused/choose-group.html", context)


@login_required
def dashboard(request, group_id):


    # Check if the group exists
    group = get_object_or_404(Group, pk=group_id)

    # You still have to check if the user has access to said group_id
    if len(group.members.filter(username=request.user.username)) <= 0:
        return redirect("kulutused:homepage")
    


    # Gets all available users in group
    users = group.members.all()


    recent_transactions = Transaction.objects.filter(group_id=group_id).order_by("-date_sent")[:5]

    
    # In this context (pun intended), all_users refers to all the user within this group
    context = {"user":request.user, "all_users":users, "recent":recent_transactions, "group_id":group_id, "group_name":group.group_name}


    return render(request, "kulutused/index.html", context)

    


def index(request):

    # Checks for UserPrefs, if there is no UserPref for the current User, or group_id is null, redirect to group choice

    try:
        if len(UserPrefs.objects.get(user=request.user)) <= 0:
            return redirect("kulutused:choose-group")
    except:
        # Obviously, there is no data
        return redirect("kulutused:choose-group")
    
    group_id = get_object_or_404(UserPrefs, user=request.user).group_id
    
    return redirect("kulutused:dashboard", group_id=group_id)



def register(request):

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            username = form.cleaned_data["username"]
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect("kulutused:index")

    else:
        form = UserCreationForm()

    context = {"form":form}
    return render(request, "registration/register.html", context)

def logout(request):

    django_logout(request)

    return HttpResponseRedirect(reverse("kulutused:index"))


@login_required
def send_transaction(request, group_id):
    User = get_user_model()

    from_user = request.user
    try:

        to_user = User.objects.get(username=request.POST["to_name"].lower())
    except User.DoesNotExist:
        messages.error(request, "Sellist kasutajat ei leitud!")
        return HttpResponseRedirect(reverse("kulutused:dashboard"), {"group_id":group_id})
    
    if from_user == to_user:

        messages.error(request, "Iseendale ei saa raha saata!")
        return HttpResponseRedirect(reverse("kulutused:dashboard"), {"group_id":group_id})


    amount = float(request.POST["amount"])

    if amount <= 0:
        messages.error(request, "Viga makse suuruses!")
        return HttpResponseRedirect(reverse("kulutused:dashboard"), {"group_id":group_id})


    group = Group.objects.get(id=group_id)
    
    if to_user not in group.members.all():
        messages.error(request, "Inimene, kellele üritad makset teha, ei ole sinu grupis!")
        return HttpResponseRedirect(reverse("kulutused:dashboard"), {"group_id":group_id})

    if request.user not in group.members.all():
        messages.error(request, "Sa ei ole grupis, kuhu üritad makset sooritada!")
        return HttpResponseRedirect(reverse("kulutused:dashboard"), {"group_id":group_id})



    date_sent = timezone.now()
    notes = request.POST['notes']
    t = Transaction(from_user=from_user, to_user=to_user, amount=amount, date_sent=date_sent, notes=notes, group_id=group_id)
    t.save()


    return HttpResponseRedirect(reverse("kulutused:dashboard", kwargs={"group_id":group_id}))


@login_required
def summary(request, group_id):

    # Throw a 404 if Group does not exist
    group = get_object_or_404(Group, pk=group_id)

    # Check if the user has access to said group_id
    if len(group.members.filter(username=request.user.username)) <= 0:
        return redirect("kulutused:homepage")


    # Returns the amount of money that user has (if negative, user is in debt)
    def get_total_of_user(user):
        return sum([x.amount for x in Transaction.objects.filter(group_id=group_id).filter(to_user__username=user)]) - sum([x.amount for x in Transaction.objects.filter(group_id=group_id).filter(from_user__username=user)])


    # All transactions in this group
    all_transactions = Transaction.objects.filter(group_id=group_id).order_by("-date_sent")


    # If no transactions can be found, redirect back home.
    if len(all_transactions) <=0:
        return redirect("kulutused:homepage")



    # This whole section is for the graph
    # We use chart.js to create responsive charts with (quite) few lines of simple code
    # Returns a dict with the keys of usernames and values of their totals
    user_data = {}
    
    # Cycle through every User in Group
    for name in group.members.all():
        user_data[name.username] = get_total_of_user(name.username)
    

    # Sort by amount of money
    sorted_user_data = dict(sorted(user_data.items(), key=lambda x:x[1], reverse=True))


    # Labels and data for the graph
    labels = []
    data = []

    for username, amount in sorted_user_data.items():
        if amount != 0:
            labels.append(username.title())
            data.append(amount)

    context = {
        'all_transactions': all_transactions,
        "user_data": sorted_user_data,
        'labels':labels,
        'data':data,
        "group_id":group_id,
    }
    

    return render(request, "kulutused/summary.html", context)


def join(request, group_id):

    group = get_object_or_404(Group, pk=group_id)


    # A POST request indicates that they want to join
    if request.method == "POST":
        group.members.add(request.user)
        group.save()
        return redirect("kulutused:dashboard", group_id=group_id)

    
    # Check if the user has already joined the group, if so, then redirect to dashboard
    if request.user in group.members.all():
        return redirect("kulutused:dashboard", group_id=group_id)


    # Add some basic group data for the template

    context = {
        "group_id":group_id,
        "group_name":group.group_name
    }

    return render(request, "kulutused/join.html", context)


@login_required
def create_group(request):
    if request.method == "POST":

        post_data = request.POST

        group_name = post_data.get("group_name", None)
        description = post_data.get("description", '')

        if group_name == None:
            messages.error(request, "Sisesta grupi nimi!")
            return render(request, "kulutused/create_group.html")


        # Save the data gotten (group name and description) to database
        g = Group(group_name=group_name, desc=description)

        g.save()

        g.members.add(request.user)

        # Go to the dashboard of the group
        return redirect("kulutused:dashboard", group_id=g.id)

    return render(request, "kulutused/create_group.html")


def share_group(request, group_id):

    full_url = request.build_absolute_uri(reverse("kulutused:join", kwargs={'group_id':group_id}))

    return render(request, "kulutused/share.html", {"url":full_url})