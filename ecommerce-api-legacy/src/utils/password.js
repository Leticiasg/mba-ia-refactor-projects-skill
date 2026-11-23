const crypto = require('crypto');

const SALT_BYTES = 16;
const KEY_LENGTH = 64;
const RANDOM_PASSWORD_BYTES = 24;

function hashPassword(password) {
  const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
  const hash = crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex');
  return `${salt}:${hash}`;
}

function randomPassword() {
  return crypto.randomBytes(RANDOM_PASSWORD_BYTES).toString('base64url');
}

module.exports = { hashPassword, randomPassword };
