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
          host = "127.0.0.1";
          port = 9000;
          workers = 1;
          uploadDir = "/var/lib/ocr-service/uploads";
          resultsDir = "/var/lib/ocr-service/results";
        };
      }
    ];
  };
in
pkgs.runCommand "ocr-service-nixos-module-eval" { } ''
  test -n "${evaluated.config.systemd.services.ocr-service.serviceConfig.ExecStart}"
  touch $out
''
