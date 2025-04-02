from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Tema(models.Model):
    """Modelo para temas de personalização."""
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    cores_primarias = models.TextField(help_text="JSON com as cores primárias do tema", default='{"primaria": "#007bff", "secundaria": "#6c757d"}')
    cores_secundarias = models.TextField(help_text="JSON com as cores secundárias do tema", default='{"primaria": "#28a745", "secundaria": "#dc3545"}')
    fonte_principal = models.CharField(max_length=100, default="Roboto")
    fonte_secundaria = models.CharField(max_length=100, default="Open Sans")
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Tema"
        verbose_name_plural = "Temas"
        ordering = ['nome']

class Layout(models.Model):
    """Modelo para layouts de personalização."""
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    estrutura = models.TextField(help_text="JSON com a estrutura do layout", default="{}")
    configuracoes = models.TextField(help_text="JSON com as configurações do layout", default="{}")
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Layout"
        verbose_name_plural = "Layouts"
        ordering = ['nome']

class Widget(models.Model):
    """Modelo para widgets de personalização."""
    TIPOS_WIDGET = [
        ('calendario', 'Calendário'),
        ('notas', 'Notas'),
        ('tarefas', 'Tarefas'),
        ('estatisticas', 'Estatísticas'),
        ('graficos', 'Gráficos'),
    ]

    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS_WIDGET)
    descricao = models.TextField(blank=True)
    configuracoes = models.TextField(help_text="JSON com as configurações do widget", default="{}")
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"

    class Meta:
        verbose_name = "Widget"
        verbose_name_plural = "Widgets"
        ordering = ['nome']

class DashboardUsuario(models.Model):
    """Modelo para o dashboard personalizado do usuário."""
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    layout = models.ForeignKey(Layout, on_delete=models.SET_NULL, null=True, blank=True)
    widgets = models.ManyToManyField(Widget, through='WidgetDashboard')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dashboard de {self.usuario.username}"

    class Meta:
        verbose_name = "Dashboard do Usuário"
        verbose_name_plural = "Dashboards dos Usuários"

class WidgetDashboard(models.Model):
    """Modelo para widgets no dashboard do usuário."""
    dashboard = models.ForeignKey(DashboardUsuario, on_delete=models.CASCADE)
    widget = models.ForeignKey(Widget, on_delete=models.CASCADE)
    posicao_x = models.IntegerField(validators=[MinValueValidator(0)])
    posicao_y = models.IntegerField(validators=[MinValueValidator(0)])
    largura = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    altura = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    configuracoes = models.TextField(help_text="JSON com as configurações específicas do widget no dashboard", default="{}")
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.widget.nome} em {self.dashboard}"

    class Meta:
        verbose_name = "Widget no Dashboard"
        verbose_name_plural = "Widgets no Dashboard"
        ordering = ['posicao_y', 'posicao_x']

class PreferenciaUsuario(models.Model):
    """Modelo para preferências de personalização do usuário."""
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tema = models.ForeignKey(Tema, on_delete=models.SET_NULL, null=True, blank=True)
    layout = models.ForeignKey(Layout, on_delete=models.SET_NULL, null=True, blank=True)
    tamanho_fonte = models.CharField(max_length=10, choices=[
        ('pequeno', 'Pequeno'),
        ('medio', 'Médio'),
        ('grande', 'Grande'),
    ], default='medio')
    alto_contraste = models.BooleanField(default=False)
    reducao_movimento = models.BooleanField(default=False)
    notificacoes_email = models.BooleanField(default=True)
    notificacoes_push = models.BooleanField(default=True)
    notificacoes_som = models.BooleanField(default=True)
    idioma = models.CharField(max_length=10, choices=[
        ('pt-br', 'Português (Brasil)'),
        ('en', 'English'),
        ('es', 'Español'),
    ], default='pt-br')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferências de {self.usuario.username}"

    class Meta:
        verbose_name = "Preferência do Usuário"
        verbose_name_plural = "Preferências dos Usuários"
