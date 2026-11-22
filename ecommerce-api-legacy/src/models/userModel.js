module.exports = (db) => ({
  findIdByEmail: (email) => db.getAsync('SELECT id FROM users WHERE email = ?', [email]),

  async create({ name, email, passwordHash }) {
    const result = await db.runAsync('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
    return result.lastID;
  },

  deleteById: (id) => db.runAsync('DELETE FROM users WHERE id = ?', [id]),
});
