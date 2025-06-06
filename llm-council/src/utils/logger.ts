/**
 * Logger utility for AI Council
 *
 * Provides structured logging capabilities with different log levels.
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogOptions {
  timestamp?: boolean;
  metadata?: Record<string, any>;
}

export class Logger {
  private level: LogLevel;
  private levels: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3,
  };

  constructor(level: LogLevel = 'info') {
    this.level = level;
  }

  /**
   * Log a debug message
   */
  debug(message: string, metadata?: Record<string, any>, options?: LogOptions): void {
    this.log('debug', message, metadata, options);
  }

  /**
   * Log an info message
   */
  info(message: string, metadata?: Record<string, any>, options?: LogOptions): void {
    this.log('info', message, metadata, options);
  }

  /**
   * Log a warning message
   */
  warn(message: string, metadata?: Record<string, any>, options?: LogOptions): void {
    this.log('warn', message, metadata, options);
  }

  /**
   * Log an error message
   */
  error(message: string, error?: any, options?: LogOptions): void {
    const metadata = error
      ? {
          error:
            typeof error === 'object'
              ? {
                  message: error.message,
                  stack: error.stack,
                  ...error,
                }
              : error,
        }
      : undefined;

    this.log('error', message, metadata, options);
  }

  /**
   * Set the current log level
   */
  setLevel(level: LogLevel): void {
    this.level = level;
  }

  /**
   * Get the current log level
   */
  getLevel(): LogLevel {
    return this.level;
  }

  /**
   * Internal logging implementation
   */
  private log(
    level: LogLevel,
    message: string,
    metadata?: Record<string, any>,
    options: LogOptions = {}
  ): void {
    // Check if we should log this message
    if (this.levels[level] < this.levels[this.level]) {
      return;
    }

    // Create log entry
    const logEntry: Record<string, any> = {
      level,
      message,
    };

    // Add timestamp if requested
    if (options.timestamp !== false) {
      logEntry.timestamp = new Date().toISOString();
    }

    // Add metadata
    if (metadata) {
      logEntry.metadata = metadata;
    }

    // Add additional options metadata
    if (options.metadata) {
      logEntry.metadata = {
        ...(logEntry.metadata || {}),
        ...options.metadata,
      };
    }

    // Output to console
    switch (level) {
      case 'debug':
        console.debug(JSON.stringify(logEntry));
        break;
      case 'info':
        console.info(JSON.stringify(logEntry));
        break;
      case 'warn':
        console.warn(JSON.stringify(logEntry));
        break;
      case 'error':
        console.error(JSON.stringify(logEntry));
        break;
    }
  }
}
