# This file is part of Workout Manager.
# 
# Foobar is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
import logging

from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import Http404
from django.forms import ModelForm
from django.core.context_processors import csrf

from manager.models import TrainingSchedule
from manager.models import Exercise
from manager.models import ExerciseComment
from manager.models import Day


logger = logging.getLogger('workout_manager.custom')

def index(request):
    latest_trainings = TrainingSchedule.objects.all().order_by('-creation_date')[:5]
    return render_to_response('index.html', {'latest_workouts_list': latest_trainings})

    
# ************************
# Workout functions
# ************************
class WorkoutForm(ModelForm):
    class Meta:
        model = TrainingSchedule

def view_workout(request, id):
    p = get_object_or_404(TrainingSchedule, pk=id)
    return render_to_response('workout/view.html', {'workout': p})
    
def add(request):
    
    workout = TrainingSchedule()
    workout.save()
    
    return HttpResponseRedirect('/workout/%s/view/' % workout.id)
    
    template_data = {}
    template_data.update(csrf(request))
    
    
    
    if request.method == 'POST':
        day_form = DayForm(request.POST)
        new_days = day_form.save()
        #return HttpResponseRedirect('/workout/add/step/2')
    else:
        day_form = DayForm()
    template_data['day_form'] = day_form
    
    if request.method == 'POST':
        workout_form = WorkoutForm(request.POST)
        new_workout = workout_form.save()
        return HttpResponseRedirect('/workout/add/step/2')
    else:
        workout_form = WorkoutForm()
    
    exercises = Exercise.objects.all()
    template_data['exercises'] = exercises
    
    
    template_data['workout_form'] = workout_form
    
    return render_to_response('workout/add.html', template_data)



# ************************
# Day functions
# ************************
class DayForm(ModelForm):
    class Meta:
        model = Day
        exclude=('training',)

def edit_day(request, id, day_id=None):
    template_data = {}
    template_data.update(csrf(request))
    
    # Load workout
    workout = get_object_or_404(TrainingSchedule, pk=id)
    template_data['workout'] = workout
    
    # Load day
    if not day_id:
        day = Day()
    else:
        day = get_object_or_404(Day, pk=day_id)
    template_data['day'] = day
    
    # Process request
    if request.method == 'POST':
        day_form = DayForm(request.POST, instance=day)
        day = day_form.save(commit=False)
        day.training = workout
        day.save()
        
        return HttpResponseRedirect('/workout/%s/view/' % id)
    else:
        day_form = DayForm(instance=day)
    template_data['day_form'] = day_form
    
    return render_to_response('day/edit.html', template_data)
    
# ************************
# Exercise comment functions
# ************************

def exercisecomment_delete(request, id):
    # Load the comment
    comment = get_object_or_404(ExerciseComment, pk=id)
    exercise_id = comment.exercise.id
    comment.delete()
    
    return HttpResponseRedirect('/exercise/view/%s' % exercise_id)
    
    

# ************************
# Exercise functions
# ************************

class ExerciseCommentForm(ModelForm):
    class Meta:
        model = ExerciseComment
        exclude=('exercise',)

class ExerciseForm(ModelForm):
    class Meta:
        model = Exercise

def exercise_overview(request):
    """Overview with all exercises
    """
    
    template_data = {}
    ex_data = {}
    
    # Gather all exercises and group them by category
    for i in Exercise.objects.all().order_by('category'):
        if not ex_data.get(i.category.id):
            ex_data[i.category.id] = {'category': i.category, 'exercises': []}
        
        ex_data[i.category.id]['exercises'].append(i)

    template_data['exercises'] = ex_data
    logger.debug(template_data)
    
    return render_to_response('exercise/overview.html', template_data)

    
def exercise_view(request, id, comment_id=None):
    """ Detail view for an exercise
    """
    template_data = {}
    template_data['comment_edit'] = False
    
    # Load the exercise itself
    exercise = get_object_or_404(Exercise, pk=id)
    template_data['exercise'] = exercise
    
    #
    # We can create and edit comments from this page, so look for Posts
    template_data.update(csrf(request))
    
    # Adding a new comment
    if request.method == 'POST' and not comment_id:
        comment_form = ExerciseCommentForm(request.POST)
        comment_form.exercise = exercise
        new_comment = comment_form.save(commit=False)
        new_comment.exercise = exercise
        new_comment.save()
        return HttpResponseRedirect('/exercise/view/%s' % id)
    else:
        comment_form = ExerciseCommentForm()

    # Editing a comment
    if comment_id:
        exercise_comment = get_object_or_404(ExerciseComment, pk=comment_id)
        template_data['comment_edit'] = exercise_comment
        
        comment_edit_form = ExerciseCommentForm(instance=exercise_comment)
        template_data['comment_edit_form'] = comment_edit_form
        
        if request.method == 'POST':
            logger.debug(exercise_comment.id)
            comment_form = ExerciseCommentForm(request.POST, instance=exercise_comment)
            comment = comment_form.save(commit=False)
            comment.save()
            return HttpResponseRedirect('/exercise/view/%s' % id)
        
    
    template_data['comment_form'] = comment_form
    
    # Render
    return render_to_response('exercise/view.html', template_data)


def exercise_edit(request, id=None):
    template_data = {}
    template_data.update(csrf(request))
    
    if not id:
        exercise = Exercise()
    else:
        exercise = get_object_or_404(Exercise, pk=id)
    template_data['exercise'] = exercise
    
    if request.method == 'POST':
        exercise_form = ExerciseForm(request.POST, instance=exercise)
        exercise = exercise_form.save()
        id = exercise.id
        return HttpResponseRedirect('/exercise/view/%s' % id)
    else:
        exercise_form = ExerciseForm(instance=exercise)
    
    template_data['edit_form'] = exercise_form
    
    return render_to_response('exercise/edit.html', template_data)


def exercise_delete(request, id):
    # Load the exercise
    exercise = get_object_or_404(Exercise, pk=id)
    exercise.delete()
    
    return HttpResponseRedirect('/exercise/overview/')