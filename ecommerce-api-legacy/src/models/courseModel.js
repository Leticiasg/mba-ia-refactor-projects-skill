module.exports = (db) => ({
  findActiveById: (courseId) =>
    db.getAsync('SELECT id, title, price FROM courses WHERE id = ? AND active = 1', [courseId]),
});
