module.exports = (db) => ({
  record: (action) => db.runAsync("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]),
});
