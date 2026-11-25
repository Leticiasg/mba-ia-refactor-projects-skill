module.exports = (db) => ({
  findByEmail: (email) =>
    db.getAsync('SELECT id, pass FROM users WHERE email = ?', [email]),

  create: async ({ name, email, passwordHash }) => {
    const result = await db.runAsync('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
      [name, email, passwordHash]);
    return result.lastID;
  },

  deleteById: async (userId) => {
    const result = await db.runAsync('DELETE FROM users WHERE id = ?', [userId]);
    return result.changes;
  },
});
