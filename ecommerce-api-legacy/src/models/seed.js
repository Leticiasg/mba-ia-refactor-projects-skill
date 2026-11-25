const { hashPassword } = require('../utils/password');
const { PAYMENT_STATUS } = require('../config/constants');

// Dados de exemplo carregados no boot (o banco é em memória).
// A senha do usuário de exemplo continua sendo '123', agora gravada com hash.
async function seed(db) {
  await db.runAsync('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
    ['Leonan', 'leonan@fullcycle.com.br', hashPassword('123')]);
  await db.runAsync('INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)',
    ['Clean Architecture', 997.00, 'Docker', 497.00]);
  await db.runAsync('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
  await db.runAsync('INSERT INTO payments (enrollment_id, amount, status) VALUES (1, ?, ?)',
    [997.00, PAYMENT_STATUS.PAID]);
}

module.exports = { seed };
