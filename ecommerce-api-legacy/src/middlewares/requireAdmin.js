const crypto = require('crypto');

// Exige o header X-Admin-Token igual a ADMIN_TOKEN. Sem token configurado, bloqueia.
module.exports = (adminToken) => (req, res, next) => {
  const expected = Buffer.from(adminToken || '');
  const received = Buffer.from(req.get('X-Admin-Token') || '');
  const valid = expected.length > 0
    && expected.length === received.length
    && crypto.timingSafeEqual(expected, received);
  if (!valid) return res.status(401).send('Não autorizado');
  return next();
};
