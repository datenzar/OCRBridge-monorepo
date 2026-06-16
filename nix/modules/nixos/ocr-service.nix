{ config, lib, ... }:

let
  cfg = config.ocrbridge.ocr-service;
  inherit (lib) mkEnableOption mkIf mkOption types;

  executable =
    if cfg.executableName == null then
      lib.getExe cfg.package
    else
      "${cfg.package}/bin/${cfg.executableName}";
  packageMainProgram = cfg.package.meta.mainProgram or null;
  expectedMainProgram = "ocr-service-${cfg.flavor}";

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
    CIRCUIT_BREAKER_ENABLED = boolToString cfg.circuitBreakerEnabled;
    CIRCUIT_BREAKER_THRESHOLD = intToString cfg.circuitBreakerThreshold;
    CIRCUIT_BREAKER_TIMEOUT_SECONDS = intToString cfg.circuitBreakerTimeoutSeconds;
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD = intToString cfg.circuitBreakerSuccessThreshold;
    API_KEY_ENABLED = boolToString cfg.apiKeyEnabled;
    API_KEY_HEADER_NAME = cfg.apiKeyHeaderName;
    CORS_ENABLED = boolToString cfg.corsEnabled;
    CORS_ORIGINS = commaList cfg.corsOrigins;
    CORS_ALLOW_CREDENTIALS = boolToString cfg.corsAllowCredentials;
    RATE_LIMIT_ENABLED = boolToString cfg.rateLimitEnabled;
    RATE_LIMIT_STORAGE_URI = cfg.rateLimitStorageUri;
    RATE_LIMIT_DEFAULT = cfg.rateLimitDefault;
    RATE_LIMIT_OCR_PROCESS = cfg.rateLimitOcrProcess;
    RATE_LIMIT_OCR_INFO = cfg.rateLimitOcrInfo;
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

    executableName = mkOption {
      type = types.nullOr types.str;
      default = null;
      description = "Executable name inside the package bin directory. Defaults to the package main program.";
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

    user = mkOption {
      type = types.str;
      default = "ocr-service";
      description = "User account for running the OCR service.";
    };

    group = mkOption {
      type = types.str;
      default = "ocr-service";
      description = "Group account for running the OCR service.";
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

    circuitBreakerEnabled = mkOption {
      type = types.bool;
      default = true;
      description = "Enable circuit breakers for failing OCR engines.";
    };

    circuitBreakerThreshold = mkOption {
      type = types.ints.positive;
      default = 5;
      description = "Consecutive failures before opening a circuit.";
    };

    circuitBreakerTimeoutSeconds = mkOption {
      type = types.ints.positive;
      default = 300;
      description = "Seconds before attempting to close an open circuit.";
    };

    circuitBreakerSuccessThreshold = mkOption {
      type = types.ints.positive;
      default = 3;
      description = "Consecutive successes required to reset failure count.";
    };

    apiKeyEnabled = mkOption {
      type = types.bool;
      default = false;
      description = "Enable API key authentication.";
    };

    apiKeys = mkOption {
      type = types.listOf types.str;
      default = [ ];
      description = "Deprecated. Do not use for secrets; use apiKeysFile instead.";
    };

    apiKeysFile = mkOption {
      type = types.nullOr types.str;
      default = null;
      description = "Runtime environment file containing API_KEYS for API key authentication. Use an absolute runtime path, not a Nix path literal.";
    };

    apiKeyHeaderName = mkOption {
      type = types.str;
      default = "X-API-Key";
      description = "HTTP header name for API key authentication.";
    };

    corsEnabled = mkOption {
      type = types.bool;
      default = false;
      description = "Enable CORS middleware.";
    };

    corsOrigins = mkOption {
      type = types.listOf types.str;
      default = [ ];
      description = "Allowed CORS origins.";
    };

    corsAllowCredentials = mkOption {
      type = types.bool;
      default = false;
      description = "Allow credentials in CORS requests.";
    };

    rateLimitEnabled = mkOption {
      type = types.bool;
      default = true;
      description = "Enable API rate limiting.";
    };

    rateLimitStorageUri = mkOption {
      type = types.str;
      default = "memory://";
      description = "Storage backend URI for rate limiting.";
    };

    rateLimitDefault = mkOption {
      type = types.str;
      default = "100/hour";
      description = "Default rate limit.";
    };

    rateLimitOcrProcess = mkOption {
      type = types.str;
      default = "10/minute";
      description = "Rate limit for OCR processing endpoints.";
    };

    rateLimitOcrInfo = mkOption {
      type = types.str;
      default = "100/minute";
      description = "Rate limit for OCR info endpoints.";
    };
  };

  config = mkIf cfg.enable {
    assertions = [
      {
        assertion = cfg.syncMaxFileSizeMb <= cfg.maxUploadSizeMb;
        message = "ocrbridge.ocr-service.syncMaxFileSizeMb cannot exceed maxUploadSizeMb.";
      }
      {
        assertion = cfg.apiKeys == [ ];
        message = "ocrbridge.ocr-service.apiKeys would expose secrets in the Nix store; use apiKeysFile instead.";
      }
      {
        assertion = cfg.apiKeysFile == null || !lib.hasPrefix builtins.storeDir cfg.apiKeysFile;
        message = "ocrbridge.ocr-service.apiKeysFile must be a runtime path outside the Nix store.";
      }
      {
        assertion =
          cfg.executableName != null
          || packageMainProgram == null
          || !lib.hasPrefix "ocr-service-" packageMainProgram
          || packageMainProgram == expectedMainProgram;
        message = "ocrbridge.ocr-service.flavor must match the package main program unless executableName is set.";
      }
    ];

    users.groups.${cfg.group} = { };
    users.users.${cfg.user} = {
      isSystemUser = true;
      group = cfg.group;
      home = "/var/lib/ocr-service";
    };

    systemd.tmpfiles.rules = [
      "d ${pathToString cfg.uploadDir} 0750 ${cfg.user} ${cfg.group} -"
      "d ${pathToString cfg.resultsDir} 0750 ${cfg.user} ${cfg.group} -"
    ];

    systemd.services.ocr-service = {
      description = "OCRBridge OCR service";
      wantedBy = [ "multi-user.target" ];
      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];
      inherit environment;

      serviceConfig = {
        ExecStart = executable;
        EnvironmentFile = lib.mkIf (cfg.apiKeysFile != null) cfg.apiKeysFile;
        User = cfg.user;
        Group = cfg.group;
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
