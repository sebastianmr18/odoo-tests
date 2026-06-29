
# Evidencia de Ejecución - Pruebas Unitarias Odoo

**Módulo probado:** `odoo_unit_tests`
**Fecha de ejecución:** 2026-06-28
**Base de datos:** `odoo_dev`
**Versión de Odoo:** 19.0
**Host/BD:** `odoo@127.0.0.1:5432`

---

## 1. Resumen General de la Ejecución

La suite de pruebas unitarias se ejecutó de forma automatizada y secuencial sobre el módulo de ventas y contabilidad.

**Resultado final (extraído del log):**

> `2026-06-28 17:40:32,407 INFO odoo_dev odoo.tests.result: 0 failed, 0 error(s) of 12 tests`

**Conclusión del resumen:**
✅ **12 pruebas ejecutadas** | ✅ **0 fallas** | ✅ **0 errores de sistema** | ✅ **Tasa de éxito: 100%**

---

## 2. Trazabilidad de Ejecución por Caso de Prueba (12 casos)

La siguiente tabla correlaciona el ID del caso (`CPU-01` a `CPU-12`), el nombre técnico del método ejecutado y la hora exacta de inicio registrada en el log.

| ID Caso | Método / Prueba Ejecutada                      | Hora de Inicio |  Estado  |
| :-----: | :---------------------------------------------- | :------------: | :------: |
| CPU-01 | `test_calcular_linea_con_impuesto`            |  17:40:24,636  | ✅ PASÓ |
| CPU-02 | `test_calcular_subtotal_linea_cotizacion`     |  17:40:25,011  | ✅ PASÓ |
| CPU-03 | `test_calcular_total_cotizacion_con_impuesto` |  17:40:25,247  | ✅ PASÓ |
| CPU-04 | `test_calcular_total_cotizacion_sin_impuesto` |  17:40:25,498  | ✅ PASÓ |
| CPU-05 | `test_confirmar_cotizacion_valida`            |  17:40:25,745  | ✅ PASÓ |
| CPU-06 | `test_confirmar_cotizacion_ya_confirmada`     |  17:40:26,012  | ✅ PASÓ |
| CPU-07 | `test_crear_factura_desde_orden_confirmada`   |  17:40:26,326  | ✅ PASÓ |
| CPU-08 | `test_crear_producto_consumible_valido`       |  17:40:27,774  | ✅ PASÓ |
| CPU-09 | `test_crear_producto_servicio_valido`         |  17:40:27,996  | ✅ PASÓ |
| CPU-10 | `test_preparar_datos_factura_desde_orden`     |  17:40:28,216  | ✅ PASÓ |
| CPU-11 | `test_publicar_factura_sin_lineas`            |  17:40:28,478  | ✅ PASÓ |
| CPU-12 | `test_publicar_factura_valida`                |  17:40:28,770  | ✅ PASÓ |

**Nota:** Las marcas de tiempo muestran una ejecución continuada y sin pausas entre pruebas (la diferencia promedio entre inicios es de milisegundos), lo que evidencia que no hubo bloqueos, congelamientos ni intervenciones manuales durante el ciclo.

---

## 3. Log Crudo Depurado (Evidencia en Anexo Técnico)

A continuación se presenta el extracto literal del log del servidor, filtrado para mostrar únicamente el inicio de cada una de las 12 pruebas y el veredicto final. Se han omitido líneas de advertencia de configuración, carga de módulos genéricos y mensajes de apagado para facilitar la lectura técnica.

```text
2026-06-28 17:40:14,918 INFO ? odoo: Odoo version 19.0
2026-06-28 17:40:14,918 INFO ? odoo: database: odoo@127.0.0.1:5432

[INICIO DE BATERÍA DE PRUEBAS]
2026-06-28 17:40:24,636 INFO odoo_dev odoo.addons.odoo_unit_tests.tests.test_unit_sales_accounting: Starting TestUnitSalesAccounting.test_calcular_linea_con_impuesto ...
2026-06-28 17:40:25,011 INFO odoo_dev odoo.addons.odoo_unit_tests.tests.test_unit_sales_accounting: Starting TestUnitSalesAccounting.test_calcular_subtotal_linea_cotizacion ...
2026-06-28 17:40:25,247 INFO odoo_dev odoo.addons.odoo_unit_tests.tests.test_unit_sales_accounting: Starting TestUnitSalesAccounting.test_calcular_total_cotizacion_con_impuesto ...
2026-06-28 17:40:25,498 INFO odoo_dev odoo.addons.odoo_unit_tests.tests.test_unit_sales_accounting: Starting TestUnitSalesAccounting.test_calcular_total_cotizacion_sin_impuesto ...
2026-06-28 17:40:25,745 INFO odoo_dev odoo.addons.odoo_unit_tests.tests.test_unit_sales_accounting: Starting TestUnitSalesAccounting.test_confirmar_cotizacion_valida ...
2026-06-28 17:40:26,012 INFO odoo_dev odoo.addons.odoo_unit_tests.tests.test_unit_sales_accounting: Starting TestUnitSalesAccounting.test_confirmar_cotizacion_ya_confirmada ...
2026-06-28 17:40:26,326 INFO odoo_dev odoo.addons.odoo_unit_tests.tests.test_unit_sales_accounting: Starting TestUnitSalesAccounting.test_crear_factura_desde_orden_confirmada ...
2026-06-28 17:40:27,774 INFO odoo_dev odoo.addons.odoo_unit_tests.tests.test_unit_sales_accounting: Starting TestUnitSalesAccounting.test_crear_producto_consumible_valido ...
2026-06-28 17:40:27,996 INFO odoo_dev odoo.addons.odoo_unit_tests.tests.test_unit_sales_accounting: Starting TestUnitSalesAccounting.test_crear_producto_servicio_valido ...
2026-06-28 17:40:28,216 INFO odoo_dev odoo.addons.odoo_unit_tests.tests.test_unit_sales_accounting: Starting TestUnitSalesAccounting.test_preparar_datos_factura_desde_orden ...
2026-06-28 17:40:28,478 INFO odoo_dev odoo.addons.odoo_unit_tests.tests.test_unit_sales_accounting: Starting TestUnitSalesAccounting.test_publicar_factura_sin_lineas ...
2026-06-28 17:40:28,770 INFO odoo_dev odoo.addons.odoo_unit_tests.tests.test_unit_sales_accounting: Starting TestUnitSalesAccounting.test_publicar_factura_valida ...

[VEREDICTO FINAL DE LA BATERÍA]
2026-06-28 17:40:32,407 INFO odoo_dev odoo.tests.result: 0 failed, 0 error(s) of 12 tests when loading database 'odoo_dev'
```
