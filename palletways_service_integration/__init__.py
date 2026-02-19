from . import models

# Hook desactivado temporalmente para evitar errores de transacción SQL
# def post_init_hook(env):
#     """Hook simplificado sin operaciones complejas"""
#     import logging
#     _logger = logging.getLogger(__name__)
#     
#     try:
#         _logger.info("Módulo Palletways instalado correctamente")
#         # No hacer operaciones de base de datos aquí
#         pass
#     except Exception as e:
#         _logger.error(f"Error en post_init_hook: {e}")
#         # No re-lanzar la excepción
#         pass
