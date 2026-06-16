{ nix-darwin, nixpkgs, self, system }:

let
  pkgs = import nixpkgs { inherit system; };
  apiKeysFile = "/run/credentials/ocr-service/api-keys.env";
  evalModule = serviceConfig: nix-darwin.lib.darwinSystem {
    inherit system;
    modules = [
      self.darwinModules.ocr-service
      { ocrbridge.ocr-service = serviceConfig; }
    ];
  };

  evaluated = evalModule {
    enable = true;
    flavor = "lite";
    package = self.packages.${system}.ocr-service-lite;
    host = "127.0.0.1";
    port = 9000;
    workers = 1;
    uploadDir = "/var/lib/ocr-service/test-uploads";
    resultsDir = "/var/lib/ocr-service/test-results";
    maxUploadSizeMb = 20;
    syncMaxFileSizeMb = 10;
    logLevel = "DEBUG";
    strictEngineLoading = true;
    circuitBreakerEnabled = false;
    circuitBreakerThreshold = 7;
    circuitBreakerTimeoutSeconds = 120;
    circuitBreakerSuccessThreshold = 2;
    apiKeyEnabled = true;
    apiKeysFile = apiKeysFile;
    corsEnabled = true;
    corsOrigins = [ "https://example.test" ];
    corsAllowCredentials = true;
    rateLimitEnabled = false;
    rateLimitStorageUri = "memory://";
    rateLimitDefault = "50/hour";
    rateLimitOcrProcess = "5/minute";
    rateLimitOcrInfo = "25/minute";
  };

  macosPackageEval = evalModule {
    enable = true;
    flavor = "macos";
    package = self.packages.${system}.ocr-service-macos;
  };

  assertionsPass = evaluatedConfig:
    assert builtins.all (assertion: assertion.assertion) evaluatedConfig.config.assertions;
    true;

  unsafeApiKeysEval = builtins.tryEval (assertionsPass (evalModule {
    enable = true;
    package = self.packages.${system}.ocr-service-lite;
    apiKeys = [ "unsafe-key" ];
  }));

  mismatchedFlavorEval = builtins.tryEval (assertionsPass (evalModule {
    enable = true;
    flavor = "macos";
    package = self.packages.${system}.ocr-service-lite;
  }));

  customPackage = pkgs.writeShellApplication {
    name = "custom-ocr-service";
    text = "exit 0";
  };

  customPackageEval = evalModule {
    enable = true;
    package = customPackage;
    executableName = "custom-ocr-service";
  };

  daemon = evaluated.config.launchd.daemons.ocr-service;
  serviceConfig = daemon.serviceConfig;
  environment = serviceConfig.EnvironmentVariables;
  programArguments = builtins.concatStringsSep " " serviceConfig.ProgramArguments;
  macosProgramArguments = builtins.concatStringsSep " " macosPackageEval.config.launchd.daemons.ocr-service.serviceConfig.ProgramArguments;
  customProgramArguments = builtins.concatStringsSep " " customPackageEval.config.launchd.daemons.ocr-service.serviceConfig.ProgramArguments;
  boolString = value: if value then "true" else "false";
in
pkgs.runCommand "ocr-service-darwin-module-eval" { } ''
  test "${serviceConfig.Label}" = "org.ocrbridge.ocr-service"
  test -n "${programArguments}"
  [[ "${programArguments}" == *"${self.packages.${system}.ocr-service-lite}/bin/ocr-service-lite"* ]]
  [[ "${programArguments}" == *"${apiKeysFile}"* ]]
  test "${environment.API_HOST}" = "127.0.0.1"
  test "${environment.API_PORT}" = "9000"
  test "${environment.API_WORKERS}" = "1"
  test "${environment.UPLOAD_DIR}" = "/var/lib/ocr-service/test-uploads"
  test "${environment.RESULTS_DIR}" = "/var/lib/ocr-service/test-results"
  test "${environment.MAX_UPLOAD_SIZE_MB}" = "20"
  test "${environment.SYNC_MAX_FILE_SIZE_MB}" = "10"
  test "${environment.LOG_LEVEL}" = "DEBUG"
  test "${environment.STRICT_ENGINE_LOADING}" = "true"
  test "${environment.CIRCUIT_BREAKER_ENABLED}" = "false"
  test "${environment.CIRCUIT_BREAKER_THRESHOLD}" = "7"
  test "${environment.CIRCUIT_BREAKER_TIMEOUT_SECONDS}" = "120"
  test "${environment.CIRCUIT_BREAKER_SUCCESS_THRESHOLD}" = "2"
  test "${environment.API_KEY_ENABLED}" = "true"
  test -z "${environment.API_KEYS or ""}"
  test "${environment.CORS_ENABLED}" = "true"
  test "${environment.CORS_ORIGINS}" = "https://example.test"
  test "${environment.CORS_ALLOW_CREDENTIALS}" = "true"
  test "${environment.RATE_LIMIT_ENABLED}" = "false"
  test "${environment.RATE_LIMIT_STORAGE_URI}" = "memory://"
  test "${environment.RATE_LIMIT_DEFAULT}" = "50/hour"
  test "${environment.RATE_LIMIT_OCR_PROCESS}" = "5/minute"
  test "${environment.RATE_LIMIT_OCR_INFO}" = "25/minute"
  test "${boolString serviceConfig.KeepAlive}" = "true"
  test "${boolString serviceConfig.RunAtLoad}" = "true"
  test "${serviceConfig.WorkingDirectory}" = "/var/lib/ocr-service"
  test "${serviceConfig.StandardOutPath}" = "/var/log/ocr-service.log"
  test "${serviceConfig.StandardErrorPath}" = "/var/log/ocr-service.err.log"
  [[ "${macosProgramArguments}" == *"/bin/ocr-service-macos"* ]]
  [[ "${customProgramArguments}" == *"/bin/custom-ocr-service"* ]]
  test "${boolString unsafeApiKeysEval.success}" = "false"
  test "${boolString mismatchedFlavorEval.success}" = "false"
  touch $out
''
