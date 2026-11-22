class AppError extends Error {
  constructor(message, statusCode = 500) {
    super(message);
    this.statusCode = statusCode;
  }
}

class ValidationError extends AppError {
  constructor(message = 'Bad Request') { super(message, 400); }
}

class PaymentDeniedError extends AppError {
  constructor(message = 'Pagamento recusado') { super(message, 400); }
}

class UnauthorizedError extends AppError {
  constructor(message = 'Não autorizado') { super(message, 401); }
}

class NotFoundError extends AppError {
  constructor(message) { super(message, 404); }
}

module.exports = { AppError, ValidationError, PaymentDeniedError, UnauthorizedError, NotFoundError };
