"""
scanner.py
Responsabilidad: Escanear el dispositivo en busca de archivos de caché
y calcular los tamaños totales de forma segura.
"""
from __future__ import annotations
import os
import glob


def formatear_tamano(data_bytes: int) -> str:
    """Transforma los bytes en un formato legible (KB, MB, GB)."""
    if data_bytes < 1024:
        return f"{data_bytes} Bytes"
    if data_bytes < 1024 * 1024:
        return f"{data_bytes / 1024:.2f} KB"
    if data_bytes < 1024 * 1024 * 1024:
        return f"{data_bytes / (1024 * 1024):.2f} MB"
    return f"{data_bytes / (1024 * 1024 * 1024):.2f} GB"


def escanear_dispositivo(categorias: dict) -> dict:
    """
    Escanea las rutas de las categorías configuradas y calcula
    el tamaño total de los archivos de caché detectados.
    """
    total_bytes = 0
    total_files = 0
    detalles_categorias = {}

    for key, config in categorias.items():
        if not config.get("enabled", True):
            continue

        bytes_categoria = 0
        archivos_categoria = 0
        rutas = config.get("paths", [])

        for ruta_raw in rutas:
            ruta_resuelta = os.path.expandvars(ruta_raw)
            rutas_expandidas = glob.glob(ruta_resuelta)

            if not rutas_expandidas:
                rutas_expandidas = [ruta_resuelta]

            for ruta in rutas_expandidas:
                if os.path.exists(ruta) and os.path.isdir(ruta):
                    try:
                        for root, _, files in os.walk(ruta):
                            for file in files:
                                fp = os.path.join(root, file)
                                if os.path.exists(fp):
                                    bytes_categoria += os.path.getsize(fp)
                                    archivos_categoria += 1
                    except (PermissionError, OSError):
                        continue

        total_bytes += bytes_categoria
        total_files += archivos_categoria
        detalles_categorias[key] = {
            "bytes": bytes_categoria,
            "files": archivos_categoria
        }

    return {
        "total_bytes": total_bytes,
        "total_files": total_files,
        "categories": detalles_categorias
    }
