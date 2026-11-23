const express = require('express');
const { settings } = require('./config/settings');
const logger = require('./config/logger');
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
const errorHandler = require('./middlewares/errorHandler');

async function start() {
  const db = createDatabase(settings.dbPath);
  await initSchema(db);
  await seed(db);

  const userModel = createUserModel(db);
  const enrollmentModel = createEnrollmentModel(db);
  const paymentModel = createPaymentModel(db);
  const paymentService = createPaymentService({ gatewayKey: settings.paymentGatewayKey, logger });

  const checkoutController = createCheckoutController({
    db,
    userModel,
    courseModel: createCourseModel(db),
    enrollmentModel,
    paymentModel,
    auditLogModel: createAuditLogModel(db),
    paymentService,
  });
  const reportController = createReportController({ reportModel: createReportModel(db) });
  const userController = createUserController({ db, userModel, enrollmentModel, paymentModel });

  if (!settings.adminToken) logger.warn('ADMIN_TOKEN não definida; rotas administrativas ficam bloqueadas (401).');

  const app = express();
  app.use(express.json());
  app.use(checkoutRoutes(checkoutController));
  app.use(reportRoutes(reportController));
  app.use(userRoutes(userController));
  app.use(errorHandler);

  app.listen(settings.port, () => logger.info(`LMS API rodando na porta ${settings.port}`));
}

start().catch((err) => {
  logger.error('Falha ao iniciar a aplicação:', err);
  process.exit(1);
});
