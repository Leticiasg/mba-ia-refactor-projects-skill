const crypto = require('crypto');
const { UnauthorizedError } = require('./errors');

module.exports = (adminToken) => (req, res, next) => {
  const expected = Buffer.from(adminToken || '');
  const received = Buffer.from(req.get('X-Admin-Token') || '');
  const valid = expected.length > 0
    && expected.length === received.length
    && crypto.timingSafeEqual(expected, received);
  return valid ? next() : next(new UnauthorizedError());
};
