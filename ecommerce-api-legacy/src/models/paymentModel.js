module.exports = (db) => ({
  async create(enrollmentId, amount, status) {
    const { lastID } = await db.runAsync('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollmentId, amount, status]);
    return lastID;
  },

  deleteByUserId: (userId) => db.runAsync(
    'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
    [userId],
  ),
});
