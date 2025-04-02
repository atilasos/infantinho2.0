from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Tema, Layout, Widget, PreferenciaUsuario
from .forms import TemaForm, LayoutForm, WidgetForm, PreferenciaUsuarioForm

@login_required
def lista_temas(request):
    """Lista todos os temas disponíveis."""
    temas = Tema.objects.all()
    return render(request, 'personalizacao/lista_temas.html', {'temas': temas})

@login_required
def criar_tema(request):
    """Cria um novo tema."""
    if request.method == 'POST':
        form = TemaForm(request.POST)
        if form.is_valid():
            tema = form.save()
            messages.success(request, 'Tema criado com sucesso!')
            return redirect('personalizacao:lista_temas')
    else:
        form = TemaForm()
    return render(request, 'personalizacao/form_tema.html', {'form': form})

@login_required
def editar_tema(request, tema_id):
    """Edita um tema existente."""
    tema = get_object_or_404(Tema, id=tema_id)
    if request.method == 'POST':
        form = TemaForm(request.POST, instance=tema)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tema atualizado com sucesso!')
            return redirect('personalizacao:lista_temas')
    else:
        form = TemaForm(instance=tema)
    return render(request, 'personalizacao/form_tema.html', {'form': form, 'tema': tema})

@login_required
def excluir_tema(request, tema_id):
    """Exclui um tema."""
    tema = get_object_or_404(Tema, id=tema_id)
    if request.method == 'POST':
        tema.delete()
        messages.success(request, 'Tema excluído com sucesso!')
        return redirect('personalizacao:lista_temas')
    return render(request, 'personalizacao/confirmar_exclusao.html', {'objeto': tema})

@login_required
def lista_layouts(request):
    """Lista todos os layouts disponíveis."""
    layouts = Layout.objects.all()
    return render(request, 'personalizacao/lista_layouts.html', {'layouts': layouts})

@login_required
def criar_layout(request):
    """Cria um novo layout."""
    if request.method == 'POST':
        form = LayoutForm(request.POST)
        if form.is_valid():
            layout = form.save()
            messages.success(request, 'Layout criado com sucesso!')
            return redirect('personalizacao:lista_layouts')
    else:
        form = LayoutForm()
    return render(request, 'personalizacao/form_layout.html', {'form': form})

@login_required
def editar_layout(request, layout_id):
    """Edita um layout existente."""
    layout = get_object_or_404(Layout, id=layout_id)
    if request.method == 'POST':
        form = LayoutForm(request.POST, instance=layout)
        if form.is_valid():
            form.save()
            messages.success(request, 'Layout atualizado com sucesso!')
            return redirect('personalizacao:lista_layouts')
    else:
        form = LayoutForm(instance=layout)
    return render(request, 'personalizacao/form_layout.html', {'form': form, 'layout': layout})

@login_required
def excluir_layout(request, layout_id):
    """Exclui um layout."""
    layout = get_object_or_404(Layout, id=layout_id)
    if request.method == 'POST':
        layout.delete()
        messages.success(request, 'Layout excluído com sucesso!')
        return redirect('personalizacao:lista_layouts')
    return render(request, 'personalizacao/confirmar_exclusao.html', {'objeto': layout})

@login_required
def lista_widgets(request):
    """Lista todos os widgets disponíveis."""
    widgets = Widget.objects.all()
    return render(request, 'personalizacao/lista_widgets.html', {'widgets': widgets})

@login_required
def criar_widget(request):
    """Cria um novo widget."""
    if request.method == 'POST':
        form = WidgetForm(request.POST)
        if form.is_valid():
            widget = form.save()
            messages.success(request, 'Widget criado com sucesso!')
            return redirect('personalizacao:lista_widgets')
    else:
        form = WidgetForm()
    return render(request, 'personalizacao/form_widget.html', {'form': form})

@login_required
def editar_widget(request, widget_id):
    """Edita um widget existente."""
    widget = get_object_or_404(Widget, id=widget_id)
    if request.method == 'POST':
        form = WidgetForm(request.POST, instance=widget)
        if form.is_valid():
            form.save()
            messages.success(request, 'Widget atualizado com sucesso!')
            return redirect('personalizacao:lista_widgets')
    else:
        form = WidgetForm(instance=widget)
    return render(request, 'personalizacao/form_widget.html', {'form': form, 'widget': widget})

@login_required
def excluir_widget(request, widget_id):
    """Exclui um widget."""
    widget = get_object_or_404(Widget, id=widget_id)
    if request.method == 'POST':
        widget.delete()
        messages.success(request, 'Widget excluído com sucesso!')
        return redirect('personalizacao:lista_widgets')
    return render(request, 'personalizacao/confirmar_exclusao.html', {'objeto': widget})

@login_required
def preferencias_usuario(request):
    """Gerencia as preferências do usuário."""
    try:
        preferencias = PreferenciaUsuario.objects.get(usuario=request.user)
    except PreferenciaUsuario.DoesNotExist:
        preferencias = PreferenciaUsuario(usuario=request.user)
    
    if request.method == 'POST':
        form = PreferenciaUsuarioForm(request.POST, instance=preferencias)
        if form.is_valid():
            form.save()
            messages.success(request, 'Preferências atualizadas com sucesso!')
            return redirect('personalizacao:preferencias_usuario')
    else:
        form = PreferenciaUsuarioForm(instance=preferencias)
    
    return render(request, 'personalizacao/preferencias_usuario.html', {'form': form})
