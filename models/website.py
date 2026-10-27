import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain


class Website(models.Model):
    _inherit = 'website'

    is_shop = fields.Boolean(
        string="Is a Shop",
        help="Tick this box to manage this website as an online shop in Script Shop Management.",
    )
    local_shop_id = fields.Many2one(
        'pos.config',
        string="Linked Local Shop",
        domain="[('is_shop', '=', True), ('company_id', '=', company_id)]",
        index=True,
        help="Local shop whose image, destination shop and stock are shared with this website. "
             "Leave empty to manage the website as a shop of its own.",
    )
    shop_image = fields.Image(
        string="Shop Image",
        max_width=512,
        max_height=512,
        compute='_compute_shop_image',
        store=True,
        readonly=False,
        help="Image of the online shop. When the website is linked to a local shop, "
             "the image is loaded from it.",
    )
    destination_shop_id = fields.Many2one(
        'pos.config',
        string="Destination Shop",
        compute='_compute_destination_shop_id',
        store=True,
        help="Destination shop of the website: the linked local shop.",
    )
    own_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Own Warehouse",
        copy=False,
        readonly=True,
        ondelete='set null',
        help="Warehouse created automatically for a website that is a shop of its own.",
    )
    warehouse_id = fields.Many2one(
        compute='_compute_warehouse_id',
        store=True,
        readonly=False,
    )
    logo = fields.Binary(
        compute='_compute_logo',
        store=True,
        readonly=False,
    )

    _local_shop_uniq = models.Constraint(
        'UNIQUE(local_shop_id)',
        "A local shop can only be linked to one website.",
    )

    # ------------------------------------------------------------------ computes

    @api.depends('local_shop_id.shop_image')
    def _compute_shop_image(self):
        """A website linked to a local shop loads its image; otherwise it keeps its own."""
        for website in self:
            if website.local_shop_id:
                website.shop_image = website.local_shop_id.shop_image

    @api.depends('local_shop_id', 'shop_image')
    def _compute_logo(self):
        """A website linked to a local shop takes the image of the shop as its logo."""
        for website in self:
            if website.local_shop_id and website.shop_image:
                website.logo = website.shop_image

    @api.depends('local_shop_id')
    def _compute_destination_shop_id(self):
        for website in self:
            website.destination_shop_id = website.local_shop_id

    @api.depends('local_shop_id.picking_type_id.warehouse_id', 'own_warehouse_id')
    def _compute_warehouse_id(self):
        """Linked: the stock of the local shop. Not linked: the website's own warehouse."""
        for website in self:
            if website.local_shop_id:
                website.warehouse_id = website.local_shop_id.picking_type_id.warehouse_id
            elif website.own_warehouse_id:
                website.warehouse_id = website.own_warehouse_id

    # ----------------------------------------------------------------- constraints

    @api.constrains('local_shop_id', 'is_shop', 'company_id')
    def _check_local_shop(self):
        for website in self.filtered('local_shop_id'):
            if not website.is_shop:
                raise ValidationError(_("A website linked to a local shop must be flagged as a shop."))
            if website.local_shop_id.company_id != website.company_id:
                raise ValidationError(_(
                    "The shop %(shop)s does not belong to the company %(company)s.",
                    shop=website.local_shop_id.display_name,
                    company=website.company_id.display_name,
                ))

    @api.constrains('is_shop', 'local_shop_id', 'warehouse_id')
    def _check_own_warehouse(self):
        """The warehouse of an online shop of its own belongs to that shop only."""
        for website in self.filtered(lambda w: w.is_shop and not w.local_shop_id and w.warehouse_id):
            owner = self.env['pos.config'].sudo().search([
                ('is_shop', '=', True),
                ('picking_type_id.warehouse_id', '=', website.warehouse_id.id),
            ], limit=1) or self.sudo().search([
                ('is_shop', '=', True),
                ('local_shop_id', '=', False),
                ('warehouse_id', '=', website.warehouse_id.id),
                ('id', '!=', website.id),
            ], limit=1)
            if owner:
                raise ValidationError(_(
                    "The warehouse %(warehouse)s is already the stock of the shop %(shop)s. "
                    "A warehouse can only belong to one shop: choose another warehouse.",
                    warehouse=website.warehouse_id.display_name,
                    shop=owner.display_name,
                ))

    # ------------------------------------------------------- own warehouse creation

    @api.model_create_multi
    def create(self, vals_list):
        websites = super().create(vals_list)
        websites.filtered('local_shop_id')._compute_logo()  # the default logo is given at creation
        websites._ensure_own_warehouse()
        return websites

    def write(self, vals):
        result = super().write(vals)
        if 'is_shop' in vals or 'local_shop_id' in vals:
            self._ensure_own_warehouse()
        return result

    def _ensure_own_warehouse(self):
        """Create the warehouse of the websites that are shops of their own."""
        for website in self.filtered(lambda w: w.is_shop and not w.local_shop_id and not w.own_warehouse_id):
            warehouse = self.env['stock.warehouse'].sudo().create({
                'name': website._get_own_warehouse_name(),
                'code': website._get_own_warehouse_code(),
                'company_id': website.company_id.id,
            })
            website.own_warehouse_id = warehouse

    def _get_existing_warehouses(self):
        self.ensure_one()
        return self.env['stock.warehouse'].sudo().with_context(active_test=False).search([
            ('company_id', '=', self.company_id.id),
        ])

    def _get_own_warehouse_name(self):
        self.ensure_one()
        taken = set(self._get_existing_warehouses().mapped('name'))
        name, number = self.name, 1
        while name in taken:
            number += 1
            name = f"{self.name} ({number})"
        return name

    def _get_own_warehouse_code(self):
        """Short name (5 characters at most) built from the website name, unique per company."""
        self.ensure_one()
        taken = set(self._get_existing_warehouses().mapped('code'))
        base = re.sub(r'[^A-Z0-9]', '', (self.name or '').upper())[:3] or 'WEB'
        code, number = base, 1
        while code in taken:
            code = f"{base}{number}"[:5]
            number += 1
        return code

    # ------------------------------------------------------------ product visibility

    def _get_shop_products_domain(self):
        """Products of the shop of the website.

        A website linked to a local shop shows the products whose destination shop is that local shop.
        A website that is a shop of its own shows the products assigned to it.
        """
        self.ensure_one()
        if self.local_shop_id:
            return Domain('shop_ids', 'in', self.local_shop_id.ids)
        return Domain('shop_website_ids', 'in', self.ids)

    def sale_product_domain(self):
        """The catalog of a shop website only lists the products of that shop."""
        domain = super().sale_product_domain()
        website = self.get_current_website()
        if website.is_shop:
            domain = Domain.AND([domain, website._get_shop_products_domain()])
        return domain
