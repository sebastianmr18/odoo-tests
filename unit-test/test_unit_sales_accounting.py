from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("standard", "at_install")
class TestUnitSalesAccounting(TransactionCase):
    """
    Pruebas unitarias estilo XUnit sobre Odoo ERP & CRM Community.

    Técnicas de caja blanca aplicadas:
    - Cobertura de caminos básicos.
    - Cobertura de decisiones.
    - Cobertura de condiciones múltiples.
    """

    def setUp(self):
        super().setUp()

        self.Product = self.env["product.product"]
        self.Partner = self.env["res.partner"]
        self.SaleOrder = self.env["sale.order"]
        self.AccountMove = self.env["account.move"]
        self.AccountAccount = self.env["account.account"]
        self.AccountJournal = self.env["account.journal"]
        self.AccountTax = self.env["account.tax"]

        self.company = self.env.company

        self.partner = self.Partner.create({
            "name": "Cliente Unitario Odoo",
            "email": "cliente.unitario@test.com",
        })

        self.income_account = self._obtener_o_crear_cuenta(
            account_type="income",
            code="UTREV001",
            name="Unit Test Revenue Account",
        )

        self.receivable_account = self._obtener_o_crear_cuenta(
            account_type="asset_receivable",
            code="UTREC001",
            name="Unit Test Receivable Account",
        )

        self.payable_account = self._obtener_o_crear_cuenta(
            account_type="liability_payable",
            code="UTPAY001",
            name="Unit Test Payable Account",
        )

        self.partner.write({
            "property_account_receivable_id": self.receivable_account.id,
            "property_account_payable_id": self.payable_account.id,
        })

        self.sale_journal = self._obtener_o_crear_diario_ventas()

        self.tax_15 = self.AccountTax.create({
            "name": "IVA Unitario 15%",
            "amount": 15,
            "amount_type": "percent",
            "type_tax_use": "sale",
            "company_id": self.company.id,
        })

        self.product_service = self._crear_producto(
            name="Servicio Unitario",
            product_type="service",
            price=100.00,
        )

        self.product_consumible = self._crear_producto(
            name="Producto Consumible Unitario",
            product_type="consu",
            price=200.00,
        )

    def _obtener_o_crear_cuenta(self, account_type, code, name):
        domain = [
            ("account_type", "=", account_type),
        ]

        # En Odoo 19 puede existir company_ids o company_id, según el modelo instalado
        if "company_ids" in self.AccountAccount._fields:
            domain.append(("company_ids", "in", [self.company.id]))
        elif "company_id" in self.AccountAccount._fields:
            domain.append(("company_id", "=", self.company.id))

        # En algunas versiones existe deprecated, pero en Odoo 19 no siempre está
        if "deprecated" in self.AccountAccount._fields:
            domain.append(("deprecated", "=", False))

        account = self.AccountAccount.search(domain, limit=1)

        if account:
            return account

        vals = {
            "name": name,
            "code": code,
            "account_type": account_type,
        }

        if "company_ids" in self.AccountAccount._fields:
            vals["company_ids"] = [(6, 0, [self.company.id])]
        elif "company_id" in self.AccountAccount._fields:
            vals["company_id"] = self.company.id

        return self.AccountAccount.create(vals)

    def _obtener_o_crear_diario_ventas(self):
        journal = self.AccountJournal.search([
            ("type", "=", "sale"),
            ("company_id", "=", self.company.id),
        ], limit=1)

        if journal:
            return journal

        vals = {
            "name": "Diario Ventas Unitario",
            "code": "UTSL",
            "type": "sale",
            "company_id": self.company.id,
        }

        if "default_account_id" in self.AccountJournal._fields:
            vals["default_account_id"] = self.income_account.id

        return self.AccountJournal.create(vals)

    def _campo_tipo_producto(self):
        if "type" in self.Product._fields:
            return "type"

        if "detailed_type" in self.Product._fields:
            return "detailed_type"

        return None

    def _crear_producto(self, name, product_type, price):
        vals = {
            "name": name,
            "sale_ok": True,
            "purchase_ok": False,
            "list_price": price,
            "standard_price": price / 2,
        }

        campo_tipo = self._campo_tipo_producto()

        if campo_tipo:
            vals[campo_tipo] = product_type

        if "invoice_policy" in self.Product._fields:
            vals["invoice_policy"] = "order"

        return self.Product.create(vals)

    def _campo_impuesto_linea_venta(self):
        SaleOrderLine = self.env["sale.order.line"]

        if "tax_ids" in SaleOrderLine._fields:
            return "tax_ids"

        return "tax_id"

    def _crear_orden_venta(self, product, quantity=1, price=100.00, tax=None):
        campo_impuesto = self._campo_impuesto_linea_venta()

        line_vals = {
            "product_id": product.id,
            "product_uom_qty": quantity,
            "price_unit": price,
        }

        if tax:
            line_vals[campo_impuesto] = [(6, 0, [tax.id])]
        else:
            line_vals[campo_impuesto] = [(6, 0, [])]

        return self.SaleOrder.create({
            "partner_id": self.partner.id,
            "order_line": [(0, 0, line_vals)],
        })

    def _crear_factura_borrador(self, con_lineas=True):
        vals = {
            "move_type": "out_invoice",
            "partner_id": self.partner.id,
            "journal_id": self.sale_journal.id,
            "invoice_date": fields.Date.today(),
        }

        if con_lineas:
            vals["invoice_line_ids"] = [(0, 0, {
                "product_id": self.product_service.id,
                "name": "Línea factura unitaria",
                "quantity": 1,
                "price_unit": 100.00,
                "account_id": self.income_account.id,
            })]

        return self.AccountMove.create(vals)

    # CPU-01
    def test_crear_producto_servicio_valido(self):
        producto = self._crear_producto(
            name="CPU-01 Servicio válido",
            product_type="service",
            price=150.00,
        )

        self.assertTrue(producto.id)
        self.assertEqual(producto.name, "CPU-01 Servicio válido")
        self.assertTrue(producto.sale_ok)
        self.assertAlmostEqual(producto.list_price, 150.00, places=2)

    # CPU-02
    def test_crear_producto_consumible_valido(self):
        producto = self._crear_producto(
            name="CPU-02 Producto consumible válido",
            product_type="consu",
            price=250.00,
        )

        self.assertTrue(producto.id)
        self.assertEqual(producto.name, "CPU-02 Producto consumible válido")
        self.assertTrue(producto.sale_ok)
        self.assertAlmostEqual(producto.list_price, 250.00, places=2)

    # CPU-03
    def test_calcular_subtotal_linea_cotizacion(self):
        orden = self._crear_orden_venta(
            product=self.product_service,
            quantity=2,
            price=100.00,
            tax=None,
        )

        linea = orden.order_line[0]

        self.assertAlmostEqual(linea.price_subtotal, 200.00, places=2)

    # CPU-04
    def test_calcular_linea_con_impuesto(self):
        orden = self._crear_orden_venta(
            product=self.product_service,
            quantity=2,
            price=100.00,
            tax=self.tax_15,
        )

        linea = orden.order_line[0]

        self.assertAlmostEqual(linea.price_subtotal, 200.00, places=2)
        self.assertAlmostEqual(linea.price_tax, 30.00, places=2)
        self.assertAlmostEqual(linea.price_total, 230.00, places=2)

    # CPU-05
    def test_calcular_total_cotizacion_sin_impuesto(self):
        orden = self._crear_orden_venta(
            product=self.product_service,
            quantity=3,
            price=100.00,
            tax=None,
        )

        if hasattr(orden, "_compute_amounts"):
            orden._compute_amounts()

        self.assertAlmostEqual(orden.amount_untaxed, 300.00, places=2)
        self.assertAlmostEqual(orden.amount_tax, 0.00, places=2)
        self.assertAlmostEqual(orden.amount_total, 300.00, places=2)

    # CPU-06
    def test_calcular_total_cotizacion_con_impuesto(self):
        orden = self._crear_orden_venta(
            product=self.product_service,
            quantity=2,
            price=100.00,
            tax=self.tax_15,
        )

        if hasattr(orden, "_compute_amounts"):
            orden._compute_amounts()

        self.assertAlmostEqual(orden.amount_untaxed, 200.00, places=2)
        self.assertAlmostEqual(orden.amount_tax, 30.00, places=2)
        self.assertAlmostEqual(orden.amount_total, 230.00, places=2)

    # CPU-07
    def test_confirmar_cotizacion_valida(self):
        orden = self._crear_orden_venta(
            product=self.product_service,
            quantity=1,
            price=100.00,
            tax=None,
        )

        self.assertIn(orden.state, ["draft", "sent"])

        orden.action_confirm()

        self.assertEqual(orden.state, "sale")

    # CPU-08
    def test_confirmar_cotizacion_ya_confirmada(self):
        orden = self._crear_orden_venta(
            product=self.product_service,
            quantity=1,
            price=100.00,
            tax=None,
        )

        orden.action_confirm()
        self.assertEqual(orden.state, "sale")

        with self.assertRaises(UserError):
            orden.action_confirm()

        self.assertEqual(orden.state, "sale")

    # CPU-09
    def test_preparar_datos_factura_desde_orden(self):
        orden = self._crear_orden_venta(
            product=self.product_service,
            quantity=1,
            price=100.00,
            tax=None,
        )

        orden.action_confirm()

        datos_factura = orden._prepare_invoice()

        self.assertEqual(datos_factura["partner_id"], self.partner.id)
        self.assertEqual(datos_factura["move_type"], "out_invoice")
        self.assertIn("invoice_origin", datos_factura)

    # CPU-10
    def test_crear_factura_desde_orden_confirmada(self):
        orden = self._crear_orden_venta(
            product=self.product_service,
            quantity=1,
            price=100.00,
            tax=None,
        )

        orden.action_confirm()

        facturas = orden._create_invoices()

        self.assertTrue(facturas)
        self.assertEqual(facturas[0].move_type, "out_invoice")
        self.assertEqual(facturas[0].partner_id.id, self.partner.id)

    # CPU-11
    def test_publicar_factura_valida(self):
        factura = self._crear_factura_borrador(con_lineas=True)

        self.assertEqual(factura.state, "draft")

        factura.action_post()

        self.assertEqual(factura.state, "posted")

    # CPU-12
    def test_publicar_factura_sin_lineas(self):
        factura = self._crear_factura_borrador(con_lineas=False)

        self.assertEqual(factura.state, "draft")

        try:
            factura.action_post()
        except Exception:
            self.assertEqual(factura.state, "draft")
        else:
            self.assertEqual(
                factura.state,
                "draft",
                "La factura sin líneas no debería publicarse."
            )