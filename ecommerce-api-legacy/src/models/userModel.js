module.exports = (db) => ({
  findByEmail: (email) => db.getAsync('SELECT id, name, email FROM users WHERE email = ?', [email]),

  async create({ name, email, passwordHash }) {
    const { lastID } = await db.runAsync('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
    return lastID;
  },

  async deleteById(userId) {
    const { changes } = await db.runAsync('DELETE FROM users WHERE id = ?', [userId]);
    return changes;
  },
});
