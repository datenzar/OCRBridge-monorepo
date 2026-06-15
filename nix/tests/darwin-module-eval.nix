{ nix-darwin, nixpkgs, self, system }:

let
  pkgs = import nixpkgs { inherit system; };
  evaluated = nix-darwin.lib.darwinSystem {
    inherit system;
    modules = [
      self.darwinModules.ocr-service
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
pkgs.runCommand "ocr-service-darwin-module-eval" { } ''
  test -n "${builtins.concatStringsSep " " evaluated.config.launchd.daemons.ocr-service.serviceConfig.ProgramArguments}"
  touch $out
''
