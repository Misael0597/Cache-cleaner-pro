"""
cleaner.py
Responsabilidad: Eliminar los archivos de caché de forma segura,
con manejo de errores y reporte detallado por categoría.
"""
from __future__ import annotations

import os
import glob
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import uuid


def resolver_ruta(ruta: str) -> str:
    """Convierte variables de entorno en rutas reales."""
    return os.path.expandvars(ruta)


def limpiar_carpeta(ruta: str) -> tuple[int, int]:
    """
    Elimina todos los archivos dentro de una carpeta sin borrar la carpeta misma.
    Retorna: (bytes_liberados, archivos_eliminados)
    """
    bytes_liberados = 0
    archivos_eliminados = 0

    try:
        for item in Path(ruta).iterdir():
            try:
                if item.is_file():
                    tamano = item.stat().st_size
                    item.unlink()
                    bytes_liberados += tamano
                    archivos_eliminados += 1
                elif item.is_dir():
                    tamano = sum(
                        f.stat().st_size
                        for f in item.rglob("*")
                        if f.is_file()
                    )
                    shutil.rmtree(item)
                    bytes_liberados += tamano
                    archivos_eliminados += 1
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError, FileNotFoundError):
        pass

    return bytes_liberados, archivos_eliminados


def limpiar_dns() -> dict:
    """Ejecuta el comando para limpiar el caché DNS de Windows."""
    try:
        resultado = subprocess.run(
            ["ipconfig", "/flushdns"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
        exito = resultado.returncode == 0
        return {
            "key": "dns_cache",
            "label": "Caché DNS",
            "bytes_freed": 0,
            "files_deleted": 0,
            "status": "success" if exito else "error",
            "reason": None if exito else "command_failed"
        }
    except Exception:  # pylint: disable=broad-exception-caught
        return {
            "key": "dns_cache",
            "label": "Caché DNS",
            "bytes_freed": 0,
            "files_deleted": 0,
            "status": "error",
            "reason": "command_not_available"
        }


def limpiar_categoria(key: str, config: dict) -> dict:
    """Limpia una categoría individual y retorna su reporte."""
    if key == "dns_cache":
        return limpiar_dns()

    total_bytes = 0
    total_archivos = 0
    rutas = config.get("paths", [])

    for ruta_raw in rutas:
        ruta_resuelta = resolver_ruta(ruta_raw)
        rutas_expandidas = glob.glob(ruta_resuelta)

        if not rutas_expandidas:
            rutas_expandidas = [ruta_resuelta]

        for ruta in rutas_expandidas:
            if os.path.exists(ruta):
                bytes_carpeta, archivos_carpeta = limpiar_carpeta(ruta)
                total_bytes += bytes_carpeta
                total_archivos += archivos_carpeta

    return {
        "key": key,
        "label": config.get("label", key),
        "bytes_freed": total_bytes,
        "files_deleted": total_archivos,
        "status": "success",
        "reason": None
    }


def ejecutar_limpieza(categorias: dict, callback=None) -> dict:
    """
    Ejecuta la limpieza completa de todas las categorías activas.
    callback: función opcional que recibe (progreso 0.0-1.0, label)
    """
    inicio = datetime.now()
    resultados = []
    total_bytes = 0
    total_archivos = 0

    categorias_activas = [
        (key, config)
        for key, config in categorias.items()
        if config.get("enabled", True)
    ]

    total = len(categorias_activas)

    for i, (key, config) in enumerate(categorias_activas):
        if callback:
            callback(i / total, config.get("label", key))

        resultado = limpiar_categoria(key, config)
        resultados.append(resultado)

        if resultado["status"] == "success":
            total_bytes += resultado["bytes_freed"]
            total_archivos += resultado["files_deleted"]

    if callback:
        callback(1.0, "Completado")

    duracion = (datetime.now() - inicio).total_seconds()

    return {
        "id": str(uuid.uuid4()),
        "timestamp": inicio.isoformat(),
        "type": "manual",
        "duration_seconds": round(duracion, 2),
        "result": {
            "total_bytes_freed": total_bytes,
            "total_files_deleted": total_archivos,
            "categories_processed": resultados
        }
    }
