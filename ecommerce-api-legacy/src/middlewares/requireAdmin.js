const crypto = require('crypto');
const { settings } = require('../config/settings');

// Exige o header X-Admin-Token igual a ADMIN_TOKEN. Sem ADMIN_TOKEN configurado, a rota fica bloqueada.
module.exports = function requireAdmin(req, res, next) {
  const expected = Buffer.from(settings.adminToken);
  const received = Buffer.from(req.get('X-Admin-Token') || '');
  if (!expected.length || expected.length !== received.length || !crypto.timingSafeEqual(expected, received)) {
    return res.status(401).send('Não autorizado');
  }
  next();
};
