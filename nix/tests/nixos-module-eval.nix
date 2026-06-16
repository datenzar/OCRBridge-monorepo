{ nixpkgs, self, system }:

let
  pkgs = import nixpkgs { inherit system; };
  evaluated = nixpkgs.lib.nixosSystem {
    inherit system;
    modules = [
      self.nixosModules.ocr-service
      {
        ocrbridge.ocr-service = {
          enable = true;
          flavor = "lite";
          package = self.packages.${system}.ocr-service-lite;
          host = "127.0.0.1";
          port = 9000;
          workers = 1;
          user = "ocrbridge-test";
          group = "ocrbridge-test";
          uploadDir = "/var/lib/ocr-service/test-uploads";
          resultsDir = "/var/lib/ocr-service/test-results";
          maxUploadSizeMb = 20;
          syncMaxFileSizeMb = 10;
          logLevel = "DEBUG";
          circuitBreakerEnabled = false;
          circuitBreakerThreshold = 7;
          circuitBreakerTimeoutSeconds = 120;
          circuitBreakerSuccessThreshold = 2;
          apiKeyEnabled = true;
          apiKeys = [ "test-key" ];
          corsEnabled = true;
          corsOrigins = [ "https://example.test" ];
          corsAllowCredentials = true;
          rateLimitEnabled = false;
          rateLimitStorageUri = "memory://";
          rateLimitDefault = "50/hour";
          rateLimitOcrProcess = "5/minute";
          rateLimitOcrInfo = "25/minute";
        };
      }
    ];
  };

  service = evaluated.config.systemd.services.ocr-service;
  serviceConfig = service.serviceConfig;
  environment = service.environment;
  tmpfilesRules = evaluated.config.systemd.tmpfiles.rules;
in
pkgs.runCommand "ocr-service-nixos-module-eval" { } ''
  test -n "${serviceConfig.ExecStart}"
  [[ "${serviceConfig.ExecStart}" == *"${self.packages.${system}.ocr-service-lite}/bin/ocr-service-lite"* ]]
  test "${environment.API_HOST}" = "127.0.0.1"
  test "${environment.API_PORT}" = "9000"
  test "${environment.API_WORKERS}" = "1"
  test "${environment.UPLOAD_DIR}" = "/var/lib/ocr-service/test-uploads"
  test "${environment.RESULTS_DIR}" = "/var/lib/ocr-service/test-results"
  test "${environment.MAX_UPLOAD_SIZE_MB}" = "20"
  test "${environment.SYNC_MAX_FILE_SIZE_MB}" = "10"
  test "${environment.LOG_LEVEL}" = "DEBUG"
  test "${environment.CIRCUIT_BREAKER_ENABLED}" = "false"
  test "${environment.CIRCUIT_BREAKER_THRESHOLD}" = "7"
  test "${environment.CIRCUIT_BREAKER_TIMEOUT_SECONDS}" = "120"
  test "${environment.CIRCUIT_BREAKER_SUCCESS_THRESHOLD}" = "2"
  test "${environment.API_KEY_ENABLED}" = "true"
  test "${environment.API_KEYS}" = "test-key"
  test "${environment.CORS_ENABLED}" = "true"
  test "${environment.CORS_ORIGINS}" = "https://example.test"
  test "${environment.CORS_ALLOW_CREDENTIALS}" = "true"
  test "${environment.RATE_LIMIT_ENABLED}" = "false"
  test "${environment.RATE_LIMIT_STORAGE_URI}" = "memory://"
  test "${environment.RATE_LIMIT_DEFAULT}" = "50/hour"
  test "${environment.RATE_LIMIT_OCR_PROCESS}" = "5/minute"
  test "${environment.RATE_LIMIT_OCR_INFO}" = "25/minute"
  test "${serviceConfig.User}" = "ocrbridge-test"
  test "${serviceConfig.Group}" = "ocrbridge-test"
  test "${evaluated.config.users.users.ocrbridge-test.group}" = "ocrbridge-test"
  test -n "${evaluated.config.users.groups.ocrbridge-test.name}"
  [[ "${builtins.concatStringsSep "\n" tmpfilesRules}" == *"d /var/lib/ocr-service/test-uploads 0750 ocrbridge-test ocrbridge-test -"* ]]
  [[ "${builtins.concatStringsSep "\n" tmpfilesRules}" == *"d /var/lib/ocr-service/test-results 0750 ocrbridge-test ocrbridge-test -"* ]]
  touch $out
''
