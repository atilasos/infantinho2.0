from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json

def cache_key_generator(*args, **kwargs):
    """Gera uma chave única para o cache baseada nos argumentos da função."""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def cache_response(timeout=300, prefix=''):
    """Decorator para cachear o resultado de uma função."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gera a chave do cache
            cache_key = f"{prefix}:{cache_key_generator(*args, **kwargs)}"
            
            # Tenta obter o resultado do cache
            result = cache.get(cache_key)
            
            if result is None:
                # Se não estiver em cache, executa a função
                result = func(*args, **kwargs)
                
                # Armazena o resultado no cache
                cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator

def clear_cache_pattern(pattern):
    """Limpa todas as chaves de cache que correspondem ao padrão."""
    keys = cache.keys(pattern)
    if keys:
        cache.delete_many(keys)

def cache_model_instance(model, instance_id, timeout=300):
    """Cachea uma instância de modelo."""
    cache_key = f"{model.__name__}:{instance_id}"
    instance = cache.get(cache_key)
    
    if instance is None:
        instance = model.objects.get(id=instance_id)
        cache.set(cache_key, instance, timeout)
    
    return instance

def invalidate_model_cache(model, instance_id):
    """Invalida o cache de uma instância de modelo."""
    cache_key = f"{model.__name__}:{instance_id}"
    cache.delete(cache_key)

def cache_query_set(queryset, timeout=300, prefix=''):
    """Cachea o resultado de uma queryset."""
    cache_key = f"{prefix}:{cache_key_generator(str(queryset.query))}"
    result = cache.get(cache_key)
    
    if result is None:
        result = list(queryset)
        cache.set(cache_key, result, timeout)
    
    return result

def bulk_cache_model_instances(model, instance_ids, timeout=300):
    """Cachea múltiplas instâncias de modelo de uma vez."""
    cache_keys = [f"{model.__name__}:{id}" for id in instance_ids]
    instances = cache.get_many(cache_keys)
    
    missing_ids = [id for id in instance_ids if f"{model.__name__}:{id}" not in instances]
    
    if missing_ids:
        missing_instances = model.objects.filter(id__in=missing_ids)
        for instance in missing_instances:
            cache_key = f"{model.__name__}:{instance.id}"
            instances[cache_key] = instance
            cache.set(cache_key, instance, timeout)
    
    return [instances.get(f"{model.__name__}:{id}") for id in instance_ids] 