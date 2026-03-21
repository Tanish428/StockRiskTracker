from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from ..models import Dictionary, QuizQuestion

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('dashboard')   # normal users go to normal dashboard
    
    return render(request, 'admin_dashboard.html')

@login_required
def manage_users(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    users = User.objects.all()

    return render(request, 'manage_users.html', {'users': users})

@login_required
def manage_dictionary(request):

    if not request.user.is_superuser:
        return redirect('dashboard')

    if request.method == "POST":
        term = request.POST.get('term')
        meaning = request.POST.get('meaning')

        # prevent empty fields
        if term and meaning:
            Dictionary.objects.create(term=term, meaning=meaning)

    terms = Dictionary.objects.all()

    return render(request, 'manage_dictionary.html', {'terms': terms})

@login_required
def delete_term(request, term_id):
    if not request.user.is_superuser:
        return redirect('dashboard')

    term = get_object_or_404(Dictionary, id=term_id)
    term.delete()

    return redirect('manage_dictionary')

@login_required
def update_term(request, term_id):

    if not request.user.is_superuser:
        return redirect('dashboard')

    term_obj = get_object_or_404(Dictionary, id=term_id)

    if request.method == "POST":
        term = request.POST.get('term')
        meaning = request.POST.get('meaning')

        if term and meaning:
            term_obj.term = term
            term_obj.meaning = meaning
            term_obj.save()

            return redirect('manage_dictionary')

    return render(request, 'update_dictionary.html', {'term': term_obj})

@login_required
def delete_user(request, user_id):

    # only admin allowed
    if not request.user.is_superuser:
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)

    # prevent admin from deleting himself
    if user.id != request.user.id:
        user.delete()

    return redirect('manage_users')

@login_required
def manage_quiz(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    if request.method == "POST":
        question = request.POST.get('question')
        option1 = request.POST.get('option1')
        option2 = request.POST.get('option2')
        option3 = request.POST.get('option3')

        # prevent empty fields
        if question and option1 and option2 and option3:
            QuizQuestion.objects.create(
                question=question,
                option1=option1,
                option2=option2,
                option3=option3
            )

    questions = QuizQuestion.objects.all()
    return render(request, 'manage_quiz.html', {'questions': questions})

@login_required
def delete_quiz_question(request, question_id):
    if not request.user.is_superuser:
        return redirect('dashboard')

    question = get_object_or_404(QuizQuestion, id=question_id)
    question.delete()

    return redirect('manage_quiz')

@login_required
def update_quiz_question(request, question_id):
    if not request.user.is_superuser:
        return redirect('dashboard')

    question_obj = get_object_or_404(QuizQuestion, id=question_id)

    if request.method == "POST":
        question = request.POST.get('question')
        option1 = request.POST.get('option1')
        option2 = request.POST.get('option2')
        option3 = request.POST.get('option3')

        if question and option1 and option2 and option3:
            question_obj.question = question
            question_obj.option1 = option1
            question_obj.option2 = option2
            question_obj.option3 = option3
            question_obj.save()

            return redirect('manage_quiz')

    return render(request, 'update_quiz.html', {'question': question_obj})