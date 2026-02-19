from odoo.tests.common import SavepointCase
from odoo.exceptions import UserError

class TestDistributorCheckout(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({"name": "Distribuidor Test"})
        cls.product = cls.env['product.product'].create({
            "name": "Producto Test",
            "type": "product",
            "list_price": 10.0,
        })
        # Carrier de ejemplo (igual que el de data)
        cls.carrier = cls.env['delivery.carrier'].create({
            "name": "Envío gestionado por el distribuidor",
            "delivery_type": "fixed",
            "fixed_price": 0.0,
        })
        # Parametrización
        cls.env['ir.config_parameter'].sudo().set_param("website_dist_checkout.carrier_id", str(cls.carrier.id))
        cls.env['ir.config_parameter'].sudo().set_param("website_dist_checkout.require_label", "1")

        # Stock para poder validar (una unidad)
        stock_loc = cls.env.ref('stock.stock_location_stock')
        cls.env['stock.quant']._update_available_quantity(cls.product, stock_loc, 5.0)

    def test_block_validation_without_label(self):
        so = self.env['sale.order'].create({
            "partner_id": self.partner.id,
            "carrier_id": self.carrier.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
                "price_unit": 10.0,
            })],
        })
        so.action_confirm()
        picking = so.picking_ids.filtered(lambda p: p.picking_type_code == "outgoing")
        self.assertTrue(picking, "Se debe crear un albarán de salida.")
        # Sin etiqueta debe bloquear
        with self.assertRaises(UserError):
            picking.button_validate()

    def test_propagate_fields_to_picking(self):
        so = self.env['sale.order'].create({
            "partner_id": self.partner.id,
            "carrier_id": self.carrier.id,
            "dist_carrier_name": "Dachser",
            "dist_carrier_account": "ACC-123",
            "dist_pickup_slot": "morning",
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
                "price_unit": 10.0,
            })],
        })
        so.action_confirm()
        pick = so.picking_ids.filtered(lambda p: p.picking_type_code == "outgoing")
        self.assertEqual(pick.dist_carrier_name, "Dachser")
        self.assertEqual(pick.dist_carrier_account, "ACC-123")
        self.assertEqual(pick.dist_pickup_slot, "morning")