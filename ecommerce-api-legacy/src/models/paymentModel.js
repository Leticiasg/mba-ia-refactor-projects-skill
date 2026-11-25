module.exports = (db) => ({
  create: (enrollmentId, amount, status) =>
    db.runAsync('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
      [enrollmentId, amount, status]),

  deleteByUserId: (userId) =>
    db.runAsync(
      'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
      [userId]),
});
