const sqlite3 = require('sqlite3');

// Cria a conexão e acrescenta helpers em Promise. A conexão é criada no
// composition root e injetada nos models.
function createDatabase(path) {
  const db = new sqlite3.Database(path);

  db.runAsync = (sql, params = []) => new Promise((resolve, reject) => {
    db.run(sql, params, function onRun(err) {
      if (err) reject(err);
      else resolve({ lastID: this.lastID, changes: this.changes });
    });
  });

  db.getAsync = (sql, params = []) => new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
  });

  db.allAsync = (sql, params = []) => new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
  });

  // Uma conexão SQLite só comporta uma transação por vez: as transações
  // entram numa fila para que requisições simultâneas não se misturem.
  let queue = Promise.resolve();
  db.withTransaction = (work) => {
    const run = async () => {
      await db.runAsync('BEGIN');
      try {
        const result = await work();
        await db.runAsync('COMMIT');
        return result;
      } catch (err) {
        await db.runAsync('ROLLBACK');
        throw err;
      }
    };
    const next = queue.then(run, run);
    queue = next.catch(() => {});
    return next;
  };

  return db;
}

async function createSchema(db) {
  await db.runAsync('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
  await db.runAsync('CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
  await db.runAsync('CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
  await db.runAsync('CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
  await db.runAsync('CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
}

module.exports = { createDatabase, createSchema };
