import os
import json
import csv
import xlsxwriter
from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db import connection
from .models import Backup, Exportacao, ConfiguracaoBackup

class BackupService:
    @staticmethod
    def criar_backup(usuario, tipo='manual', descricao=''):
        """Cria um novo backup"""
        backup = Backup.objects.create(
            usuario=usuario,
            tipo=tipo,
            descricao=descricao
        )
        return backup
    
    @staticmethod
    def executar_backup(backup):
        """Executa o backup e salva o arquivo"""
        try:
            backup.status = 'em_andamento'
            backup.save()
            
            # Criar diretório temporário para o backup
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_backups')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Nome do arquivo de backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(temp_dir, f'backup_{timestamp}.json')
            
            # Coletar dados do banco
            data = {}
            with connection.cursor() as cursor:
                # Lista de tabelas para backup
                tables = [
                    'listas_verificacao_listaverificacao',
                    'listas_verificacao_objetivo',
                    'listas_verificacao_progressoaluno',
                    'listas_verificacao_aprendizagemessencial',
                    'listas_verificacao_comentario',
                    'listas_verificacao_duvida',
                    'listas_verificacao_diarioaprendizagem',
                    'listas_verificacao_meta',
                    'listas_verificacao_prazo',
                ]
                
                for table in tables:
                    cursor.execute(f"SELECT * FROM {table}")
                    columns = [col[0] for col in cursor.description]
                    data[table] = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Salvar dados em arquivo JSON
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Salvar arquivo no modelo
            with open(backup_file, 'rb') as f:
                backup.salvar_arquivo(ContentFile(f.read(), name=f'backup_{timestamp}.json'))
            
            # Limpar arquivo temporário
            os.remove(backup_file)
            
            # Atualizar status
            backup.status = 'concluido'
            backup.data_conclusao = timezone.now()
            backup.save()
            
            return backup
            
        except Exception as e:
            backup.status = 'erro'
            backup.erro = str(e)
            backup.save()
            raise
    
    @staticmethod
    def restaurar_backup(backup):
        """Restaura um backup"""
        try:
            if not backup.arquivo:
                raise ValueError("Arquivo de backup não encontrado")
            
            # Ler dados do backup
            with backup.arquivo.open('r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Restaurar dados
            with connection.cursor() as cursor:
                for table, rows in data.items():
                    if rows:
                        # Criar tabela temporária
                        temp_table = f"temp_{table}"
                        cursor.execute(f"CREATE TEMP TABLE {temp_table} (LIKE {table} INCLUDING ALL)")
                        
                        # Inserir dados
                        columns = list(rows[0].keys())
                        placeholders = ', '.join(['%s'] * len(columns))
                        insert_sql = f"INSERT INTO {temp_table} ({', '.join(columns)}) VALUES ({placeholders})"
                        
                        for row in rows:
                            values = [row[col] for col in columns]
                            cursor.execute(insert_sql, values)
                        
                        # Atualizar dados existentes
                        cursor.execute(f"""
                            UPDATE {table} t
                            SET {', '.join(f"{col} = temp.{col}" for col in columns)}
                            FROM {temp_table} temp
                            WHERE t.id = temp.id
                        """)
                        
                        # Inserir novos registros
                        cursor.execute(f"""
                            INSERT INTO {table}
                            SELECT temp.*
                            FROM {temp_table} temp
                            LEFT JOIN {table} t ON t.id = temp.id
                            WHERE t.id IS NULL
                        """)
            
            return True
            
        except Exception as e:
            raise ValueError(f"Erro ao restaurar backup: {str(e)}")

class ExportacaoService:
    @staticmethod
    def criar_exportacao(usuario, formato, filtros=None, descricao=''):
        """Cria uma nova exportação"""
        exportacao = Exportacao.objects.create(
            usuario=usuario,
            formato=formato,
            filtros=filtros or {},
            descricao=descricao
        )
        return exportacao
    
    @staticmethod
    def executar_exportacao(exportacao):
        """Executa a exportação e salva o arquivo"""
        try:
            exportacao.status = 'em_andamento'
            exportacao.save()
            
            # Criar diretório temporário
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_exportacoes')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Nome do arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'exportacao_{timestamp}'
            
            if exportacao.formato == 'csv':
                arquivo = os.path.join(temp_dir, f'{filename}.csv')
                ExportacaoService._exportar_csv(arquivo, exportacao.filtros)
            elif exportacao.formato == 'excel':
                arquivo = os.path.join(temp_dir, f'{filename}.xlsx')
                ExportacaoService._exportar_excel(arquivo, exportacao.filtros)
            elif exportacao.formato == 'pdf':
                arquivo = os.path.join(temp_dir, f'{filename}.pdf')
                ExportacaoService._exportar_pdf(arquivo, exportacao.filtros)
            else:
                raise ValueError(f"Formato de exportação não suportado: {exportacao.formato}")
            
            # Salvar arquivo no modelo
            with open(arquivo, 'rb') as f:
                exportacao.salvar_arquivo(ContentFile(f.read(), name=os.path.basename(arquivo)))
            
            # Limpar arquivo temporário
            os.remove(arquivo)
            
            # Atualizar status
            exportacao.status = 'concluido'
            exportacao.data_conclusao = timezone.now()
            exportacao.save()
            
            return exportacao
            
        except Exception as e:
            exportacao.status = 'erro'
            exportacao.erro = str(e)
            exportacao.save()
            raise
    
    @staticmethod
    def _exportar_csv(arquivo, filtros):
        """Exporta dados para CSV"""
        with connection.cursor() as cursor:
            # Implementar lógica de exportação CSV
            pass
    
    @staticmethod
    def _exportar_excel(arquivo, filtros):
        """Exporta dados para Excel"""
        workbook = xlsxwriter.Workbook(arquivo)
        # Implementar lógica de exportação Excel
        workbook.close()
    
    @staticmethod
    def _exportar_pdf(arquivo, filtros):
        """Exporta dados para PDF"""
        # Implementar lógica de exportação PDF
        pass 