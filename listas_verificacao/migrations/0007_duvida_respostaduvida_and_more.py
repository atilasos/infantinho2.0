# Generated by Django 5.1.7 on 2025-04-02 09:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listas_verificacao', '0006_alter_avaliacaoaprendizagem_estado'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Duvida',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200)),
                ('descricao', models.TextField()),
                ('categoria', models.CharField(choices=[('conceito', 'Conceito'), ('exercicio', 'Exercício'), ('recurso', 'Recurso'), ('outro', 'Outro')], default='conceito', max_length=20)),
                ('prioridade', models.CharField(choices=[('baixa', 'Baixa'), ('media', 'Média'), ('alta', 'Alta'), ('urgente', 'Urgente')], default='media', max_length=20)),
                ('estado', models.CharField(choices=[('aberta', 'Aberta'), ('em_andamento', 'Em Andamento'), ('respondida', 'Respondida'), ('fechada', 'Fechada')], default='aberta', max_length=20)),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('data_atualizacao', models.DateTimeField(auto_now=True)),
                ('data_resposta', models.DateTimeField(blank=True, null=True)),
                ('aprendizagem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='duvidas', to='listas_verificacao.aprendizagemessencial')),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='duvidas_criadas', to=settings.AUTH_USER_MODEL)),
                ('respondido_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='duvidas_respondidas', to=settings.AUTH_USER_MODEL)),
                ('turma', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='duvidas', to='listas_verificacao.turma')),
            ],
            options={
                'verbose_name': 'Dúvida',
                'verbose_name_plural': 'Dúvidas',
                'ordering': ['-data_criacao'],
            },
        ),
        migrations.CreateModel(
            name='RespostaDuvida',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto', models.TextField()),
                ('anexos', models.FileField(blank=True, null=True, upload_to='anexos_duvidas/')),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('data_atualizacao', models.DateTimeField(auto_now=True)),
                ('melhor_resposta', models.BooleanField(default=False)),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='respostas_duvidas', to=settings.AUTH_USER_MODEL)),
                ('duvida', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='respostas', to='listas_verificacao.duvida')),
            ],
            options={
                'verbose_name': 'Resposta de Dúvida',
                'verbose_name_plural': 'Respostas de Dúvidas',
                'ordering': ['-melhor_resposta', 'data_criacao'],
            },
        ),
        migrations.AddIndex(
            model_name='duvida',
            index=models.Index(fields=['estado', 'data_criacao'], name='listas_veri_estado_1cd2c8_idx'),
        ),
        migrations.AddIndex(
            model_name='duvida',
            index=models.Index(fields=['categoria', 'prioridade'], name='listas_veri_categor_cfc639_idx'),
        ),
    ]
