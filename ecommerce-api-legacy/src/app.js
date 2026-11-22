const express = require('express');
const { settings } = require('./config/settings');
const { createLogger } = require('./config/logger');
const { createDatabase, initSchema, seed } = require('./models/database');

const createUserModel = require('./models/userModel');
const createCourseModel = require('./models/courseModel');
const createEnrollmentModel = require('./models/enrollmentModel');
const createPaymentModel = require('./models/paymentModel');
const createAuditLogModel = require('./models/auditLogModel');
const createReportModel = require('./models/reportModel');
const createPaymentService = require('./services/paymentService');
const createCheckoutController = require('./controllers/checkoutController');
const createReportController = require('./controllers/reportController');
const createUserController = require('./controllers/userController');
const checkoutRoutes = require('./views/checkoutRoutes');
const reportRoutes = require('./views/reportRoutes');
const userRoutes = require('./views/userRoutes');
const createRequireAdmin = require('./middlewares/requireAdmin');
const createErrorHandler = require('./middlewares/errorHandler');

const logger = createLogger(settings.logLevel);

async function main() {
  if (!settings.adminToken) logger.warn('ADMIN_TOKEN não definido; rotas administrativas ficam bloqueadas.');

  const db = createDatabase(settings.dbPath);
  await initSchema(db);
  await seed(db);

  const userModel = createUserModel(db);
  const courseModel = createCourseModel(db);
  const enrollmentModel = createEnrollmentModel(db);
  const paymentModel = createPaymentModel(db);
  const auditLogModel = createAuditLogModel(db);
  const reportModel = createReportModel(db);
  const paymentService = createPaymentService({ gatewayKey: settings.paymentGatewayKey, logger });

  const checkoutController = createCheckoutController({
    db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentService,
  });
  const reportController = createReportController({ reportModel });
  const userController = createUserController({ db, userModel, enrollmentModel, paymentModel });
  const requireAdmin = createRequireAdmin(settings.adminToken);

  const app = express();
  app.use(express.json());
  app.use(checkoutRoutes(checkoutController));
  app.use(reportRoutes(reportController, requireAdmin));
  app.use(userRoutes(userController, requireAdmin));
  app.use(createErrorHandler(logger));

  app.listen(settings.port, () => logger.info(`LMS API rodando na porta ${settings.port}...`));
}

main().catch((err) => {
  logger.error('Falha ao iniciar a aplicação:', err);
  process.exit(1);
});
