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
          uploadDir = "/var/lib/ocr-service/test-uploads";
          resultsDir = "/var/lib/ocr-service/test-results";
          maxUploadSizeMb = 20;
          syncMaxFileSizeMb = 10;
          logLevel = "DEBUG";
          apiKey.enabled = true;
          apiKey.keys = [ "test-key" ];
          cors.enabled = true;
          cors.origins = [ "https://example.test" ];
          rateLimit.default = "50/hour";
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
  test "${environment.API_KEY_ENABLED}" = "true"
  test "${environment.API_KEYS}" = "test-key"
  test "${environment.CORS_ENABLED}" = "true"
  test "${environment.CORS_ORIGINS}" = "https://example.test"
  test "${environment.RATE_LIMIT_DEFAULT}" = "50/hour"
  test "${serviceConfig.User}" = "ocr-service"
  test "${serviceConfig.Group}" = "ocr-service"
  test "${evaluated.config.users.users.ocr-service.group}" = "ocr-service"
  test -n "${evaluated.config.users.groups.ocr-service.name}"
  [[ "${builtins.concatStringsSep "\n" tmpfilesRules}" == *"d /var/lib/ocr-service/test-uploads 0750 ocr-service ocr-service -"* ]]
  [[ "${builtins.concatStringsSep "\n" tmpfilesRules}" == *"d /var/lib/ocr-service/test-results 0750 ocr-service ocr-service -"* ]]
  touch $out
''
