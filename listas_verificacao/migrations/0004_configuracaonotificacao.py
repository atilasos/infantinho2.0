# Generated by Django 5.1.7 on 2025-03-30 23:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listas_verificacao', '0003_notificacao'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracaoNotificacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notif_baixo_progresso', models.BooleanField(default=True, verbose_name='Alertas de Baixo Progresso')),
                ('notif_prazos', models.BooleanField(default=True, verbose_name='Notificações de Prazos')),
                ('notif_duvidas', models.BooleanField(default=True, verbose_name='Notificações de Dúvidas')),
                ('notif_conquistas', models.BooleanField(default=True, verbose_name='Notificações de Conquistas')),
                ('notif_feedback', models.BooleanField(default=True, verbose_name='Notificações de Feedback')),
                ('receber_emails', models.BooleanField(default=True, verbose_name='Receber Emails')),
                ('frequencia_emails', models.CharField(choices=[('imediato', 'Imediatamente'), ('diario', 'Resumo Diário'), ('semanal', 'Resumo Semanal'), ('desativado', 'Desativado')], default='imediato', max_length=20, verbose_name='Frequência de Emails')),
                ('horario_inicio', models.TimeField(default='08:00', verbose_name='Horário de Início')),
                ('horario_fim', models.TimeField(default='18:00', verbose_name='Horário de Fim')),
                ('dias_semana', models.CharField(default='1,2,3,4,5', help_text='Dias da semana (1-7, separados por vírgula. 1=Segunda, 7=Domingo)', max_length=20, verbose_name='Dias da Semana')),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='config_notificacoes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Configuração de Notificação',
                'verbose_name_plural': 'Configurações de Notificações',
            },
        ),
    ]
