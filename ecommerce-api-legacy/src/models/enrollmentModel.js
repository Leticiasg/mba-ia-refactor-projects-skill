module.exports = (db) => ({
  async create(userId, courseId) {
    const { lastID } = await db.runAsync('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
    return lastID;
  },

  deleteByUserId: (userId) => db.runAsync('DELETE FROM enrollments WHERE user_id = ?', [userId]),
});
