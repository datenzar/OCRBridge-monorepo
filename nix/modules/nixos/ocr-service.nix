{ config, lib, ... }:

let
  cfg = config.ocrbridge.ocr-service;
  inherit (lib) mkEnableOption mkIf mkOption types;

  programName = cfg.package.meta.mainProgram or "ocr-service-${cfg.flavor}";

  boolToString = value: if value then "true" else "false";
  intToString = value: builtins.toString value;
  pathToString = value: builtins.toString value;
  commaList = values: lib.concatStringsSep "," values;

  environment = {
    API_HOST = cfg.host;
    API_PORT = intToString cfg.port;
    API_WORKERS = intToString cfg.workers;
    UPLOAD_DIR = pathToString cfg.uploadDir;
    RESULTS_DIR = pathToString cfg.resultsDir;
    MAX_UPLOAD_SIZE_MB = intToString cfg.maxUploadSizeMb;
    JOB_EXPIRATION_HOURS = intToString cfg.jobExpirationHours;
    SYNC_TIMEOUT_SECONDS = intToString cfg.syncTimeoutSeconds;
    SYNC_MAX_FILE_SIZE_MB = intToString cfg.syncMaxFileSizeMb;
    PDFOCR_COMMAND = cfg.pdfocrCommand;
    LOG_LEVEL = cfg.logLevel;
    LOG_FORMAT = cfg.logFormat;
    DEBUG = boolToString cfg.debug;
    RELOAD = boolToString cfg.reload;
    STRICT_ENGINE_LOADING = boolToString cfg.strictEngineLoading;
    CIRCUIT_BREAKER_ENABLED = boolToString cfg.circuitBreaker.enabled;
    CIRCUIT_BREAKER_THRESHOLD = intToString cfg.circuitBreaker.threshold;
    CIRCUIT_BREAKER_TIMEOUT_SECONDS = intToString cfg.circuitBreaker.timeoutSeconds;
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD = intToString cfg.circuitBreaker.successThreshold;
    API_KEY_ENABLED = boolToString cfg.apiKey.enabled;
    API_KEYS = commaList cfg.apiKey.keys;
    API_KEY_HEADER_NAME = cfg.apiKey.headerName;
    CORS_ENABLED = boolToString cfg.cors.enabled;
    CORS_ORIGINS = commaList cfg.cors.origins;
    CORS_ALLOW_CREDENTIALS = boolToString cfg.cors.allowCredentials;
    RATE_LIMIT_ENABLED = boolToString cfg.rateLimit.enabled;
    RATE_LIMIT_STORAGE_URI = cfg.rateLimit.storageUri;
    RATE_LIMIT_DEFAULT = cfg.rateLimit.default;
    RATE_LIMIT_OCR_PROCESS = cfg.rateLimit.ocrProcess;
    RATE_LIMIT_OCR_INFO = cfg.rateLimit.ocrInfo;
  };
