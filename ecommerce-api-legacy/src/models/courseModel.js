module.exports = (db) => ({
  findActiveById: (id) => db.getAsync('SELECT id, title, price FROM courses WHERE id = ? AND active = 1', [id]),
});
