const sqlite3 = require('sqlite3');
const { hashPassword } = require('../utils/password');
const { PAYMENT_STATUS } = require('../config/settings');

function createDatabase(path) {
  const db = new sqlite3.Database(path);

  db.runAsync = (sql, params = []) => new Promise((resolve, reject) =>
    db.run(sql, params, function onRun(err) { return err ? reject(err) : resolve(this); }));
  db.getAsync = (sql, params = []) => new Promise((resolve, reject) =>
    db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row))));
  db.allAsync = (sql, params = []) => new Promise((resolve, reject) =>
    db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows))));

  // Uma conexão só: as transações são enfileiradas para não se sobreporem.
  let queue = Promise.resolve();
  db.transaction = (work) => {
    const run = queue.then(async () => {
      await db.runAsync('BEGIN');
      try {
        const result = await work();
        await db.runAsync('COMMIT');
        return result;
      } catch (err) {
        await db.runAsync('ROLLBACK');
        throw err;
      }
    });
    queue = run.catch(() => {});
    return run;
  };

  return db;
}

async function initSchema(db) {
  await db.runAsync('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
  await db.runAsync('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
  await db.runAsync('CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
  await db.runAsync('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
  await db.runAsync('CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
}

async function seed(db) {
  const { count } = await db.getAsync('SELECT COUNT(*) AS count FROM users');
  if (count > 0) return;
  await db.transaction(async () => {
    await db.runAsync('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
      ['Leonan', 'leonan@fullcycle.com.br', hashPassword('123')]);
    await db.runAsync('INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)',
      ['Clean Architecture', 997.0, 'Docker', 497.0]);
    await db.runAsync('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
    await db.runAsync('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
      [1, 997.0, PAYMENT_STATUS.PAID]);
  });
}

module.exports = { createDatabase, initSchema, seed };
