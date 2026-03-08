from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import DiaryNote

@login_required
def investment_diary(request):
    notes = DiaryNote.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'investment_diary.html', {'notes': notes})

@login_required
def add_note(request):
    if request.method == 'POST':
        DiaryNote.objects.create(user=request.user, title=request.POST['title'], content=request.POST['content'])
        return redirect('investment_diary')
    return redirect('investment_diary')

@login_required
def edit_note(request, note_id):
    note = get_object_or_404(DiaryNote, id=note_id, user=request.user)
    if request.method == 'POST':
        note.title = request.POST['title']
        note.content = request.POST['content']
        note.save()
        return redirect('investment_diary')
    return render(request, 'edit_note.html', {'note': note})

@login_required
def delete_note(request, note_id):
    note = get_object_or_404(DiaryNote, id=note_id, user=request.user)
    note.delete()
    return redirect('investment_diary')