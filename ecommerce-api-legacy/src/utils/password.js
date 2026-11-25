const crypto = require('crypto');

const SALT_BYTES = 16;
const KEY_LENGTH = 64;
const RANDOM_PASSWORD_BYTES = 16;

function hashPassword(password) {
  const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
  const hash = crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex');
  return `${salt}:${hash}`;
}

function verifyPassword(password, stored) {
  if (typeof password !== 'string' || typeof stored !== 'string' || !stored.includes(':')) return false;
  const [salt, hash] = stored.split(':');
  const expected = Buffer.from(hash, 'hex');
  const candidate = crypto.scryptSync(password, salt, KEY_LENGTH);
  return expected.length === candidate.length && crypto.timingSafeEqual(candidate, expected);
}

function randomPassword() {
  return crypto.randomBytes(RANDOM_PASSWORD_BYTES).toString('hex');
}

module.exports = { hashPassword, verifyPassword, randomPassword };