in
{
  options.ocrbridge.ocr-service = {
    enable = mkEnableOption "OCRBridge OCR service";

    flavor = mkOption {
      type = types.enum [ "lite" "full" ];
      default = "lite";
      description = "OCR service package flavor.";
    };

    package = mkOption {
      type = types.package;
      description = "Package providing the OCRBridge OCR service executable.";
    };

    host = mkOption {
      type = types.str;
      default = "0.0.0.0";
      description = "Host address for the OCR service API.";
    };

    port = mkOption {
      type = types.port;
      default = 8000;
      description = "Port for the OCR service API.";
    };

    workers = mkOption {
      type = types.ints.positive;
      default = 4;
      description = "Number of API worker processes.";
    };

    uploadDir = mkOption {
      type = types.path;
      default = "/var/lib/ocr-service/uploads";
      description = "Directory for temporary uploaded files.";
    };

    resultsDir = mkOption {
      type = types.path;
      default = "/var/lib/ocr-service/results";
      description = "Directory for OCR result cache files.";
    };

    maxUploadSizeMb = mkOption {
      type = types.ints.positive;
      default = 25;
      description = "Maximum upload size in megabytes.";
    };

    jobExpirationHours = mkOption {
      type = types.ints.positive;
      default = 48;
      description = "Hours before asynchronous job results expire.";
    };

    syncTimeoutSeconds = mkOption {
      type = types.ints.between 5 60;
      default = 30;
      description = "Maximum processing time for synchronous OCR requests.";
    };

    syncMaxFileSizeMb = mkOption {
      type = types.ints.between 1 25;
      default = 5;
      description = "Maximum file size in megabytes for synchronous OCR requests.";
    };

    pdfocrCommand = mkOption {
      type = types.str;
      default = "pdfocr";
      description = "Executable name or path for searchable PDF generation.";
    };

    logLevel = mkOption {
      type = types.str;
      default = "INFO";
      description = "Service log level.";
    };

    logFormat = mkOption {
      type = types.str;
      default = "json";
      description = "Service log format.";
    };

    debug = mkOption {
      type = types.bool;
      default = false;
      description = "Enable debug mode.";
    };

    reload = mkOption {
      type = types.bool;
      default = false;
      description = "Enable development auto-reload mode.";
    };

    strictEngineLoading = mkOption {
      type = types.bool;
      default = false;
      description = "Fail startup if an OCR engine fails to load.";
    };

    circuitBreaker = {
      enabled = mkOption {
        type = types.bool;
        default = true;
        description = "Enable circuit breakers for failing OCR engines.";
      };

      threshold = mkOption {
        type = types.ints.positive;
        default = 5;
        description = "Consecutive failures before opening a circuit.";
      };

      timeoutSeconds = mkOption {
        type = types.ints.positive;
        default = 300;
        description = "Seconds before attempting to close an open circuit.";
      };

      successThreshold = mkOption {
        type = types.ints.positive;
        default = 3;
        description = "Consecutive successes required to reset failure count.";
      };
    };

    apiKey = {
      enabled = mkOption {
        type = types.bool;
        default = false;
        description = "Enable API key authentication.";
      };

      keys = mkOption {
        type = types.listOf types.str;
        default = [ ];
        description = "Valid API keys.";
      };

      headerName = mkOption {
        type = types.str;
        default = "X-API-Key";
        description = "HTTP header name for API key authentication.";
      };
    };

    cors = {
      enabled = mkOption {
        type = types.bool;
        default = false;
        description = "Enable CORS middleware.";
      };

      origins = mkOption {
        type = types.listOf types.str;
        default = [ ];
        description = "Allowed CORS origins.";
      };

      allowCredentials = mkOption {
        type = types.bool;
        default = false;
        description = "Allow credentials in CORS requests.";
      };
    };

    rateLimit = {
      enabled = mkOption {
        type = types.bool;
        default = true;
        description = "Enable API rate limiting.";
      };

      storageUri = mkOption {
        type = types.str;
        default = "memory://";
        description = "Storage backend URI for rate limiting.";
      };

      default = mkOption {
        type = types.str;
        default = "100/hour";
        description = "Default rate limit.";
      };

      ocrProcess = mkOption {
        type = types.str;
        default = "10/minute";
        description = "Rate limit for OCR processing endpoints.";
      };

      ocrInfo = mkOption {
        type = types.str;
        default = "100/minute";
        description = "Rate limit for OCR info endpoints.";
      };
    };
  };

  config = mkIf cfg.enable {
    assertions = [
      {
        assertion = cfg.syncMaxFileSizeMb <= cfg.maxUploadSizeMb;
        message = "ocrbridge.ocr-service.syncMaxFileSizeMb cannot exceed maxUploadSizeMb.";
      }
    ];

    users.groups.ocr-service = { };
    users.users.ocr-service = {
      isSystemUser = true;
      group = "ocr-service";
      home = "/var/lib/ocr-service";
    };

    systemd.tmpfiles.rules = [
      "d ${pathToString cfg.uploadDir} 0750 ocr-service ocr-service -"
      "d ${pathToString cfg.resultsDir} 0750 ocr-service ocr-service -"
    ];

    systemd.services.ocr-service = {
      description = "OCRBridge OCR service";
      wantedBy = [ "multi-user.target" ];
      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];
      inherit environment;

      serviceConfig = {
        ExecStart = "${cfg.package}/bin/${programName}";
        User = "ocr-service";
        Group = "ocr-service";
        Restart = "on-failure";
        RestartSec = "5s";
        WorkingDirectory = "/var/lib/ocr-service";
        StateDirectory = "ocr-service";
        NoNewPrivileges = true;
        PrivateTmp = true;
      };
    };
  };
}
