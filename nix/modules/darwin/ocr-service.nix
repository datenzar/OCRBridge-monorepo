{ config, lib, pkgs, ... }:

let
  cfg = config.ocrbridge.ocr-service;
in
{
  options.ocrbridge.ocr-service = {
    enable = lib.mkEnableOption "OCRBridge OCR service";
    flavor = lib.mkOption {
      type = lib.types.enum [ "lite" "full" "macos" ];
      default = "lite";
      description = "OCR service package flavor.";
    };
    host = lib.mkOption { type = lib.types.str; default = "0.0.0.0"; };
    port = lib.mkOption { type = lib.types.port; default = 8000; };
    workers = lib.mkOption { type = lib.types.ints.positive; default = 4; };
    uploadDir = lib.mkOption { type = lib.types.path; default = "/var/lib/ocr-service/uploads"; };
    resultsDir = lib.mkOption { type = lib.types.path; default = "/var/lib/ocr-service/results"; };
  };

  config = lib.mkIf cfg.enable {
    launchd.daemons.ocr-service.serviceConfig.ProgramArguments = [ "${pkgs.hello}/bin/hello" ];
  };
}
