/** @odoo-module **/
(() => {
  document.addEventListener('DOMContentLoaded', () => {
    try {
      // Sólo aplica en /my/orders/<id>
      const m = window.location.pathname.match(/\/my\/orders\/(\d+)/);
      if (!m) return;
      const soId = m[1];

      // Evitar duplicados
      if (document.querySelector('.o_wdc_btn')) return;

      // Crear botón
      const btn = document.createElement('a');
      btn.href = `/my/orders/${soId}/dist-shipping`;
      btn.className = 'btn btn-secondary btn-sm mt-2 o_wdc_btn';
      btn.innerHTML = '<i class="fa fa-truck me-1"></i> Envío del distribuidor';

      // Intentar varios contenedores habituales en el portal
      const targets = [
        '.o_portal_sidebar',
        '#portal_order_content',
        '.o_portal_wrap',
        '.container .row .col-lg-3',
        '.container'
      ];
      let host = null;
      for (const sel of targets) {
        host = document.querySelector(sel);
        if (host) break;
      }
      if (host) {
        host.prepend(btn);
      }
    } catch (e) {
      console.warn('website_dist_checkout: no se pudo insertar el botón del portal', e);
    }
  });
})();
