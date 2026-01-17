"""Resumen de datos por ciudad."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
from pathlib import Path

print('=' * 60)
print('RESUMEN FINAL - 10 PRINCIPALES CIUDADES DE ESPAÑA')
print('=' * 60)
print('')

total_general = 0
ciudades_stats = []

data_dir = Path('data')
for archivo in sorted(data_dir.glob('*.json')):
    if 'config' in archivo.name or 'api_usage' in archivo.name:
        continue
    
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        registros = data.get('registros', [])
        n = len(registros)
        con_tel = sum(1 for r in registros if r.get('telefono'))
        con_email = sum(1 for r in registros if r.get('email'))
        
        ciudad = archivo.stem.title()
        ciudades_stats.append({
            'ciudad': ciudad,
            'total': n,
            'con_tel': con_tel,
            'con_email': con_email
        })
        total_general += n
    except:
        continue

# Ordenar por total
ciudades_stats.sort(key=lambda x: -x['total'])

print(f"{'Ciudad':<15} {'Total':>8} {'Tel':>8} {'Email':>8}")
print('-' * 45)

for c in ciudades_stats:
    print(f"{c['ciudad']:<15} {c['total']:>8} {c['con_tel']:>8} {c['con_email']:>8}")

print('-' * 45)
print(f"{'TOTAL':<15} {total_general:>8}")
