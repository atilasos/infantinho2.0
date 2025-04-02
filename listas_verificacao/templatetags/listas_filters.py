from django import template
from ..models import ProgressoAluno, ListaVerificacao

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    return dictionary.get(key)

@register.filter
def filter_validados(status_map, dominio):
    """Count the number of validated objectives for a given domain"""
    return sum(1 for status in status_map.values() 
              if status.objetivo.dominio == dominio and status.status == 'validado')

@register.filter
def div(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def progresso_geral(aluno):
    """Calculate the overall progress for a student"""
    # Get all lists the student is enrolled in
    listas = ListaVerificacao.objects.filter(turma__alunos=aluno)
    
    if not listas.exists():
        return 0
    
    total_aprendizagens = 0
    total_concluidas = 0
    
    for lista in listas:
        total_aprendizagens += lista.aprendizagens.count()
        total_concluidas += ProgressoAluno.objects.filter(
            aluno=aluno,
            lista_verificacao=lista,
            estado='concluido'
        ).count()
    
    if total_aprendizagens == 0:
        return 0
        
    return round((total_concluidas / total_aprendizagens) * 100, 1) 